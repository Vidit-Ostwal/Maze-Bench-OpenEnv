"""Run one MazeEnv rollout with LLM-selected actions."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Optional
from uuid import uuid4

from openai import OpenAI

try:
    from .client import MazeEnv
    from .models import MazeAction, MazeObservation
    from .render_rollout_gif import render_rollout_gif
except ImportError:
    from client import MazeEnv
    from models import MazeAction, MazeObservation
    from render_rollout_gif import render_rollout_gif


VALID_DIRECTIONS = ("LEFT", "RIGHT", "UP", "DOWN")
ACTION_REGEX = re.compile(r"\b(LEFT|RIGHT|UP|DOWN)\b", flags=re.IGNORECASE)
THOUGHT_REGEX = re.compile(r"(?im)^thought\s*:\s*(.+)$")
DIRECTION_LINE_REGEX = re.compile(r"(?im)^direction\s*:\s*(LEFT|RIGHT|UP|DOWN)\s*$")


def resolve_rollout_path(path: Optional[Path], *, rollout_id: str, extension: str) -> Optional[Path]:
    """Resolve output path templates and directory targets using rollout UUID."""
    if path is None:
        return None

    raw = str(path)
    if "{uuid}" in raw:
        return Path(raw.replace("{uuid}", rollout_id))

    # Treat suffix-less values like "outputs" as a directory target.
    if path.suffix == "":
        return path / f"rollout_{rollout_id}{extension}"

    return path


def extract_text_from_response(response: object) -> str:
    """Best-effort extraction for text from OpenAI Responses API objects."""
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()
    if output_text is not None:
        text = str(output_text).strip()
        if text:
            return text
    return str(response).strip()


def parse_direction(text: str) -> str:
    """Parse one valid direction token from model text."""
    match = ACTION_REGEX.search(text or "")
    if not match:
        return "UP"
    return match.group(1).upper()


def parse_decision(text: str) -> tuple[str, str]:
    """Parse Direction/Thought output with graceful fallback."""
    direction_match = DIRECTION_LINE_REGEX.search(text or "")
    direction = direction_match.group(1).upper() if direction_match else parse_direction(text)
    thought_match = THOUGHT_REGEX.search(text or "")
    thought = thought_match.group(1).strip() if thought_match else (text or "").strip()
    if not thought:
        thought = "No reasoning provided."
    return direction, thought


def decide_action(client: OpenAI, model: str, obs: MazeObservation) -> tuple[str, str, str]:
    """Call OpenAI, reason over all directions, and choose an action."""
    user_prompt = (
        "Evaluate each direction mentally (LEFT, RIGHT, UP, DOWN), "
        "predict what each would achieve, then choose the best move.\n"
        "Return exactly this format:\n"
        "Direction: <LEFT|RIGHT|UP|DOWN>\n"
        "Thought: <brief reasoning>\n"
    )

    response = client.responses.create(
        model=model,
        instructions=obs.system_prompt,
        input=user_prompt,
    )
    raw_text = extract_text_from_response(response)
    direction, thought = parse_decision(raw_text)
    return direction, thought, raw_text


def append_observation(
    output_path: Path,
    *,
    step_index: int,
    observation: MazeObservation,
    chosen_action: Optional[str],
    model_thought: Optional[str],
    model_response: Optional[str],
    metadata: dict,
) -> None:
    """Append one observation snapshot to a JSONL file."""
    record = {
        "metadata": metadata,
        "step_index": step_index,
        "chosen_action": chosen_action,
        "model_thought": model_thought,
        "model_response": model_response,
        "observation": observation.model_dump(),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(record) + "\n")


def run_rollout(
    *,
    base_url: str,
    level_index: Optional[int],
    model: str,
    output_path: Path,
    gif_output: Optional[Path],
    frame_duration_ms: int,
) -> None:
    """Create env, run one episode rollout, print + save observations."""
    if not os.getenv("OPENAI_API_KEY"):
        raise EnvironmentError("OPENAI_API_KEY is not set.")

    llm_client = OpenAI()
    rollout_id = str(uuid4())
    output_path = resolve_rollout_path(output_path, rollout_id=rollout_id, extension=".jsonl")
    if output_path is None:
        raise ValueError("output_path must resolve to a valid file path.")
    gif_output = resolve_rollout_path(gif_output, rollout_id=rollout_id, extension=".gif")

    if output_path.exists():
        output_path.unlink()

    with MazeEnv(base_url=base_url).sync() as env:
        reset_result = env.reset(level_index=level_index)
        obs = reset_result.observation
        resolved_level_index = obs.level_index
        if resolved_level_index == -1:
            resolved_level_index = (obs.metadata or {}).get("level_index", level_index)
        rollout_metadata = {
            "rollout_id": rollout_id,
            "level_index": resolved_level_index,
            "model": model,
        }

        print("\n=== RESET ===")
        print(f"rollout_id={rollout_metadata['rollout_id']}")
        print(obs)
        print(f"step={obs.step_count}/{obs.max_steps} done={obs.done} reward={obs.reward}")
        print(f"message={obs.message}")
        append_observation(
            output_path,
            step_index=obs.step_count,
            observation=obs,
            chosen_action=None,
            model_thought=None,
            model_response=None,
            metadata=rollout_metadata,
        )

        while not obs.done and obs.step_count < obs.max_steps:
            action, thought, model_text = decide_action(llm_client, model, obs)
            step_result = env.step(MazeAction(direction=action))
            obs = step_result.observation

            print(f"\n=== STEP {obs.step_count} ===")
            print(f"direction={action}")
            print(f"thought={thought}")
            print(obs)
            print(f"done={obs.done} reward={obs.reward}")
            print(f"message={obs.message}")

            append_observation(
                output_path,
                step_index=obs.step_count,
                observation=obs,
                chosen_action=action,
                model_thought=thought,
                model_response=model_text,
                metadata=rollout_metadata,
            )

    print("\n=== ROLLOUT COMPLETE ===")
    print(f"Saved observations to: {output_path}")
    if gif_output is not None:
        render_rollout_gif(
            output_path,
            gif_output,
            frame_duration_ms=frame_duration_ms,
        )
        print(f"Saved rollout GIF to: {gif_output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one MazeEnv rollout using OpenAI.")
    parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:8000",
        help="Maze environment server URL.",
    )
    parser.add_argument(
        "--level-index",
        type=int,
        default=None,
        help="Optional level index to reset to.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-5.4-mini",
        help="OpenAI model name for action selection.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="outputs/rollout_{uuid}.jsonl",
        help=(
            "Path to output JSONL observations file. Supports {uuid} token "
            "and directory targets."
        ),
    )
    parser.add_argument(
        "--gif-output",
        type=str,
        default="outputs/rollout_{uuid}.gif",
        help=(
            "Path to rendered rollout GIF. Supports {uuid} token and directory targets. "
            "Set empty string to disable GIF generation."
        ),
    )
    parser.add_argument(
        "--frame-duration-ms",
        type=int,
        default=700,
        help="Duration of each GIF frame in milliseconds.",
    )
    args = parser.parse_args()
    gif_output = Path(args.gif_output) if args.gif_output else None

    run_rollout(
        base_url=args.base_url,
        level_index=args.level_index,
        model=args.model,
        output_path=Path(args.output),
        gif_output=gif_output,
        frame_duration_ms=args.frame_duration_ms,
    )


if __name__ == "__main__":
    main()
