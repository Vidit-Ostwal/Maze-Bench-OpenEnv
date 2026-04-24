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

Ice-sliding maze environment built on [OpenEnv](https://github.com/meta-pytorch/OpenEnv).

Try it online: [Hugging Face Space](https://huggingface.co/spaces/ViditOstwal/maze_env)

Levels are loaded from `dataset/ice-maze-levels.json`.

## Core Rules

- Actions: `LEFT`, `RIGHT`, `UP`, `DOWN`
- All players move simultaneously and slide until blocked
- Sliding is blocked by walls (`#`) or other players (`a`/`b`)
- Exit cells (`e`) are traversable
- Episode is solved only when every player is on an exit after a step

Board symbols:

- `#` wall
- `.` empty ice
- `e` exit
- `a` player on non-exit
- `b` player on exit

## Reward Design (Thought Process)

The reward function is in `server/maze_env_rewards.py` and is designed to discourage loops while keeping a strong success signal:

- **Solved bonus `+10`**: make completion the dominant objective.
- **Repeat action `-1`**: repeating the same direction is often wasteful on ice.
- **Immediate reverse `-1`**: opposite moves (e.g., `UP` then `DOWN`) often undo progress.
- **Revisit-count penalty**: if a board state has already been seen, penalize by `-1 * prior_visits`.
- **Wasted-step revisit penalty**: on revisits, also penalize by `-0.1 * min(step_gap, 50)` to reflect how long the detour took.

The observation `message` (reward feedback) is also included in the `system_prompt` under the **LAST STEP** section, so agents can reason from immediate reward context.

## Quick Start

Run the server:

```bash
uv run --project . server
```

Or:

```bash
uv run uvicorn server.app:app --reload
```

Client example:

```python
from maze_env import MazeAction, MazeEnv

with MazeEnv(base_url="http://localhost:8000").sync() as env:
    obs = env.reset(level_index=0).observation
    print(obs.board)
    step_obs = env.step(MazeAction(direction="LEFT")).observation
    print(step_obs.message, step_obs.reward, step_obs.done)
```

## Useful Commands

- Validate dataset: `uv run python dataset/validate_dataset.py`
- Run one rollout: `OPENAI_API_KEY=... uv run rollout --base-url http://localhost:8000 --level-index 0`
- Render GIF from rollout: `uv run rollout-gif --input rollout_observations.jsonl --output rollout.gif`
- Deploy: `openenv push`
