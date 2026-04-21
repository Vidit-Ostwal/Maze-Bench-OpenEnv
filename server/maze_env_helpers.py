# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Pure helpers for the Ice Maze environment (I/O, coords, prompts, slide order)."""

from __future__ import annotations

import json
import os
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

try:
    from ..models import MazeDirection
except ImportError:
    from models import MazeDirection

# ---------------------------------------------------------------------------
# Level dataset
# ---------------------------------------------------------------------------

_LEVELS_CACHE: Optional[List[dict]] = None


def load_ice_maze_levels() -> List[dict]:
    """Load the level JSON once and reuse it across environment instances."""
    global _LEVELS_CACHE
    if _LEVELS_CACHE is not None:
        return _LEVELS_CACHE
    levels_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "dataset", "ice-maze-levels.json")
    )
    with open(levels_path, "r") as f:
        _LEVELS_CACHE = json.load(f)
    return _LEVELS_CACHE


# ---------------------------------------------------------------------------
# Board / cell utilities
# ---------------------------------------------------------------------------

def parse_board_entities(
    grid: List[List[str]],
) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
    """Extract player (`a`/`b`) and exit (`e`/`b`) coordinates from the board grid."""
    agents: List[Tuple[int, int]] = []
    exits: Set[Tuple[int, int]] = set()

    for br, row in enumerate(grid):
        for bc, cell in enumerate(row):
            ir, ic = br - 1, bc - 1
            if cell == "e":
                exits.add((ir, ic))
            elif cell == "b":
                agents.append((ir, ic))
                exits.add((ir, ic))
            elif cell == "a":
                agents.append((ir, ic))

    return agents, sorted(exits)


def render_board(grid: List[List[str]]) -> str:
    """Convert the 2D grid into the text board sent in observations/prompts."""
    return "\n".join("".join(row) for row in grid)


# ---------------------------------------------------------------------------
# Movement
# ---------------------------------------------------------------------------

DIRECTION_DELTAS: Dict[str, Tuple[int, int]] = {
    MazeDirection.UP.value: (-1, 0),
    MazeDirection.DOWN.value: (1, 0),
    MazeDirection.LEFT.value: (0, -1),
    MazeDirection.RIGHT.value: (0, 1),
}


def cell_at_interior(grid: List[List[str]], ir: int, ic: int) -> str:
    """Read the grid character at an interior coordinate (border-offset by +1)."""
    return grid[ir + 1][ic + 1]


def set_cell_at_interior(grid: List[List[str]], ir: int, ic: int, ch: str) -> None:
    """Write a grid character at an interior coordinate (border-offset by +1)."""
    grid[ir + 1][ic + 1] = ch


def can_move_to_cell(
    grid: List[List[str]],
    ir: int,
    ic: int,
    exit_positions: FrozenSet[Tuple[int, int]],
) -> bool:
    """Return whether a player may slide into this interior cell."""
    br, bc = ir + 1, ic + 1
    if br < 0 or bc < 0 or br >= len(grid) or bc >= len(grid[0]):
        return False
    ch = cell_at_interior(grid, ir, ic)
    # Movable: empty ice or unoccupied exit.
    if ch == "." or ch == "e":
        return True
    # Blocked: wall, occupied floor, occupied exit.
    if ch == "#" or ch == "a" or ch == "b":
        return False
    return ch == "."


def glyph_agent_enters(
    ir: int,
    ic: int,
    exit_positions: FrozenSet[Tuple[int, int]],
) -> str:
    """Return destination glyph after an agent enters a cell."""
    if (ir, ic) in exit_positions:
        return "b"
    return "a"


def glyph_after_agent_leaves(
    ir: int,
    ic: int,
    exit_positions: FrozenSet[Tuple[int, int]],
) -> str:
    """Return source glyph after an agent leaves a cell."""
    if (ir, ic) in exit_positions:
        return "e"
    return "."


def slide_one_agent(
    grid: List[List[str]],
    agent_positions: List[Tuple[int, int]],
    agent_index: int,
    dr: int,
    dc: int,
    exit_positions: FrozenSet[Tuple[int, int]],
) -> bool:
    """Slide one agent until blocked; return True if it moved at least one cell."""
    moved = False
    while True:
        ir, ic = agent_positions[agent_index]
        nr, nc = ir + dr, ic + dc
        if not can_move_to_cell(grid, nr, nc, exit_positions):
            break
        set_cell_at_interior(
            grid,
            ir,
            ic,
            glyph_after_agent_leaves(ir, ic, exit_positions),
        )
        set_cell_at_interior(
            grid,
            nr,
            nc,
            glyph_agent_enters(nr, nc, exit_positions),
        )
        agent_positions[agent_index] = (nr, nc)
        moved = True
    return moved


