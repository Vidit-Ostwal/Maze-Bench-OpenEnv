# Ice Maze Environment — Implementation Plan

## Overview

This document describes the full design for implementing the Ice Maze environment on top of the OpenEnv framework. The environment loads puzzle levels from `server/ice-maze-levels.json`, supports 1–N players sliding on ice simultaneously, and exposes a clean API for LLM agents to interact with.

---

## 1. Data Format (`ice-maze-levels.json`)

Each level is a JSON object with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `width` | int | Number of interior columns (excluding border walls) |
| `height` | int | Number of interior rows (excluding border walls) |
| `players` | int | Number of simultaneous players |
| `diameter` | int | Length of the optimal solution path |
| `open_cells` | int | Number of non-wall cells |
| `states` | int | Total reachable states |
| `start` | `[[row, col], ...]` | Starting interior coordinates per player |
| `end` | `[[row, col], ...]` | Goal interior coordinates per player |
| `path` | str | Optimal solution as a string of U/D/L/R characters |
| `annotated_board` | `[str, ...]` | ASCII board rows including border |
| `date` | str | Generation timestamp |

### Coordinate System

The `annotated_board` is `(height+2) × (width+2)` — it includes a border of `#` walls on all sides.

`start`/`end` use **interior coordinates** `[row, col]` where `[0, 0]` is the **top-left interior cell**:

```
board_row = interior_row + 1
board_col = interior_col + 1
```

**Verification:**
- `start: [[3, 6]]` → `board[4][7]` = `'a'` in `"###....a.#"` ✓
- `end: [[0, 5]]` → `board[1][6]` = `'e'` in `"#.....e..#"` ✓

### Board Symbols

| Symbol | Meaning |
|--------|---------|
| `#` | Wall (impassable) |
| `.` | Open cell (slippery ice) |
| `a` | Player agent (one per player) |
| `e` | Exit/goal cell |

---

## 2. Ice-Sliding Mechanic

When a player moves in a direction, they **slide** along that axis until they hit a wall (`#`) or another player (who acts as a wall). They stop at the last open cell before the obstacle.

```
Direction vectors:
  "up"    → (dr=-1, dc= 0)
  "down"  → (dr=+1, dc= 0)
  "left"  → (dr= 0, dc=-1)
  "right" → (dr= 0, dc=+1)

Slide algorithm for one player:
  curr = player_position
  while True:
      next_r = curr[0] + dr
      next_c = curr[1] + dc
      if grid[next_r][next_c] == '#':       break   # wall ahead, stop
      if (next_r, next_c) in occupied_set:  break   # another player ahead, stop
      curr = (next_r, next_c)               # slide one step
  player_new_position = curr
```

The player slides **as far as possible** and stops only when the next cell is a wall or occupied by another player. The exit cell `e` does **not** stop the slide — the player slides through or onto it just like any open cell.

---

## 3. Multi-Player Simultaneous Movement

All players move **simultaneously** in the same direction each turn. Players act as walls to each other — they cannot occupy the same cell.

### Collision Resolution Order

To correctly resolve simultaneous movement, players are processed in the order that is "furthest ahead" in the movement direction first. This ensures a player that has already resolved its new position acts as a wall for players behind it.

| Direction | Processing Order |
|-----------|-----------------|
| `left` | Players sorted by `col` ascending (leftmost first) |
| `right` | Players sorted by `col` descending (rightmost first) |
| `up` | Players sorted by `row` ascending (topmost first) |
| `down` | Players sorted by `row` descending (bottommost first) |

After each player resolves their slide, their **new** position is added to the `occupied` set so subsequent players treat it as a wall.

### Done Condition (checked AFTER all players stop)

- Exit cells (`e`) are **shared** — any player can land on any `e` cell.
- After **all players have finished sliding** (each stopped by a wall or another player), check: is **every player** currently on an `e` cell?
- The **episode is done** when all players are simultaneously on `e` cells after a move resolves.
- Players do **not** get individually "locked in" — every player slides on every turn until the episode ends.
- There are always exactly `players` exit cells on the board, one per player.

**Example (2 players, 2 exits):**
```
Turn 1: Player A slides to cell X, Player B slides to cell Y.
        Check: is X an 'e'? is Y an 'e'?
        → Only if BOTH are on 'e' cells → done=True.
        → If only one is on 'e' → done=False, both keep moving next turn.
```

---

## 4. Internal State

```python
self._levels: list[dict]                    # all levels loaded from JSON (class-level cache)
self._current_level_index: int              # which level is active
self._level: dict                           # current level dict
self._grid: list[list[str]]                 # mutable 2D board (board coords, includes border)
self._num_players: int                      # number of players this level
self._agent_positions: list[tuple[int,int]] # board coords per player (updated each step)
self._exit_positions: set[tuple[int,int]]   # board coords of ALL exit cells (fixed, from 'e' in board)
self._action_history: list[str]             # e.g. ["left", "up", "left", "down"]
self._state: State                          # episode_id + step_count
```

