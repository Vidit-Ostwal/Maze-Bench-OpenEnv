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
- **Sliding stops on**: walls (`#`) or occupied cells (`a`/`b`) only; exits (`e`) are traversable
- **Win condition**: episode is solved only when every player is on an exit after a step
- **Rewards**: solved `+1.0`, moved `-0.01`, no movement `-0.1`

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

## Run One LLM Rollout

Use OpenAI to choose a direction at each step (using `system_prompt` from every observation):

```bash
OPENAI_API_KEY=... uv run python rollout.py --base-url http://localhost:8000 --level-index 0
```

Or via installed script:

```bash
OPENAI_API_KEY=... uv run rollout --base-url http://localhost:8000 --level-index 0
```

Useful rollout flags:

- `--model` (default: `gpt-5.4-mini`)
- `--frame-duration-ms` (default: `700`)
- omit `--level-index` to cycle levels across resets

By default, each run writes paired files in `outputs/` with the same UUID:

- `outputs/rollout_<uuid>.jsonl`
- `outputs/rollout_<uuid>.gif`

JSONL records contain: `metadata`, `step_index`, `chosen_action`, `model_response`, `observation`.
If the model output does not contain a valid direction token, rollout falls back to `UP`.

The GIF plays three phases per move:

1. bright direction arrow on current board (`Model chose action`)
2. dim arrow flash on current board
3. resulting next board (`After move`)

Override paths (supports `{uuid}` token or directory targets):

```bash
OPENAI_API_KEY=... uv run rollout --base-url http://localhost:8000 --level-index 0 \
  --output outputs/custom_{uuid}.jsonl \
  --gif-output outputs/custom_{uuid}.gif
```

Disable GIF rendering with:

```bash
OPENAI_API_KEY=... uv run rollout --base-url http://localhost:8000 --level-index 0 --gif-output ""
```

Render a GIF from an existing observations file:

```bash
uv run python render_rollout_gif.py --input rollout_observations.jsonl --output rollout.gif
```

Or via script entrypoint:

```bash
uv run rollout-gif --input rollout_observations.jsonl --output rollout.gif
```

Optional renderer flag:

- `--cell-size` (default: `48`)

## Sample Replay

![Rollout replay sample](outputs/rollout_2f7201fb-e92e-4f6d-b99c-7ff2fd2d01d9.gif)

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
├── rollout.py
├── render_rollout_gif.py
├── outputs/                  # generated rollout JSONL + GIF files
├── dataset/
│   ├── ice-maze-levels.json
│   └── validate_dataset.py
└── server/
    ├── app.py
    ├── maze_env_environment.py
    ├── maze_env_helpers.py
    └── Dockerfile
```
