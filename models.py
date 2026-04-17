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

from typing import List

from openenv.core.env_server.types import Action, Observation
from pydantic import Field


class MazeAction(Action):
    """
    Action for the Ice Maze environment.

    The agent specifies a direction to slide all players simultaneously.
    On ice, players slide until they hit a wall (#) or another player.
    Exit cells (e) do NOT stop sliding — players slide through them.
    """

    direction: str = Field(
        ...,
        description=(
            "Direction to move all players simultaneously. "
            "Valid values: 'up', 'down', 'left', 'right' "
            "(single-letter aliases 'u', 'd', 'l', 'r' are also accepted)."
        ),
    )


class MazeObservation(Observation):
    """
    Observation from the Ice Maze environment.

    Contains the current board state, player/exit positions, step count,
    a human-readable status message, and (on reset only) a full system prompt
    explaining the rules.

    Inherited from Observation base:
        done (bool)         — True when all players are simultaneously on exit cells
        reward (float|None) — Reward signal for this step
        metadata (dict)     — Extra info: level_index, optimal_path, action_history
    """

    board: str = Field(
        default="",
        description=(
            "Current ASCII board rendered as a newline-separated string. "
            "Symbols: # = wall, . = open cell, a = player, e = exit cell."
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
    step_count: int = Field(
        default=0,
        description="Number of steps taken so far in this episode.",
    )
    message: str = Field(
        default="",
        description=(
            "Human-readable status message describing what just happened, "
            "e.g. 'Moved left. Step 3.', 'Solved! All players reached an exit in 6 steps.', "
            "'Invalid direction. Use: up, down, left, right'."
        ),
    )
    system_prompt: str = Field(
        default="",
        description=(
            "Full instructions for the LLM agent explaining the maze rules, "
            "valid actions, and the current board layout. "
            "Populated only on reset(); empty string on subsequent step() calls."
        ),
    )