def apply_direction_slide(
    grid: List[List[str]],
    direction: str,
    num_players: int,
    agent_positions: List[Tuple[int, int]],
    exit_positions: FrozenSet[Tuple[int, int]],
) -> bool:
    """Apply one directional move to all players; return whether any player moved."""
    dr, dc = DIRECTION_DELTAS[direction]
    any_moved = False
    indices = sorted_slide_player_indices(direction, num_players, agent_positions)
    for agent_index in indices:
        if slide_one_agent(
            grid=grid,
            agent_positions=agent_positions,
            agent_index=agent_index,
            dr=dr,
            dc=dc,
            exit_positions=exit_positions,
        ):
            any_moved = True
    return any_moved


def build_step_feedback(done: bool, moved: bool, direction: str, step_count: int) -> Tuple[float, str]:
    """Return step reward and status message from current transition outcome."""
    if done:
        return (
            1.0,
            f"Solved! All players reached an exit in {step_count} step(s).",
        )
    if not moved:
        return (-0.1, f"No player moved — already against a wall going {direction}.")
    return (-0.01, f"Moved {direction}. Step {step_count}.")


def sorted_slide_player_indices(
    direction: str,
    num_players: int,
    agent_positions: List[Tuple[int, int]],
) -> List[int]:
    """Order player updates so simultaneous sliding resolves collisions correctly."""
    if direction == MazeDirection.LEFT.value:
        return sorted(range(num_players), key=lambda i: agent_positions[i][1])
    if direction == MazeDirection.RIGHT.value:
        return sorted(range(num_players), key=lambda i: agent_positions[i][1], reverse=True)
    if direction == MazeDirection.UP.value:
        return sorted(range(num_players), key=lambda i: agent_positions[i][0])
    return sorted(range(num_players), key=lambda i: agent_positions[i][0], reverse=True)


# ---------------------------------------------------------------------------
# Episode parameters
# ---------------------------------------------------------------------------

def resolve_max_steps(level: dict, reset_kwargs: Optional[dict] = None) -> int:
    """Choose max steps from reset args, level config, or a diameter-based default."""
    reset_kwargs = reset_kwargs or {}
    if "max_steps" in reset_kwargs:
        return int(reset_kwargs["max_steps"])
    if "max_steps" in level:
        return int(level["max_steps"])
    path = level.get("path") or ""
    diam = int(level.get("diameter", len(path) if path else 1))
    return max(1, diam * 5)


# ---------------------------------------------------------------------------
# LLM system prompt
# ---------------------------------------------------------------------------

def build_system_prompt(
    *,
    width: object,
    height: object,
    num_players: int,
    board: str,
    agent_positions_interior: List[List[int]],
    exit_positions_interior: List[List[int]],
    max_steps: int,
    step_count: int,
    previous_actions: List[str],
) -> str:
    """Build the full system prompt text describing rules and current episode state."""
    player_line = (
        "There is 1 player on the board."
        if num_players == 1
        else f"There are {num_players} players on the board."
    )
    move_line = (
        "Each turn, send a direction to move the player."
        if num_players == 1
        else "Each turn, ALL players move SIMULTANEOUSLY in the same direction."
    )
    block_line = (
        "" if num_players == 1
        else "  - Players act as walls — they block each other's sliding.\n"
    )
    prev_display = ", ".join(previous_actions) if previous_actions else "(none yet)"

    return (
        f"You are playing an Ice Maze puzzle.\n"
        f"\n"
        f"BOARD ({width}×{height}):\n"
        f"{board}\n"
        f"\n"
        f"SYMBOLS:\n"
        f"  #  = Wall (impassable)\n"
        f"  .  = Open cell (slippery ice)\n"
        f"  a  = Player on a non-exit cell\n"
        f"  b  = Player currently on an exit cell\n"
        f"  e  = Exit cell (goal)\n"
        f"\n"
        f"RULES:\n"
        f"  - {player_line}\n"
        f"  - {move_line}\n"
        f"  - On ice, each player SLIDES until they hit a wall (#) or another player (a or b).\n"
        f"{block_line}"
        f"  - Exit cells (e) do NOT stop sliding — players slide through or onto them.\n"
        f"  - After all players stop: if EVERY player is on an exit cell → you win!\n"
        f"  - Exit cells are shared — any player can use any exit.\n"
        f"\n"
        f"STEP BUDGET: at most {max_steps} steps for this level.\n"
        f"\n"
        f"VALID ACTIONS: \"LEFT\", \"RIGHT\", \"UP\", \"DOWN\"\n"
        f"\n"
        f"Current player position(s): {agent_positions_interior}\n"
        f"Exit cell position(s):       {exit_positions_interior}\n"
        f"\n"
        f"EPISODE PROGRESS:\n"
        f"  - Step count (moves so far): {step_count} / {max_steps}\n"
        f"  - Previous actions (oldest → newest): {prev_display}\n"
    )
