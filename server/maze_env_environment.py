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

from typing import FrozenSet, List, Optional, Tuple
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import MazeAction, MazeObservation
    from .maze_env_helpers import (
        apply_direction_slide,
        build_step_feedback,
        build_system_prompt,
        load_ice_maze_levels,
        parse_board_entities,
        render_board,
        resolve_max_steps,
    )
except ImportError:
    try:
        from models import MazeAction, MazeObservation
        from server.maze_env_helpers import (
            apply_direction_slide,
            build_step_feedback,
            build_system_prompt,
            load_ice_maze_levels,
            parse_board_entities,
            render_board,
            resolve_max_steps,
        )
    except ImportError:
        import os
        import sys

        repo_root = os.path.dirname(os.path.dirname(__file__))
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)

        from models import MazeAction, MazeObservation
        from maze_env_helpers import (
            apply_direction_slide,
            build_step_feedback,
            build_system_prompt,
            load_ice_maze_levels,
            parse_board_entities,
            render_board,
            resolve_max_steps,
        )

class MazeEnvironment(Environment):
    """
    Ice Maze environment.

    Each episode loads one puzzle level from dataset/ice-maze-levels.json.
    Players slide on ice until hitting a wall or another player.
    All players move simultaneously in the same direction each turn.
    The episode ends when every player is on an exit cell simultaneously.

    Supports concurrent WebSocket sessions (each session gets its own instance).
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        """Initialise with empty state; call reset() to load a level."""
        super().__init__()
        self._levels: List[dict] = load_ice_maze_levels()
        self._current_level_index: int = 0
        self._reset_index: int = 0
        self._level: dict = {}
        self._grid: List[List[str]] = []
        self._num_players: int = 1
        # Interior coords (0-based inside ``#`` wall): grid row/col = interior + 1
        self._agent_positions: List[Tuple[int, int]] = []
        # Goal tile interiors are fixed for the episode.
        self._exit_positions: FrozenSet[Tuple[int, int]] = frozenset()
        self._action_history: List[str] = []
        self._max_steps: int = 0
        self._done: bool = False
        self._state: State = State(episode_id=str(uuid4()), step_count=0)

    def _interior_positions_lists(self) -> Tuple[List[List[int]], List[List[int]]]:
        """Return agent/exit interior positions as JSON-friendly `[row, col]` lists."""
        agents = [[r, c] for r, c in self._agent_positions]
        exits = [[r, c] for r, c in sorted(self._exit_positions)]
        return agents, exits

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reset(self, level_index: Optional[int] = None, **kwargs) -> MazeObservation:
        """
        Reset the environment and load a puzzle level.

        Args:
            level_index: If given, load this level index (modulo number of levels).
                If omitted, use the internal reset counter and advance it so
                successive resets cycle through the dataset.

        Returns:
            MazeObservation with the initial board state and full system prompt.
        """
        n = len(self._levels)
        if level_index is not None:
            idx = int(level_index) % n
        else:
            idx = self._reset_index % n
        # Count every reset call, including manual level picks.
        self._reset_index += 1
        self._current_level_index = idx
        self._level = self._levels[idx]

        self._grid = [list(row) for row in self._level["annotated_board"]]
        agent_list, exit_list = parse_board_entities(self._grid)
        self._agent_positions = list(agent_list)
        self._exit_positions = frozenset(exit_list)

        self._num_players = self._level.get("players", len(self._agent_positions))
        self._action_history = []
        self._max_steps = resolve_max_steps(self._level, kwargs)
        self._done = False
        self._state = State(episode_id=str(uuid4()), step_count=0)

        # Check degenerate case: all players already on exits
        self._done = all(pos in self._exit_positions for pos in self._agent_positions)

        ag, ex = self._interior_positions_lists()
        return MazeObservation(
            board=render_board(self._grid),
            step_count=0,
            max_steps=self._max_steps,
            previous_actions=[],
            system_prompt=self._full_system_prompt(),
            agent_positions=ag,
            exit_positions=ex,
            num_players=self._num_players,
            level_index=idx,
            message="Level loaded. Find the exit!",
            done=self._done,
            reward=0.0,
            # path/diameter live on self._level for offline rubrics only — not agent-facing
            metadata={
                "level_index": idx,
            },
        )

    def step(self, action: MazeAction, **kwargs) -> MazeObservation:  # type: ignore[override]
        """
        Execute one environment step for a direction command.

        If the episode is already done, return the current state unchanged.
        Otherwise apply one directional slide move to all players and update
        step history, solved status, reward, and message.
        """
        # MazeAction enforces a valid MazeDirection; value is canonical ("LEFT", etc.).
        direction = action.direction.value
        if self._done:
            return self._current_obs(
                message="Episode already complete. Call reset() to start a new episode.",
                reward=0.0,
            )

        any_slide_moved = apply_direction_slide(
            grid=self._grid,
            direction=direction,
            num_players=self._num_players,
            agent_positions=self._agent_positions,
            exit_positions=self._exit_positions,
        )

        self._action_history.append(direction)
        self._state.step_count += 1

        self._done = all(pos in self._exit_positions for pos in self._agent_positions)
        reward, message = build_step_feedback(
            done=self._done,
            moved=any_slide_moved,
            direction=direction,
            step_count=self._state.step_count,
        )

        prev = list(self._action_history)
        ag, ex = self._interior_positions_lists()
        return MazeObservation(
            board=render_board(self._grid),
            step_count=self._state.step_count,
            max_steps=self._max_steps,
            previous_actions=prev,
            system_prompt=self._full_system_prompt(),
            agent_positions=ag,
            exit_positions=ex,
            num_players=self._num_players,
            level_index=self._current_level_index,
            message=message,
            done=self._done,
            reward=reward,
            metadata={
                "level_index": self._current_level_index,
                "action_history": prev,
            },
        )

    @property
    def state(self) -> State:
        """
        Return the full current state for LLM introspection.

        Includes board, positions, action history, and level metadata.
        """
        ag, ex = self._interior_positions_lists()
        return State(
            episode_id=self._state.episode_id,
            step_count=self._state.step_count,
            # Extra fields (State uses extra="allow")
            current_board=render_board(self._grid),
            num_players=self._num_players,
            agent_positions=ag,
            exit_positions=ex,
            action_history=list(self._action_history),
            level_index=self._current_level_index,
            done=self._done,
        )

    def _full_system_prompt(self) -> str:
        """Rules + board + positions + step budget + current step count and action history."""
        ag, ex = self._interior_positions_lists()
        return build_system_prompt(
            width=self._level.get("width", "?"),
            height=self._level.get("height", "?"),
            num_players=self._num_players,
            board=render_board(self._grid),
            agent_positions_interior=ag,
            exit_positions_interior=ex,
            max_steps=self._max_steps,
            step_count=self._state.step_count,
            previous_actions=list(self._action_history),
        )

    def _current_obs(self, message: str, reward: float) -> MazeObservation:
        """Return an observation reflecting the current state (no movement)."""
        prev = list(self._action_history)
        ag, ex = self._interior_positions_lists()
        return MazeObservation(
            board=render_board(self._grid),
            step_count=self._state.step_count,
            max_steps=self._max_steps,
            previous_actions=prev,
            system_prompt=self._full_system_prompt(),
            agent_positions=ag,
            exit_positions=ex,
            num_players=self._num_players,
            level_index=self._current_level_index,
            message=message,
            done=self._done,
            reward=reward,
            metadata={
                "level_index": self._current_level_index,
                "action_history": prev,
            },
        )


# ---------------------------------------------------------------------------
# Quick smoke-test (run directly: python server/maze_env_environment.py)
# ---------------------------------------------------------------------------

# if __name__ == "__main__":
#     env = MazeEnvironment()

#     print("=== RESET (level 0) ===")
#     obs = env.reset(level_index=23)
#     print(obs)
#     print(f"done={obs.done}, reward={obs.reward}")

#     moves = ["UP", "LEFT", "DOWN", "RIGHT"]
#     for move in moves:
#         print(f"\n=== STEP: {move} ===")
#         obs = env.step(MazeAction(direction=move))
#         print(obs)
#         print("######################################################")