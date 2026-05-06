# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Run FastAPI + Maze environment with the Gradio web UI enabled.

Must set ENABLE_WEB_INTERFACE before ``server.app`` is imported (that module
builds ``app`` at import time). This entry point does that, then serves both:

- Same-process **backend**: ``POST /reset``, ``POST /step``, ``GET /schema``, …
- **Web UI** at ``/web`` (Gradio), backed by ``WebInterfaceManager`` so reset/step
  keep a persistent episode (unlike the stateless HTTP simulation handlers).

Usage::

    uv run web
    uv run web -- --port 8000 --reload
"""

from __future__ import annotations

import argparse
import os


def main() -> None:
    os.environ["ENABLE_WEB_INTERFACE"] = "true"

    import uvicorn

    parser = argparse.ArgumentParser(description="Maze server with Gradio UI at /web")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address")
    parser.add_argument("--port", type=int, default=8000, help="Listen port")
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Dev auto-reload (reloads process; re-reads ENABLE_WEB_INTERFACE)",
    )
    args, _unknown = parser.parse_known_args()

    uvicorn.run(
        "maze_env.server.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        factory=False,
    )


if __name__ == "__main__":
    main()