Note: `_exit_positions` is a **set** of all `e` cells on the board. There is no per-player pairing — any player on any exit counts.

---

## 5. Models (`models.py`)

### `MazeAction`

```python
class MazeAction(Action):
    direction: str  # "up" | "down" | "left" | "right"
```

No `player` field — all players always move together in the same direction.

### `MazeObservation`

```python
class MazeObservation(Observation):
    board: str              # ASCII board rendered as newline-joined string
    agent_positions: list   # [[row, col], ...] interior coords per player
    exit_positions: list    # [[row, col], ...] interior coords of all exit cells
    num_players: int        # number of players
    step_count: int         # steps taken so far this episode
    message: str            # human-readable status message
    system_prompt: str      # full instructions — only on reset(), empty on step()
    # inherited: done (bool), reward (float|None), metadata (dict)
```

---

## 6. `reset(level_index: int = 0)` Logic

```
1. Load levels from JSON (cached at class level after first load)
2. idx = level_index % len(levels)
3. Store self._current_level_index = idx, self._level = levels[idx]
4. Parse annotated_board → self._grid (list[list[str]])
   - Each row string becomes a list of characters
5. Scan grid for 'a' characters → self._agent_positions (board coords, in scan order)
   - Fallback: use level["start"] converted to board coords if no 'a' found
6. Scan grid for 'e' characters → self._exit_positions (set of board coords)
   - Fallback: use level["end"] converted to board coords
7. self._num_players = level["players"]
8. self._action_history = []
9. self._state = State(episode_id=uuid4(), step_count=0)
10. Build system_prompt string (see Section 13)
11. Return MazeObservation(
        board=_render_board(),
        agent_positions=[_to_interior(r,c) for (r,c) in _agent_positions],
        exit_positions=[_to_interior(r,c) for (r,c) in sorted(_exit_positions)],
        num_players=_num_players,
        step_count=0,
        message="Level loaded. Find the exit!",
        system_prompt=<system_prompt>,
        done=False,
        reward=0.0,
        metadata={"level_index": idx, "optimal_path": level.get("path",""), "optimal_steps": level.get("diameter")}
    )
```

---

## 7. `step(action: MazeAction)` Logic

```
1. Normalize direction: action.direction.strip().lower()
   Aliases: "u"→"up", "d"→"down", "l"→"left", "r"→"right"
   Invalid → return current obs with message="Invalid direction. Use: up, down, left, right"
             reward=0.0, done=False (no state change)

2. If episode already done:
   → return current obs with message="Episode already complete. Call reset() to start a new episode."

3. Determine direction vector (dr, dc):
   "up"    → (-1,  0)
   "down"  → (+1,  0)
   "left"  → ( 0, -1)
   "right" → ( 0, +1)

4. Sort player indices by processing order:
   "left"  → sort by col ascending  (leftmost player resolves first)
   "right" → sort by col descending (rightmost player resolves first)
   "up"    → sort by row ascending  (topmost player resolves first)
   "down"  → sort by row descending (bottommost player resolves first)

5. occupied = set(_agent_positions)   # all current player positions

6. new_positions = list(_agent_positions)  # will be updated per player

7. For each player index i in sorted order:
   a. Remove _agent_positions[i] from occupied  (player doesn't block itself)
   b. curr = _agent_positions[i]
   c. SLIDE LOOP:
      while True:
          next_r = curr[0] + dr
          next_c = curr[1] + dc
          if _grid[next_r][next_c] == '#':       break  # wall
          if (next_r, next_c) in occupied:       break  # another player
          curr = (next_r, next_c)                # move one step
   d. new_positions[i] = curr
   e. occupied.add(curr)   # new position blocks subsequent players

8. Update _grid to reflect new positions:
   For each player i:
       old_r, old_c = _agent_positions[i]
       new_r, new_c = new_positions[i]
       if (old_r, old_c) != (new_r, new_c):
           _grid[old_r][old_c] = '.'   # clear old cell
           _grid[new_r][new_c] = 'a'   # place player at new cell
           # Note: if new cell was 'e', we overwrite with 'a' visually
           #       but we still track exit positions separately

9. _agent_positions = new_positions
10. _action_history.append(normalized_direction)
11. _state.step_count += 1

12. CHECK WIN CONDITION:
    all_on_exit = all(pos in _exit_positions for pos in _agent_positions)
    done = all_on_exit

13. Compute reward:
    any_moved = any(new_positions[i] != old_positions[i] for i in range(num_players))
    if done:
        reward = 1.0                  # solved!
    elif not any_moved:
        reward = -0.1                 # wasted move (no player moved at all)
    else:
        reward = -0.01                # small step cost to encourage efficiency

14. Build message:
    if done:       "Solved! All players reached an exit in {step_count} steps."
    elif not moved: "No player moved — already against a wall in that direction."
    else:          "Moved {direction}. Step {step_count}."

15. Return MazeObservation(
        board=_render_board(),
        agent_positions=[_to_interior(r,c) for (r,c) in _agent_positions],
        exit_positions=[_to_interior(r,c) for (r,c) in sorted(_exit_positions)],
        num_players=_num_players,
        step_count=_state.step_count,
        message=<message>,
        system_prompt="",
        done=done,
        reward=reward,
        metadata={"level_index": _current_level_index, "action_history": _action_history}
    )
```

