#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Validate dataset/ice-maze-levels.json: ``start`` / ``end`` present and match board scan.

Board glyphs: ``a`` = start (player) only, ``e`` = exit only, ``b`` = start and exit on the same cell.
Other lowercase letters (e.g. ``c``) are treated as additional player starts only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple


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
    return err


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
    for i, level in enumerate(data):
        if isinstance(level, dict):
            errors.extend(validate_level(i, level))
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
