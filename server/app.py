# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
FastAPI application for the Maze Env Environment.

This module creates an HTTP server that exposes the MazeEnvironment
over HTTP and WebSocket endpoints, compatible with EnvClient.

Endpoints:
    - POST /reset: Reset the environment
    - POST /step: Execute an action
    - GET /state: Get current environment state
    - GET /schema: Get action/observation schemas
    - WS /ws: WebSocket endpoint for persistent sessions

Usage:
    # Development (with auto-reload):
    uvicorn server.app:app --reload --host 0.0.0.0 --port 8000

    # Production:
    uvicorn server.app:app --host 0.0.0.0 --port 8000 --workers 4

    # Or run directly:
    python -m server.app
"""

import os

try:
    import gradio as gr
    from fastapi import Body, HTTPException, WebSocket, WebSocketDisconnect, status
    from fastapi.responses import RedirectResponse
    from openenv.core.env_server.gradio_theme import OPENENV_GRADIO_CSS, OPENENV_GRADIO_THEME
    from openenv.core.env_server.http_server import create_fastapi_app
    from openenv.core.env_server.web_interface import (
        WebInterfaceManager,
        _extract_action_fields,
        _is_chat_env,
        get_quick_start_markdown,
        load_environment_metadata,
    )
except Exception as e:  # pragma: no cover
    raise ImportError(
        "openenv is required for the web interface. Install dependencies with '\n    uv sync\n'"
    ) from e

try:
    from ..models import MazeAction, MazeObservation
    from .gradio_ui import build_maze_gradio_app
    from .maze_env_environment import MazeEnvironment
except ImportError:
    from models import MazeAction, MazeObservation
    from server.gradio_ui import build_maze_gradio_app
    from server.maze_env_environment import MazeEnvironment


def _create_custom_only_web_app():
    """Create FastAPI app with only the custom Gradio UI mounted at /web."""
    app = create_fastapi_app(
        MazeEnvironment,
        MazeAction,
        MazeObservation,
        max_concurrent_envs=1,  # increase this number to allow more concurrent WebSocket sessions
    )

    metadata = load_environment_metadata(MazeEnvironment, "maze_env")
    web_manager = WebInterfaceManager(MazeEnvironment, MazeAction, MazeObservation, metadata)

    @app.get("/", include_in_schema=False)
    async def web_root():
        return RedirectResponse(url="/web/")

    @app.get("/web", include_in_schema=False)
    async def web_root_no_slash():
        return RedirectResponse(url="/web/")

    @app.get("/web/metadata")
    async def web_metadata():
        return web_manager.metadata.model_dump()

    @app.websocket("/ws/ui")
    async def websocket_ui_endpoint(websocket: WebSocket):
        await web_manager.connect_websocket(websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            await web_manager.disconnect_websocket(websocket)

    @app.post("/web/reset")
    async def web_reset(request: dict | None = Body(default=None)):
        return await web_manager.reset_environment(request)

    @app.post("/web/step")
    async def web_step(request: dict):
        if "message" in request:
            message = request["message"]
            if hasattr(web_manager.env, "message_to_action"):
                action = web_manager.env.message_to_action(message)
                if hasattr(action, "tokens"):
                    action_data = {"tokens": action.tokens.tolist()}
                else:
                    action_data = action.model_dump(exclude={"metadata"})
            else:
                action_data = {"message": message}
        else:
            action_data = request.get("action", {})

        return await web_manager.step_environment(action_data)

    @app.get("/web/state")
    async def web_state():
        try:
            return web_manager.get_state()
        except RuntimeError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            ) from exc

    action_fields = _extract_action_fields(MazeAction)
    is_chat_env = _is_chat_env(MazeAction)
    quick_start_md = get_quick_start_markdown(metadata, MazeAction, MazeObservation)

    custom_blocks = build_maze_gradio_app(
        web_manager,
        action_fields,
        metadata,
        is_chat_env,
        metadata.name,
        quick_start_md,
    )
    if not isinstance(custom_blocks, gr.Blocks):
        raise TypeError(
            f"build_maze_gradio_app must return gr.Blocks, got {type(custom_blocks).__name__}"
        )

    app = gr.mount_gradio_app(
        app,
        custom_blocks,
        path="/web",
        theme=OPENENV_GRADIO_THEME,
        css=OPENENV_GRADIO_CSS,
    )
    return app


_enable_web = os.getenv("ENABLE_WEB_INTERFACE", "false").lower() in ("true", "1", "yes")
if _enable_web:
    app = _create_custom_only_web_app()
else:
    app = create_fastapi_app(
        MazeEnvironment,
        MazeAction,
        MazeObservation,
        max_concurrent_envs=1,  # increase this number to allow more concurrent WebSocket sessions
    )


def main(host: str = "0.0.0.0", port: int = 8000):
    """
    Entry point for direct execution via uv run or python -m.

    This function enables running the server without Docker:
        uv run --project . server
        uv run --project . server --port 8001
        python -m maze_env.server.app

    Args:
        host: Host address to bind to (default: "0.0.0.0")
        port: Port number to listen on (default: 8000)

    For production deployments, consider using uvicorn directly with
    multiple workers:
        uvicorn maze_env.server.app:app --workers 4
    """
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    main(port=args.port)
