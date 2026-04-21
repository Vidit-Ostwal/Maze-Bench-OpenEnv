---
title: Maze Env Environment Server
emoji: 🎭
colorFrom: green
colorTo: pink
sdk: docker
pinned: false
app_port: 8000
base_path: /web
tags:
  - openenv
---

# Maze Env Environment

Ice-sliding maze environment on [OpenEnv](https://github.com/meta-pytorch/OpenEnv).

Agents call `reset` / `step` with directions. All players slide simultaneously in the chosen direction until blocked by a wall or another player.

Levels live in `dataset/ice-maze-levels.json`.

## Core Rules

- **Actions**: `LEFT`, `RIGHT`, `UP`, `DOWN`
- **Movement**: on each step, every player slides as far as possible in that direction
- **Win condition**: episode is solved only when every player is on an exit after a step

Board symbols used at runtime:

- `#` wall
- `.` empty ice
- `e` unoccupied exit
- `a` player on non-exit cell
- `b` player on exit cell

## Quick Start (Client)

```python
from maze_env import MazeAction, MazeEnv

with MazeEnv(base_url="http://localhost:8000").sync() as env:
    reset_result = env.reset(level_index=0)
    print(reset_result.observation.board)
    print(reset_result.observation.system_prompt)

    step_result = env.step(MazeAction(direction="LEFT"))
    obs = step_result.observation
    print(obs.board)
    print(obs.message, obs.reward, obs.done)
```

## Run Locally

Start server:

```bash
uv run --project . server
```

Or with uvicorn directly:

```bash
uv run uvicorn server.app:app --reload
```

## Docker

Build:

```bash
docker build -t maze_env-env:latest -f server/Dockerfile .
```

Run:

```bash
docker run --rm -p 8000:8000 maze_env-env:latest
```

## Dataset Validation

Run:

```bash
uv run python dataset/validate_dataset.py
```

The validator checks:

- `start`/`end` consistency against `annotated_board`
- `diameter == len(path)` when both are present
- path replay through the actual environment:
  - `done` must **not** become `True` before the final path move
  - `done` must be `True` at the final path move

## Smoke Test Environment Logic

```bash
uv run python server/maze_env_environment.py
```

This runs a direct `reset`/`step` demo without starting the API server.

## Deployment (OpenEnv / Hugging Face)

```bash
openenv push
```

This uses `openenv.yaml` and deploys the Docker-backed environment.

## Project Structure

```text
.
├── __init__.py
├── client.py
├── models.py
├── openenv.yaml
├── pyproject.toml
├── dataset/
│   ├── ice-maze-levels.json
│   └── validate_dataset.py
└── server/
    ├── app.py
    ├── maze_env_environment.py
    ├── maze_env_helpers.py
    └── Dockerfile
```
