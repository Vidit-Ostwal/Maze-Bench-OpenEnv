#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Validate dataset/ice-maze-levels.json: ``start`` / ``end`` match the board, and ``diameter`` equals ``len(path)`` when both are set.

Board glyphs: ``a`` = start (player) only, ``e`` = exit only, ``b`` = start and exit on the same cell.
Other lowercase letters (e.g. ``c``) are treated as additional player starts only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from models import MazeAction
from server.maze_env_environment import MazeEnvironment

STEP_CHAR_TO_DIRECTION = {
    "U": "UP",
    "D": "DOWN",
    "L": "LEFT",
    "R": "RIGHT",
}


def parse_board(rows: List[str]) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
    """Board ``(row, col)`` from ``enumerate``: ``a``/``b``/other players → starts; ``e``/``b`` → exits."""
    players: List[Tuple[int, int]] = []
    exits: List[Tuple[int, int]] = []
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == "b":
                players.append((r, c))
                exits.append((r, c))
            elif ch == "a":
                players.append((r, c))
            elif ch == "e":
                exits.append((r, c))
            elif len(ch) == 1 and ch.islower() and ch.isalpha():
                players.append((r, c))
    return sorted(players), sorted(exits)


def to_interior_zero_based(board_rc: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """0-based interior: subtract 1 from each board (row, col) from ``enumerate``."""
    return sorted((r - 1, c - 1) for r, c in board_rc)


def json_coords(name: str, raw: object) -> List[Tuple[int, int]]:
    if not isinstance(raw, list):
        raise ValueError(f"{name} must be a list")
    out: List[Tuple[int, int]] = []
    for i, item in enumerate(raw):
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise ValueError(f"{name}[{i}] must be [row, col]")
        out.append((int(item[0]), int(item[1])))
    return sorted(out)


def validate_level(i: int, level: Dict) -> List[str]:
    err: List[str] = []
    p = f"Level[{i}]"

    if not isinstance(level.get("annotated_board"), list) or not level["annotated_board"]:
        err.append(f"{p}: need non-empty annotated_board (list of strings)")
        return err

    if "start" not in level:
        err.append(f"{p}: missing start")
    if "end" not in level:
        err.append(f"{p}: missing end")
    if err:
        return err

    rows = level["annotated_board"]
    try:
        board_players, board_exits = parse_board(rows)
    except (TypeError, ValueError) as e:
        return [f"{p}: board parse error: {e}"]

    try:
        want_players = json_coords("start", level["start"])
        want_exits = json_coords("end", level["end"])
    except ValueError as e:
        return [f"{p}: {e}"]

    got_players = to_interior_zero_based(board_players)
    got_exits = to_interior_zero_based(board_exits)

    if got_players != want_players:
        err.append(
            f"{p}: start mismatch — JSON (0-based interior, sorted): {want_players}; "
            f"parsed board row/col (sorted): {board_players}; after -1 per axis: {got_players}"
        )
    if got_exits != want_exits:
        err.append(
            f"{p}: end mismatch — JSON (0-based interior, sorted): {want_exits}; "
            f"parsed board row/col (sorted): {board_exits}; after -1 per axis: {got_exits}"
        )

    if "diameter" in level and "path" in level:
        path = level["path"]
        diam = level["diameter"]
        if not isinstance(path, str):
            err.append(f"{p}: path must be a string, got {type(path).__name__}")
        elif not isinstance(diam, int) or isinstance(diam, bool):
            err.append(f"{p}: diameter must be an int, got {type(diam).__name__}")
        elif len(path) != diam:
            err.append(
                f"{p}: diameter ({diam}) != len(path) ({len(path)}); path={path!r}"
            )

    return err


def validate_level_path_replay(i: int, level: Dict, env: MazeEnvironment) -> List[str]:
    """Replay level path in MazeEnvironment and verify done only at the final step."""
    p = f"Level[{i}]"
    path = level.get("path")
    if path is None:
        return []
    if not isinstance(path, str):
        return [f"{p}: path must be a string, got {type(path).__name__}"]

    errors: List[str] = []
    obs = env.reset(level_index=i)

    if not path:
        if not obs.done:
            errors.append(f"{p}: empty path but reset state is not done")
        return errors

    if obs.done:
        errors.append(f"{p}: reset starts done=True but path is non-empty ({path!r})")
        return errors

    for step_idx, token in enumerate(path, start=1):
        direction = STEP_CHAR_TO_DIRECTION.get(token)
        if direction is None:
            errors.append(
                f"{p}: path contains invalid token {token!r} at 1-based step {step_idx}; "
                f"use only {sorted(STEP_CHAR_TO_DIRECTION)}"
            )
            break

        obs = env.step(MazeAction(direction=direction))
        is_last = step_idx == len(path)

        if obs.done and not is_last:
            errors.append(
                f"{p}: done became True too early at step {step_idx}/{len(path)}; path={path!r}"
            )
            break
        if is_last and not obs.done:
            errors.append(
                f"{p}: done is False at final path step {step_idx}/{len(path)}; path={path!r}"
            )

    return errors


def main() -> int:
    path = Path(__file__).resolve().parent / "ice-maze-levels.json"
    if not path.is_file():
        print(f"error: missing {path}", file=sys.stderr)
        return 1

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        print("error: root must be a JSON array", file=sys.stderr)
        return 1

    errors: List[str] = []
    env = MazeEnvironment()
    for i, level in enumerate(data):
        if isinstance(level, dict):
            errors.extend(validate_level(i, level))
            errors.extend(validate_level_path_replay(i, level, env))
        else:
            errors.append(f"Level[{i}]: not an object")

    if errors:
        for msg in errors:
            print(msg, file=sys.stderr)
        return 1

    print(f"OK: {len(data)} levels — {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
