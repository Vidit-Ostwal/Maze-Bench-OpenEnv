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
except ImportError:
    from client import MazeEnv
    from models import MazeAction, MazeObservation


VALID_DIRECTIONS = ("LEFT", "RIGHT", "UP", "DOWN")
ACTION_REGEX = re.compile(r"\b(LEFT|RIGHT|UP|DOWN)\b", flags=re.IGNORECASE)


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


def decide_action(client: OpenAI, model: str, obs: MazeObservation) -> tuple[str, str]:
    """Call OpenAI and choose one movement direction."""
    user_prompt = (
        "Choose the next move.\n"
        "Return only one token from: LEFT, RIGHT, UP, DOWN.\n\n"
    )

    response = client.responses.create(
        model=model,
        instructions=obs.system_prompt,
        input=user_prompt,
    )
    raw_text = extract_text_from_response(response)
    direction = parse_direction(raw_text)
    return direction, raw_text


def append_observation(
    output_path: Path,
    *,
    step_index: int,
    observation: MazeObservation,
    chosen_action: Optional[str],
    model_response: Optional[str],
    metadata: dict,
) -> None:
    """Append one observation snapshot to a JSONL file."""
    record = {
        "metadata": metadata,
        "step_index": step_index,
        "chosen_action": chosen_action,
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
) -> None:
    """Create env, run one episode rollout, print + save observations."""
    if not os.getenv("OPENAI_API_KEY"):
        raise EnvironmentError("OPENAI_API_KEY is not set.")

    llm_client = OpenAI()

    if output_path.exists():
        output_path.unlink()

    with MazeEnv(base_url=base_url).sync() as env:
        reset_result = env.reset(level_index=level_index)
        obs = reset_result.observation
        resolved_level_index = obs.level_index
        if resolved_level_index == -1:
            resolved_level_index = (obs.metadata or {}).get("level_index", level_index)
        rollout_metadata = {
            "rollout_id": str(uuid4()),
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
            model_response=None,
            metadata=rollout_metadata,
        )

        while not obs.done and obs.step_count < obs.max_steps:
            action, model_text = decide_action(llm_client, model, obs)
            step_result = env.step(MazeAction(direction=action))
            obs = step_result.observation

            print(f"\n=== STEP {obs.step_count} ===")
            print(f"action={action} | model_response={model_text!r}")
            print(obs)
            print(f"done={obs.done} reward={obs.reward}")
            print(f"message={obs.message}")

            append_observation(
                output_path,
                step_index=obs.step_count,
                observation=obs,
                chosen_action=action,
                model_response=model_text,
                metadata=rollout_metadata,
            )

    print("\n=== ROLLOUT COMPLETE ===")
    print(f"Saved observations to: {output_path}")


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
        default="rollout_observations.jsonl",
        help="Path to output JSONL observations file.",
    )
    args = parser.parse_args()

    run_rollout(
        base_url=args.base_url,
        level_index=args.level_index,
        model=args.model,
        output_path=Path(args.output),
    )


if __name__ == "__main__":
    main()
