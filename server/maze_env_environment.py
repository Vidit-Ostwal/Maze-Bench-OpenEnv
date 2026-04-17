# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Ice Maze Environment Implementation.

Players slide on ice in a given direction until they hit a wall (#) or
another player. All players move simultaneously. The episode is solved
when every player is simultaneously on an exit cell (e) after a move.
"""

import json
import os
from typing import List, Optional, Set, Tuple
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import MazeAction, MazeObservation
except ImportError:
    from models import MazeAction, MazeObservation


# ---------------------------------------------------------------------------
# Direction constants
# ---------------------------------------------------------------------------

_DIRECTION_MAP = {
    "up":    (-1,  0),
    "down":  ( 1,  0),
    "left":  ( 0, -1),
    "right": ( 0,  1),
    # single-letter aliases
    "u": (-1,  0),
    "d": ( 1,  0),
    "l": ( 0, -1),
    "r": ( 0,  1),
}

_CANONICAL = {
    "up": "up", "u": "up",
    "down": "down", "d": "down",
    "left": "left", "l": "left",
    "right": "right", "r": "right",
}


# ---------------------------------------------------------------------------
# Level cache (loaded once, shared across all instances)
# ---------------------------------------------------------------------------

_LEVELS_CACHE: Optional[List[dict]] = None


def _load_levels() -> List[dict]:
    """Load ice-maze-levels.json once and cache it."""
    global _LEVELS_CACHE
    if _LEVELS_CACHE is not None:
        return _LEVELS_CACHE
    levels_path = os.path.join(os.path.dirname(__file__), "ice-maze-levels.json")
    with open(levels_path, "r") as f:
        _LEVELS_CACHE = json.load(f)
    return _LEVELS_CACHE


# ---------------------------------------------------------------------------
# MazeEnvironment
# ---------------------------------------------------------------------------

class MazeEnvironment(Environment):
    """
    Ice Maze environment.

    Each episode loads one puzzle level from ice-maze-levels.json.
    Players slide on ice until hitting a wall or another player.
    All players move simultaneously in the same direction each turn.
    The episode ends when every player is on an exit cell simultaneously.

    Supports concurrent WebSocket sessions (each session gets its own instance).
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        """Initialise with empty state; call reset() to load a level."""
        super().__init__()
        self._levels: List[dict] = _load_levels()
        self._current_level_index: int = 0
        self._level: dict = {}
        self._grid: List[List[str]] = []
        self._num_players: int = 1
        self._agent_positions: List[Tuple[int, int]] = []   # board coords
        self._exit_positions: Set[Tuple[int, int]] = set()  # board coords (fixed)
        self._action_history: List[str] = []
        self._done: bool = False
        self._state: State = State(episode_id=str(uuid4()), step_count=0)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reset(self, level_index: int = 0, **kwargs) -> MazeObservation:
        """
        Reset the environment and load a puzzle level.

        Args:
            level_index: Which level to load (wraps with modulo if out of range).

        Returns:
            MazeObservation with the initial board state and full system prompt.
        """
        idx = level_index % len(self._levels)
        self._current_level_index = idx
        self._level = self._levels[idx]

        # Parse board
        self._grid = [list(row) for row in self._level["annotated_board"]]

        # Locate agents ('a') and exits ('e') by scanning the board
        self._agent_positions = []
        self._exit_positions = set()
        for r, row in enumerate(self._grid):
            for c, cell in enumerate(row):
                if cell == "a":
                    self._agent_positions.append((r, c))
                elif cell == "e":
                    self._exit_positions.add((r, c))

        # Fallback: use start/end from JSON if board scan found nothing
        if not self._agent_positions and "start" in self._level:
            self._agent_positions = [
                self._to_board(int_r, int_c)
                for int_r, int_c in self._level["start"]
            ]
        if not self._exit_positions and "end" in self._level:
            self._exit_positions = {
                self._to_board(int_r, int_c)
                for int_r, int_c in self._level["end"]
            }

        self._num_players = self._level.get("players", len(self._agent_positions))
        self._action_history = []
        self._done = False
        self._state = State(episode_id=str(uuid4()), step_count=0)

        # Check degenerate case: all players already on exits
        self._done = all(pos in self._exit_positions for pos in self._agent_positions)

        system_prompt = self._build_system_prompt()

        return MazeObservation(
            board=self._render_board(),
            agent_positions=[self._to_interior(r, c) for r, c in self._agent_positions],
            exit_positions=[self._to_interior(r, c) for r, c in sorted(self._exit_positions)],
            num_players=self._num_players,
            step_count=0,
            message="Level loaded. Find the exit!",
            system_prompt=system_prompt,
            done=self._done,
            reward=0.0,
            metadata={
                "level_index": idx,
                "optimal_path": self._level.get("path", ""),
                "optimal_steps": self._level.get("diameter"),
            },
        )

    def step(self, action: MazeAction, **kwargs) -> MazeObservation:  # type: ignore[override]
        """
        Execute one step: slide all players simultaneously in the given direction.

        Args:
            action: MazeAction with a direction string.

        Returns:
            MazeObservation with updated board state.
        """
        # --- Validate direction ---
        raw = action.direction.strip().lower()
        if raw not in _DIRECTION_MAP:
            return self._current_obs(
                message=f"Invalid direction '{action.direction}'. Use: up, down, left, right",
                reward=0.0,
            )

        # --- Already done? ---
        if self._done:
            return self._current_obs(
                message="Episode already complete. Call reset() to start a new episode.",
                reward=0.0,
            )

        canonical = _CANONICAL[raw]
        dr, dc = _DIRECTION_MAP[raw]

        # --- Snapshot old positions for reward/message computation ---
        old_positions = list(self._agent_positions)

        # --- Sort players by processing order ---
        sorted_indices = self._sorted_player_indices(canonical)

        # --- Occupied set: all current player positions ---
        occupied: Set[Tuple[int, int]] = set(self._agent_positions)

        new_positions = list(self._agent_positions)

        # --- Slide each player ---
        for i in sorted_indices:
            curr_r, curr_c = self._agent_positions[i]

            # Remove this player from occupied so it doesn't block itself
            occupied.discard((curr_r, curr_c))

            # Slide loop
            while True:
                next_r = curr_r + dr
                next_c = curr_c + dc
                if self._grid[next_r][next_c] == "#":
                    break   # wall ahead
                if (next_r, next_c) in occupied:
                    break   # another player ahead
                curr_r, curr_c = next_r, next_c  # slide one step

            new_positions[i] = (curr_r, curr_c)
            occupied.add((curr_r, curr_c))  # new position blocks subsequent players

        # --- Update grid ---
        for i in range(self._num_players):
            old_r, old_c = old_positions[i]
            new_r, new_c = new_positions[i]
            if (old_r, old_c) != (new_r, new_c):
                # Restore old cell: if it was an exit, put 'e' back; else '.'
                self._grid[old_r][old_c] = "e" if (old_r, old_c) in self._exit_positions else "."
                # Place player at new cell (overwrites 'e' visually; tracked separately)
                self._grid[new_r][new_c] = "a"

        self._agent_positions = new_positions

        # --- Update history and step count ---
        self._action_history.append(canonical)
        self._state.step_count += 1

        # --- Win condition: ALL players on exit cells simultaneously ---
        all_on_exit = all(pos in self._exit_positions for pos in self._agent_positions)
        self._done = all_on_exit

        # --- Reward ---
        any_moved = any(new_positions[i] != old_positions[i] for i in range(self._num_players))
        if self._done:
            reward = 1.0
        elif not any_moved:
            reward = -0.1
        else:
            reward = -0.01

        # --- Message ---
        if self._done:
            message = f"Solved! All players reached an exit in {self._state.step_count} step(s)."
        elif not any_moved:
            message = f"No player moved — already against a wall going {canonical}."
        else:
            message = f"Moved {canonical}. Step {self._state.step_count}."

        return MazeObservation(
            board=self._render_board(),
            agent_positions=[self._to_interior(r, c) for r, c in self._agent_positions],
            exit_positions=[self._to_interior(r, c) for r, c in sorted(self._exit_positions)],
            num_players=self._num_players,
            step_count=self._state.step_count,
            message=message,
            system_prompt="",
            done=self._done,
            reward=reward,
            metadata={
                "level_index": self._current_level_index,
                "action_history": list(self._action_history),
            },
        )

    @property
    def state(self) -> State:
        """
        Return the full current state for LLM introspection.

        Includes board, positions, action history, and level metadata.
        """
        return State(
            episode_id=self._state.episode_id,
            step_count=self._state.step_count,
            # Extra fields (State uses extra="allow")
            current_board=self._render_board(),
            num_players=self._num_players,
            agent_positions=[self._to_interior(r, c) for r, c in self._agent_positions],
            exit_positions=[self._to_interior(r, c) for r, c in sorted(self._exit_positions)],
            action_history=list(self._action_history),
            level_index=self._current_level_index,
            optimal_path=self._level.get("path", ""),
            optimal_path_length=self._level.get("diameter"),
            done=self._done,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _render_board(self) -> str:
        """Render the current grid as a newline-separated ASCII string."""
        return "\n".join("".join(row) for row in self._grid)

    def _to_interior(self, board_r: int, board_c: int) -> List[int]:
        """Convert board coordinates (with border) to interior coordinates."""
        return [board_r - 1, board_c - 1]

    def _to_board(self, int_r: int, int_c: int) -> Tuple[int, int]:
        """Convert interior coordinates to board coordinates."""
        return (int_r + 1, int_c + 1)

    def _sorted_player_indices(self, direction: str) -> List[int]:
        """
        Return player indices sorted so the 'leading' player resolves first.

        This ensures correct collision: the player furthest in the movement
        direction resolves first and acts as a wall for players behind it.
        """
        if direction == "left":
            # Leftmost (smallest col) resolves first
            return sorted(range(self._num_players), key=lambda i: self._agent_positions[i][1])
        elif direction == "right":
            # Rightmost (largest col) resolves first
            return sorted(range(self._num_players), key=lambda i: self._agent_positions[i][1], reverse=True)
        elif direction == "up":
            # Topmost (smallest row) resolves first
            return sorted(range(self._num_players), key=lambda i: self._agent_positions[i][0])
        else:  # down
            # Bottommost (largest row) resolves first
            return sorted(range(self._num_players), key=lambda i: self._agent_positions[i][0], reverse=True)

    def _current_obs(self, message: str, reward: float) -> MazeObservation:
        """Return an observation reflecting the current state (no movement)."""
        return MazeObservation(
            board=self._render_board(),
            agent_positions=[self._to_interior(r, c) for r, c in self._agent_positions],
            exit_positions=[self._to_interior(r, c) for r, c in sorted(self._exit_positions)],
            num_players=self._num_players,
            step_count=self._state.step_count,
            message=message,
            system_prompt="",
            done=self._done,
            reward=reward,
            metadata={
                "level_index": self._current_level_index,
                "action_history": list(self._action_history),
            },
        )

    def _build_system_prompt(self) -> str:
        """Build the full system prompt shown to the LLM on reset."""
        width = self._level.get("width", "?")
        height = self._level.get("height", "?")
        diameter = self._level.get("diameter", "?")
        n = self._num_players
        board = self._render_board()
        agent_pos = [self._to_interior(r, c) for r, c in self._agent_positions]
        exit_pos = [self._to_interior(r, c) for r, c in sorted(self._exit_positions)]

        player_line = (
            "There is 1 player on the board."
            if n == 1
            else f"There are {n} players on the board, each marked 'a'."
        )
        move_line = (
            "Each turn, send a direction to move the player."
            if n == 1
            else "Each turn, ALL players move SIMULTANEOUSLY in the same direction."
        )
        block_line = (
            "" if n == 1
            else "  - Players act as walls — they block each other's sliding.\n"
        )

        return (
            f"You are playing an Ice Maze puzzle.\n"
            f"\n"
            f"BOARD ({width}×{height}):\n"
            f"{board}\n"
            f"\n"
            f"SYMBOLS:\n"
            f"  #  = Wall (impassable)\n"
            f"  .  = Open cell (slippery ice)\n"
            f"  a  = Player agent\n"
            f"  e  = Exit cell (goal)\n"
            f"\n"
            f"RULES:\n"
            f"  - {player_line}\n"
            f"  - {move_line}\n"
            f"  - On ice, each player SLIDES until they hit a wall (#) or another player.\n"
            f"{block_line}"
            f"  - Exit cells (e) do NOT stop sliding — players slide through or onto them.\n"
            f"  - After all players stop: if EVERY player is on an exit cell → you win!\n"
            f"  - Exit cells are shared — any player can use any exit.\n"
            f"\n"
            f"VALID ACTIONS: \"up\", \"down\", \"left\", \"right\"\n"
            f"\n"
            f"HINT: This puzzle can be solved in {diameter} move(s).\n"
            f"\n"
            f"Current player position(s): {agent_pos}\n"
            f"Exit cell position(s):       {exit_pos}\n"
        )


# ---------------------------------------------------------------------------
# Quick smoke-test (run directly: python server/maze_env_environment.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    env = MazeEnvironment()

    print("=== RESET (level 1) ===")
    obs = env.reset(level_index=1)
    print(obs.system_prompt)
    print(f"done={obs.done}, reward={obs.reward}")

    moves = ["left", "up", "left", "down", "right", "up"]
    for move in moves:
        print(f"\n=== STEP: {move} ===")
        obs = env.step(MazeAction(direction=move))
        print(obs.board)
        print(f"message : {obs.message}")
        print(f"agents  : {obs.agent_positions}")
        print(f"exits   : {obs.exit_positions}")
        print(f"done={obs.done}, reward={obs.reward}")
        if obs.done:
            break

    print("\n=== STATE ===")
    s = env.state
    print(f"step_count     : {s.step_count}")
    print(f"action_history : {s.action_history}")
    print(f"optimal_path   : {s.optimal_path}")