---

## 8. `state` Property

Returns a `State` object with extra fields (base `State` uses `extra="allow"`):

```python
State(
    episode_id=self._state.episode_id,
    step_count=self._state.step_count,
    # extra fields (allowed by State's extra="allow" config):
    current_board=_render_board(),
    num_players=self._num_players,
    agent_positions=[_to_interior(r,c) for (r,c) in _agent_positions],
    exit_positions=[_to_interior(r,c) for (r,c) in sorted(_exit_positions)],
    action_history=self._action_history,
    level_index=self._current_level_index,
    optimal_path=self._level.get("path", ""),
    optimal_path_length=self._level.get("diameter"),
)
```

This gives the LLM full context: current board, where every player is, where all exits are, every move made so far, and the optimal solution length as a hint.

---

## 9. Board Rendering

```python
def _render_board(self) -> str:
    return "\n".join("".join(row) for row in self._grid)
```

The grid is kept in sync with `_agent_positions` at all times. Exit cells (`e`) that are currently occupied by a player show `'a'` (player overwrites `e` visually), but `_exit_positions` always tracks where exits are.

Example output (single player, initial state):
```
##########
#.....e..#
#........#
#......#.#
###....a.#
#........#
#........#
#........#
#........#
##########
```

---

## 10. Coordinate Helpers

```python
def _to_interior(self, board_r: int, board_c: int) -> list[int]:
    """Board coords (with border) → interior coords (0-indexed, no border)"""
    return [board_r - 1, board_c - 1]

def _to_board(self, int_r: int, int_c: int) -> tuple[int, int]:
    """Interior coords → board coords"""
    return (int_r + 1, int_c + 1)
```

---

## 11. Reward Structure

| Event | Reward |
|-------|--------|
| All players on exit cells (solved!) | +1.0 |
| Normal step (at least one player moved) | -0.01 |
| Wasted move (no player moved at all) | -0.1 |
| Invalid direction string | 0.0 (no state change) |

---

## 12. Files Changed

| File | Change |
|------|--------|
| `plan.md` | This document |
| `models.py` | `MazeAction`: `direction` field; `MazeObservation`: `board`, `agent_positions`, `exit_positions`, `num_players`, `step_count`, `message`, `system_prompt` |
| `server/maze_env_environment.py` | Full rewrite with ice-slide + multi-player collision + shared exits |
| `client.py` | Update `_step_payload` (send `direction`), `_parse_result` (parse new obs fields) |

---

## 13. System Prompt Template (on reset)

```
You are playing an Ice Maze puzzle.

BOARD ({width}×{height}):
{rendered_board}

SYMBOLS:
  #  = Wall (impassable)
  .  = Open cell (slippery ice)
  a  = Player agent
  e  = Exit cell (goal)

RULES:
  - There are {N} player(s) on the board.
  - Each turn, ALL players move SIMULTANEOUSLY in the same direction.
  - On ice, each player SLIDES until they hit a wall (#) or another player.
  - Players act as walls — they block each other's sliding.
  - The exit cells (e) do NOT stop sliding — players slide through them.
  - After all players stop, check: if EVERY player is on an exit cell → you win!
  - Exit cells are shared — any player can use any exit.

VALID ACTIONS: "up", "down", "left", "right"

HINT: This puzzle can be solved in {diameter} move(s).

Current player position(s): {agent_positions}
Exit cell position(s):       {exit_positions}
```

---

## 14. Edge Cases

| Case | Handling |
|------|----------|
| Level has no `start`/`end` keys | Scan `annotated_board` for `'a'` and `'e'` characters |
| `level_index` out of range | Use `level_index % len(levels)` (modular wrap) |
| All players already on exits at reset | `done=True` immediately (degenerate level) |
| Episode done, step called again | Return current obs with `message="Episode already complete."` |
| Invalid direction string | Return current obs with error message, no state change, `reward=0.0` |
| No player moved (all against walls) | `reward=-0.1`, message explains no movement |
| Two players moving toward each other | Processing order ensures one stops first; the other is blocked by it |
| Player slides over an exit cell | Player continues sliding (exits don't stop movement) |
| Player stops exactly on an exit cell | Counted as "on exit" for win check |
