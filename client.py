# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Ice Maze Environment Client."""

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from .models import MazeAction, MazeObservation


class MazeEnv(EnvClient[MazeAction, MazeObservation, State]):
    """
    Client for the Ice Maze Environment.

    Maintains a persistent WebSocket connection to the environment server,
    enabling efficient multi-step interactions with lower latency.
    Each client instance has its own dedicated environment session on the server.

    Example (async):
        >>> async with MazeEnv(base_url="http://localhost:8000") as env:
        ...     obs = await env.reset(level_index=1)
        ...     print(obs.observation.system_prompt)
        ...
        ...     obs = await env.step(MazeAction(direction="LEFT"))
        ...     print(obs.observation.board)
        ...     print(obs.observation.message)

    Example (sync wrapper):
        >>> with MazeEnv(base_url="http://localhost:8000").sync() as env:
        ...     obs = env.reset(level_index=1)
        ...     print(obs.observation.system_prompt)
        ...     obs = env.step(MazeAction(direction="UP"))
        ...     print(obs.observation.board)

    Example with Docker:
        >>> client = await MazeEnv.from_docker_image("maze_env-env:latest")
        >>> try:
        ...     obs = await client.reset(level_index=0)
        ...     obs = await client.step(MazeAction(direction="RIGHT"))
        ... finally:
        ...     await client.close()
    """

    def _step_payload(self, action: MazeAction) -> Dict:
        """
        Convert MazeAction to JSON payload for the step WebSocket message.

        Args:
            action: MazeAction instance with a direction field.

        Returns:
            Dictionary representation suitable for JSON encoding.
        """
        # Send canonical wire value expected by the environment.
        return {"direction": action.direction.value}

    def _parse_result(self, payload: Dict) -> StepResult[MazeObservation]:
        """
        Parse server response into StepResult[MazeObservation].

        The server serializes the observation via serialize_observation(), which
        produces:
            {
                "observation": { <MazeObservation fields minus done/reward/metadata> },
                "reward": float | None,
                "done": bool,
            }

        Args:
            payload: JSON response data from server.

        Returns:
            StepResult with a fully populated MazeObservation.
        """
        obs_data = payload.get("observation", {})
        done = payload.get("done", False)
        reward = payload.get("reward")
        observation = MazeObservation(
            board=obs_data.get("board", ""),
            step_count=obs_data.get("step_count", 0),
            max_steps=obs_data.get("max_steps", 0),
            previous_actions=obs_data.get("previous_actions", []),
            system_prompt=obs_data.get("system_prompt", ""),
            agent_positions=obs_data.get("agent_positions", []),
            exit_positions=obs_data.get("exit_positions", []),
            num_players=obs_data.get("num_players", 1),
            message=obs_data.get("message", ""),
            done=done,
            reward=reward,
            metadata=obs_data.get("metadata", payload.get("metadata", {})),
        )

        return StepResult(
            observation=observation,
            reward=reward,
            done=done,
        )

    def _parse_state(self, payload: Dict) -> State:
        """
        Parse server response into a State object.

        The state endpoint returns the full State dict including extra fields
        (current_board, agent_positions, action_history, etc.).

        Args:
            payload: JSON response from the state WebSocket message.

        Returns:
            State object with episode_id, step_count, and all extra fields.
        """
        return State(**payload) if payload else State()
