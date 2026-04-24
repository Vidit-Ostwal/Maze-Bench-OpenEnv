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

from typing import Any, Dict, FrozenSet, List, Optional, Tuple
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import MazeAction, MazeObservation
    from .maze_env_helpers import (
        apply_direction_slide,
        build_system_prompt,
        load_ice_maze_levels,
        parse_board_entities,
        render_board,
        resolve_max_steps,
    )
    from .maze_env_rewards import board_fingerprint, compute_maze_step_reward
except ImportError:
    try:
        from models import MazeAction, MazeObservation
        from server.maze_env_helpers import (
            apply_direction_slide,
            build_system_prompt,
            load_ice_maze_levels,
            parse_board_entities,
            render_board,
            resolve_max_steps,
        )
        from server.maze_env_rewards import board_fingerprint, compute_maze_step_reward
    except ImportError:
        import os
        import sys

        repo_root = os.path.dirname(os.path.dirname(__file__))
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)

        from models import MazeAction, MazeObservation
        from maze_env_helpers import (
            apply_direction_slide,
            build_system_prompt,
            load_ice_maze_levels,
            parse_board_entities,
            render_board,
            resolve_max_steps,
        )
        from maze_env_rewards import board_fingerprint, compute_maze_step_reward

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
        super().__init__()
        self._levels: List[dict] = load_ice_maze_levels()
        self._current_level_index: int = 0
        self._reset_index: int = 0
        self._level: dict = {}
        self._grid: List[List[str]] = []
        self._num_players: int = 1
        self._agent_positions: List[Tuple[int, int]] = []  # interior coords; grid uses +1 offset
        self._exit_positions: FrozenSet[Tuple[int, int]] = frozenset()
        self._action_history: List[str] = []
        self._board_state_visit_counts: Dict[Tuple[str, ...], int] = {}  # full-board fp -> visits
        self._board_state_last_step: Dict[Tuple[str, ...], int] = {}  # fp -> last step index
        self._max_steps: int = 0
        self._done: bool = False
        self._state: State = State(episode_id=str(uuid4()), step_count=0)

    def _interior_positions_lists(self) -> Tuple[List[List[int]], List[List[int]]]:
        """Return agent/exit interior positions as JSON-friendly `[row, col]` lists."""
        agents = [[r, c] for r, c in self._agent_positions]
        exits = [[r, c] for r, c in sorted(self._exit_positions)]
        return agents, exits

    def _load_level(self, idx: int, **kwargs) -> None:
        """Load level ``idx``; ``kwargs`` are forwarded to ``resolve_max_steps``."""
        self._current_level_index = idx
        self._level = self._levels[idx]
        self._grid = [list(row) for row in self._level["annotated_board"]]
        agent_list, exit_list = parse_board_entities(self._grid)
        self._agent_positions = list(agent_list)
        self._exit_positions = frozenset(exit_list)
        self._num_players = self._level.get("players", len(self._agent_positions))
        self._action_history = []
        self._board_state_visit_counts = {}
        self._board_state_last_step = {}
        self._max_steps = resolve_max_steps(self._level, kwargs)
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._done = all(pos in self._exit_positions for pos in self._agent_positions)
        fp0 = board_fingerprint(self._grid)  # starting layout counts as first visit (step 0)
        self._board_state_visit_counts[fp0] = 1
        self._board_state_last_step[fp0] = 0

    def _observation(
        self,
        message: str,
        reward: float,
        *,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> MazeObservation:
        """Assemble a :class:`MazeObservation` from the current in-memory state."""
        ag, ex = self._interior_positions_lists()
        prev = list(self._action_history)
        metadata: Dict[str, Any] = {"level_index": self._current_level_index, "action_history": prev}
        if extra_metadata:
            metadata.update(extra_metadata)
        return MazeObservation(
            board=render_board(self._grid),
            step_count=self._state.step_count,
            max_steps=self._max_steps,
            previous_actions=prev,
            system_prompt=self._full_system_prompt(message),
            agent_positions=ag,
            exit_positions=ex,
            num_players=self._num_players,
            level_index=self._current_level_index,
            message=message,
            done=self._done,
            reward=reward,
            metadata=metadata,
        )

    def reset(self, level_index: Optional[int] = None, **kwargs) -> MazeObservation:
        """
        Reset the environment. ``level_index`` is reduced modulo the dataset size;
        if omitted, the internal index advances so successive resets cycle levels.
        """
        n = len(self._levels)
        idx = (int(level_index) % n) if level_index is not None else (self._reset_index % n)
        self._reset_index += 1
        self._load_level(idx, **kwargs)
        return self._observation("Level loaded. Find the exit!", 0.0)

    def _bump_state_visit(self, fp: Tuple[str, ...]) -> Tuple[int, int]:
        """Record post-slide layout ``fp``; return (visit count before, waste gap for reward)."""
        n_before = self._board_state_visit_counts.get(fp, 0)
        gap = (
            self._state.step_count - self._board_state_last_step[fp] if n_before > 0 else 0
        )
        self._board_state_visit_counts[fp] = n_before + 1
        self._board_state_last_step[fp] = self._state.step_count
        return n_before, gap

    def _step_extra_metadata(
        self,
        moved: bool,
        reward_breakdown: Dict[str, float],
        fp: Tuple[str, ...],
        waste_step_gap: int,
    ) -> Dict[str, Any]:
        return {
            "moved": moved,
            "reward_breakdown": reward_breakdown,
            "state_fingerprint_total_visits": self._board_state_visit_counts[fp],
            "revisit_waste_step_gap": waste_step_gap,
        }

    def step(self, action: MazeAction, **kwargs) -> MazeObservation:  # type: ignore[override]
        """One slide; updates history, visit tracking, reward, and observation. No-op if ``done``."""
        direction = action.direction.value
        if self._done:
            return self._observation(
                "Episode already complete. Call reset() to start a new episode.",
                0.0,
            )

        prev = self._action_history[-1] if self._action_history else None
        moved = apply_direction_slide(
            grid=self._grid,
            direction=direction,
            num_players=self._num_players,
            agent_positions=self._agent_positions,
            exit_positions=self._exit_positions,
        )
        self._action_history.append(direction)
        self._state.step_count += 1
        self._done = all(p in self._exit_positions for p in self._agent_positions)
        fp = board_fingerprint(self._grid)
        prior, gap = self._bump_state_visit(fp)
        reward, message, br = compute_maze_step_reward(
            done=self._done,
            direction=direction,
            previous_direction=prev,
            state_visit_count_before=prior,
            waste_step_gap=gap,
            step_count=self._state.step_count,
        )
        return self._observation(
            message, reward, extra_metadata=self._step_extra_metadata(moved, br, fp, gap)
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

    def _full_system_prompt(self, last_step_feedback: str) -> str:
        """Rules, board, positions, step budget, history, and last-step reward message."""
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
            last_step_feedback=last_step_feedback,
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