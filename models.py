# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the Ice Maze Environment.

The maze environment loads ice-sliding puzzle levels and exposes them
to LLM agents via the OpenEnv protocol.
"""

from enum import Enum
from typing import List

from openenv.core.env_server.types import Action, Observation
from pydantic import Field, field_validator


class MazeDirection(str, Enum):
    """Cardinal direction for a single Ice Maze step (all players move together)."""

    LEFT = "LEFT"
    RIGHT = "RIGHT"
    UP = "UP"
    DOWN = "DOWN"


class MazeAction(Action):
    """
    Action for the Ice Maze environment.

    The agent specifies a direction to slide all players simultaneously.
    On ice, players slide until they hit a wall (#) or another player.
    Exit cells (e) do NOT stop sliding — players slide through them.
    """

    direction: MazeDirection = Field(
        ...,
        description="Direction to move all players simultaneously: LEFT, RIGHT, UP, or DOWN.",
    )

    @field_validator("direction", mode="before")
    @classmethod
    def _coerce_direction(cls, v: object) -> object:
        if isinstance(v, MazeDirection):
            return v
        if isinstance(v, str):
            key = v.strip().upper()
            if key in MazeDirection.__members__:
                return MazeDirection[key]
        return v


class MazeObservation(Observation):
    """
    Observation from the Ice Maze environment.

    Primary agent-facing fields: current board, step budget, action history,
    and (on reset) the system prompt with rules and layout context.
    Additional fields support tooling and state introspection.

    Inherited from Observation base:
        done (bool)         — True when all players are simultaneously on exit cells
        reward (float|None) — Reward signal for this step
        metadata (dict)     — Extra info: level_index, action_history (no oracle path)
    """

    board: str = Field(
        default="",
        description=(
            "Current ASCII board rendered as a newline-separated string. "
            "Symbols: # wall, . ice, a player on non-exit, e unoccupied exit, "
            "b player currently on an exit."
        ),
    )
    step_count: int = Field(
        default=0,
        description="Number of steps taken so far in this episode.",
    )
    max_steps: int = Field(
        default=0,
        description="Maximum steps allowed for this episode before a hard limit (set on reset).",
    )
    previous_actions: List[str] = Field(
        default_factory=list,
        description=(
            "Directions applied so far in order, each value one of "
            "LEFT, RIGHT, UP, DOWN (same vocabulary as MazeAction)."
        ),
    )
    system_prompt: str = Field(
        default="",
        description=(
            "Instructions for the LLM: maze rules, valid actions, symbols, layout, "
            "step count vs max steps, and previous actions (oldest first). "
            "Refreshed on reset() and on each step()."
        ),
    )
    agent_positions: List[List[int]] = Field(
        default_factory=list,
        description=(
            "Current interior coordinates of each player as [[row, col], ...]. "
            "Interior coords are 0-indexed from the top-left non-wall cell "
            "(i.e. board_row - 1, board_col - 1)."
        ),
    )
    exit_positions: List[List[int]] = Field(
        default_factory=list,
        description=(
            "Interior coordinates of all exit cells as [[row, col], ...]. "
            "Exit cells are shared — any player can use any exit. "
            "Fixed for the duration of the episode."
        ),
    )
    num_players: int = Field(
        default=1,
        description="Number of players in this level.",
    )
    message: str = Field(
        default="",
        description=(
            "Human-readable status message describing what just happened, "
            "e.g. 'Moved LEFT. Step 3.', 'Solved! All players reached an exit in 6 steps.', "
            "'Invalid direction. Use: LEFT, RIGHT, UP, DOWN'."
        ),
    )

    def __str__(self) -> str:
        parts = []

        parts.append(f"done={self.done} | reward={self.reward}")
        parts.append(f"step={self.step_count}/{self.max_steps}")
        parts.append(f"players={self.agent_positions} exits={self.exit_positions}")

        if self.previous_actions:
            parts.append(f"actions={self.previous_actions}")

        if self.message:
            parts.append(f"message={self.message}")

        # 👇 Full system prompt (clearly separated)
        if self.system_prompt:
            parts.append("\n=== SYSTEM PROMPT ===")
            parts.append(self.system_prompt)

        return "\n".join(parts)