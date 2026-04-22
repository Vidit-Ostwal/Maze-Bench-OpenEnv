from __future__ import annotations

import html
from typing import Any

import gradio as gr

# Light Gradio theme (avoids OpenEnv’s square-corner / terminal CSS on /web).
MAZE_GRADIO_THEME = gr.themes.Soft(
    primary_hue=gr.themes.colors.sky,
    secondary_hue=gr.themes.colors.blue,
    neutral_hue=gr.themes.colors.slate,
).set(
    body_background_fill="#e6ebf3",
    body_background_fill_dark="#e6ebf3",
    background_fill_primary="#e8ecf4",
    background_fill_secondary="#e2e7f0",
    block_background_fill="#e8ecf4",
    block_border_color="#d2dce8",
    block_label_text_color="#64748b",
    block_title_text_color="#1e3a5f",
    border_color_primary="#dbe7f2",
    input_background_fill="#eceff6",
    input_border_color="#c8d5e3",
    button_primary_background_fill="#0ea5e9",
    button_primary_background_fill_hover="#0284c7",
    button_primary_text_color="#ffffff",
    button_secondary_background_fill="#eceff6",
    button_secondary_background_fill_hover="#e2e8f0",
    button_secondary_text_color="#1e3a5f",
    button_secondary_border_color="#cfe2f0",
)


# ==========================================================
# ICE OPS UI
# ==========================================================

_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

:root{
    /* Page: same hue as boxes — tinted blue-gray, not white */
    --bg1:#e8ecf4;
    --bg2:#dfe5ef;
    /* Column shells: step darker so cards still read against the page */
    --panel:#d8dfe9;
    --panel-mid:#d0d8e4;
    /* Nested regions inside a column — barely lighter, still matches the trio */
    --panel-inset:#eceff6;
    --line:#d2dce8;
    --text:#1e3a5f;
    --muted:#64748b;
    --blue:#0ea5e9;
    --blue2:#7dd3fc;
    --green:#0d9488;
    /* Full-page paint (reused below + for !important overrides) */
    --mz-page-stack:
        radial-gradient(circle at 12% 8%,#eef1f7 0%,transparent 48%),
        radial-gradient(circle at 88% 92%,#e3e8f1 0%,transparent 44%),
        linear-gradient(165deg,var(--bg1) 0%,var(--bg2) 100%);
    /* Gradio theme tokens — layout uses these for big surfaces; keep them off pure white */
    --body-background-fill:var(--bg2);
    --background-fill-primary:var(--bg1);
    --background-fill-secondary:#e2e7f0;
    --block-background-fill:var(--bg1);
}

html{
    background:var(--mz-page-stack) !important;
    background-color:var(--bg2) !important;
    min-height:100%;
}

body{
    background:var(--mz-page-stack) !important;
    background-color:var(--bg2) !important;
    font-family:Inter,sans-serif!important;
    color:var(--text)!important;
}

/* Host element for Gradio 6 — often paints the visible “page” behind blocks */
gradio-app{
    background:var(--mz-page-stack) !important;
    background-color:var(--bg2) !important;
    /* Inherited into shadow tree — keeps inner wrappers off default white */
    --body-background-fill:var(--bg2);
    --background-fill-primary:var(--bg1);
    --background-fill-secondary:#e2e7f0;
    --block-background-fill:var(--bg1);
}

body .gradio-container{
    background:transparent !important;
    font-family:Inter,sans-serif!important;
    color:var(--text)!important;
}

footer{display:none!important;}

.block-container{
    max-width:1480px!important;
    padding-top:22px!important;
    background:transparent !important;
}

.mz-card{
    background:linear-gradient(180deg,var(--panel) 0%,var(--panel-mid) 100%);
    backdrop-filter:blur(10px);
    border:1px solid var(--line);
    border-radius:24px;
    padding:18px;
    box-shadow:0 6px 20px rgba(15,23,42,.05);
}

#mz-head{
    background:linear-gradient(135deg,var(--panel-inset),var(--bg2));
    border:1px solid var(--line);
    border-radius:24px;
    padding:18px 24px;
    margin-bottom:14px;
}

#mz-title{
    font-size:1.55rem;
    font-weight:900;
    color:#1e3a5f;
}

#mz-sub{
    margin-top:6px;
    color:var(--muted);
    font-size:.92rem;
}

#mz-board{
    min-height:640px;
    display:flex;
    justify-content:center;
    align-items:center;
    border-radius:24px;
    background:linear-gradient(180deg,var(--panel) 0%,var(--panel-mid) 100%);
    border:1px solid var(--line);
    padding:18px;
}

button{
    min-height:58px!important;
    border-radius:18px!important;
    border:1px solid #c8d5e3!important;
    background:linear-gradient(180deg,var(--panel-inset),#e2e8f0)!important;
    color:#1e3a5f!important;
    font-weight:800!important;
    transition:.18s ease!important;
}

button:hover{
    transform:translateY(-2px);
    box-shadow:0 8px 20px rgba(15,23,42,.08);
}

.dir button{
    min-height:76px!important;
    min-width:76px!important;
    font-size:1.45rem!important;
    font-weight:900!important;
    border-radius:22px!important;
}

.dpad{
    display:flex;
    flex-direction:column;
    gap:10px;
    background:linear-gradient(180deg,var(--panel-inset),var(--panel));
    border:1px solid var(--line);
    border-radius:18px;
    padding:10px;
}

.dpad-row{
    display:grid;
    grid-template-columns:1fr 1fr 1fr;
    gap:10px;
    align-items:center;
}

.dpad-slot{
    height:76px;
    border-radius:22px;
    border:1px dashed #b8c5d4;
    background:linear-gradient(180deg,var(--bg2),var(--panel-inset));
}

.dpad-core{
    height:76px;
    border-radius:22px;
    border:1px solid var(--line);
    background:linear-gradient(180deg,var(--panel-inset),var(--panel));
    display:flex;
    align-items:center;
    justify-content:center;
    color:#94a3b8;
    font-weight:900;
    letter-spacing:.1em;
}

.section{
    font-size:1rem;
    font-weight:900;
    color:#1e3a5f;
    margin-bottom:10px;
}

.grid{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:10px;
}

.card{
    background:linear-gradient(180deg,var(--panel-inset),var(--panel));
    border:1px solid var(--line);
    border-radius:18px;
    padding:14px;
}

.label{
    font-size:.72rem;
    color:#64748b;
    font-weight:900;
    letter-spacing:.04em;
}

.value{
    margin-top:7px;
    font-size:1.2rem;
    font-weight:900;
    color:#1e3a5f;
}

.info{
    margin-top:12px;
    background:linear-gradient(180deg,var(--panel-inset),var(--panel));
    border:1px solid var(--line);
    border-radius:18px;
    padding:14px;
}

.right-stack{
    display:flex;
    flex-direction:column;
    gap:12px;
}

.left-stack{
    display:flex;
    flex-direction:column;
    gap:12px;
}

.left-box{
    background:linear-gradient(180deg,var(--panel-inset),var(--panel));
    border:1px solid var(--line);
    border-radius:18px;
    padding:14px;
}

.left-head,
.right-head{
    font-size:.78rem;
    color:#64748b;
    font-weight:900;
    letter-spacing:.06em;
    margin-bottom:10px;
    text-transform:uppercase;
}

.right-box{
    background:linear-gradient(180deg,var(--panel-inset),var(--panel));
    border:1px solid var(--line);
    border-radius:18px;
    padding:14px;
}

.kv-table{
    border:1px solid var(--line);
    border-radius:14px;
    overflow:hidden;
    background:var(--panel-inset);
}

.kv-row{
    display:grid;
    grid-template-columns: 42% 58%;
    border-top:1px solid rgba(203,213,225,.55);
}

.kv-row:first-child{
    border-top:none;
}

.kv-key{
    padding:10px 12px;
    background:#d8e0eb;
    font-size:.74rem;
    font-weight:900;
    color:#64748b;
    letter-spacing:.04em;
    text-transform:uppercase;
    border-right:1px solid var(--line);
}

.kv-val{
    padding:10px 12px;
    font-size:.88rem;
    font-weight:700;
    color:#1e3a5f;
    word-break:break-word;
    line-height:1.45;
}

.kv-val.status-ok{ color:#0d9488; }
.kv-val.status-run{ color:#0284c7; }

.chip{
    display:inline-block;
    padding:8px 12px;
    border-radius:999px;
    margin:6px 8px 0 0;
    font-size:.82rem;
    font-weight:900;
    border:1px solid #cfe2f0;
    background:#e8f4fc;
    color:#0369a1;
}

.chip-wrap{
    display:flex;
    flex-wrap:wrap;
    gap:6px;
}

.mono{
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

#status textarea,
#status input{
    background:var(--bg2)!important;
    border:1px solid var(--line)!important;
    border-radius:14px!important;
    color:#1e3a5f!important;
    font-weight:700!important;
}

.solve{
    margin-top:12px;
    text-align:center;
    font-weight:900;
    color:var(--green);
}
"""


# ==========================================================
# BOARD
# ==========================================================

def _cell(symbol: str) -> str:
    base = """
    width:46px;height:46px;
    border-radius:14px;
    display:flex;
    justify-content:center;
    align-items:center;
    """

    if symbol == "#":
        return f"""
        <div style="{base}
        background:linear-gradient(135deg,#8cb7e5,#628fc5);
        border:1px solid #4f7eb8;"></div>
        """

    if symbol == ".":
        return f"""
        <div style="{base}
        background:linear-gradient(180deg,#ffffff,#f4faff);
        border:1px solid #dfecff;"></div>
        """

    if symbol == "e":
        return f"""
        <div style="{base}
        background:linear-gradient(180deg,#eafff6,#dffff0);
        border:1px solid #a9e6c9;">
        <div style="
        width:18px;height:18px;
        transform:rotate(45deg);
        background:#11c989;
        border-radius:3px;"></div>
        </div>
        """

    if symbol == "a":
        return f"""
        <div style="{base}
        background:linear-gradient(180deg,#ffffff,#f2f9ff);
        border:1px solid #dceaff;">
        <div style="
        width:24px;height:24px;
        border-radius:50%;
        background:radial-gradient(circle,#ffffff,#70c2ff,#2f8fff);
        box-shadow:0 0 12px rgba(47,143,255,.35);"></div>
        </div>
        """

    if symbol == "b":
        return f"""
        <div style="{base}
        background:linear-gradient(180deg,#eafff6,#dffff0);
        border:1px solid #a9e6c9;">
        <div style="
        width:24px;height:24px;
        border-radius:50%;
        background:radial-gradient(circle,#ffffff,#70c2ff,#2f8fff);"></div>
        </div>
        """

    return f"""<div style="{base}background:#fff;"></div>"""


def _parse(board: str):
    rows = [r.strip() for r in board.splitlines() if r.strip()]
    return [row.split() for row in rows]


def _render_board(board: str, done=False):
    grid = _parse(board)

    if not grid:
        grid = [["." for _ in range(10)] for _ in range(10)]

    rows = []

    for row in grid:
        cells = "".join(_cell(c) for c in row)
        rows.append(
            f"<div style='display:flex;gap:6px;margin-bottom:6px'>{cells}</div>"
        )

    solved = (
        """
        <div style="
            display:flex;
            justify-content:center;
            align-items:center;
            margin:18px 0 10px 0;
        ">
            <div class="solve" style="
                padding:14px 28px;
                border-radius:16px;
                border:1px solid rgba(255,255,255,0.18);
                background:linear-gradient(135deg,#10b981,#059669);
                color:white;
                font-size:18px;
                font-weight:800;
                letter-spacing:1.5px;
                text-transform:uppercase;
                box-shadow:0 10px 30px rgba(16,185,129,0.28);
                text-align:center;
                min-width:320px;
            ">
                ✨ PUZZLE SOLVED ✨
            </div>
        </div>
        """
        if done else ""
)

    return f"<div>{''.join(rows)}{solved}</div>"


# ==========================================================
# RIGHT PANEL
# ==========================================================

def _mini(title, val):
    return f"""
    <div class='card'>
        <div class='label'>{title}</div>
        <div class='value'>{val}</div>
    </div>
    """


def _kv_table(rows: list[tuple[str, str]]) -> str:
    """Render a guaranteed-visible key/value HTML table using inline styles."""
    body = []
    for key, value in rows:
        body.append(
            "<tr>"
            "<td style='width:42%;padding:10px 12px;background:#d8e0eb;border:1px solid #d2dce8;"
            "font-size:12px;font-weight:900;color:#5c6b80;text-transform:uppercase;letter-spacing:.04em;'>"
            f"{key}</td>"
            "<td style='width:58%;padding:10px 12px;background:#e8ecf4;border:1px solid #d2dce8;"
            "font-size:14px;font-weight:700;color:#1b3a5a;word-break:break-word;'>"
            f"{value}</td>"
            "</tr>"
        )
    return (
        "<table style='width:100%;border-collapse:collapse;border:1px solid #d2dce8;"
        "border-radius:12px;overflow:hidden;background:#eceff6;'>"
        + "".join(body)
        + "</table>"
    )


def _metrics(payload):
    obs = payload.get("observation", payload)
    done = payload.get("done", False)
    reward = payload.get("reward", obs.get("reward", 0))
    reward_display = f"{reward:+.2f}" if isinstance(reward, (int, float)) else str(reward)
    status_text = "SOLVED" if done else "RUNNING"
    status_color = "#0f9b6c" if done else "#2f8fff"
    table = _kv_table(
        [
            ("Level", html.escape(str(obs.get("level_index", "?")))),
            ("Moves", html.escape(f"{obs.get('step_count',0)}/{obs.get('max_steps',0)}")),
            ("Reward", html.escape(reward_display)),
            ("Status", f"<span style='color:{status_color};font-weight:900'>{status_text}</span>"),
        ]
    )
    return f"""
    <div class='right-box'>
        <div class='right-head'>Live Stats</div>
        {table}
    </div>
    """


def _obs(payload):
    obs = payload.get("observation", payload)

    player = html.escape(str(obs.get("agent_positions", [])))
    exits = html.escape(str(obs.get("exit_positions", [])))
    history = obs.get("previous_actions", [])
    moves_text = ", ".join(str(x) for x in history[-8:]) if history else "None"
    moves_text = html.escape(moves_text)

    table = _kv_table(
        [
            ("Players", html.escape(str(obs.get("num_players", 1)))),
            (
                "Agent Position",
                f"<span style='font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;color:#1e3a5f;font-weight:800;'>{player}</span>",
            ),
            (
                "Exit Position",
                f"<span style='font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;color:#1e3a5f;font-weight:800;'>{exits}</span>",
            ),
            (
                "Recent Moves",
                f"<span style='font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;color:#1e3a5f;font-weight:800;'>{moves_text}</span>",
            ),
        ]
    )

    return f"""
    <div class='right-box'>
        <div class='right-head'>Observation</div>
        {table}
    </div>
    """


# ==========================================================
# APP
# ==========================================================

def build_maze_gradio_app(
    web_manager: Any,
    action_fields: list[dict[str, Any]],
    metadata: Any,
    is_chat_env: bool,
    title: str,
    quick_start_md: str,
):

    env_name = getattr(metadata, "name", "maze_env")

    async def _reset():
        payload = await web_manager.reset_environment()
        obs = payload.get("observation", payload)
        done = payload.get("done", False)

        return (
            _render_board(obs.get("board", ""), done),
            _metrics(payload),
            _obs(payload),
            "Environment reset.",
        )

    async def _move(direction):
        payload = await web_manager.step_environment(
            {"direction": direction}
        )
        obs = payload.get("observation", payload)
        done = payload.get("done", False)

        return (
            _render_board(obs.get("board", ""), done),
            _metrics(payload),
            _obs(payload),
            f"Moved {direction}",
        )

    async def _up():
        return await _move("UP")

    async def _left():
        return await _move("LEFT")

    async def _right():
        return await _move("RIGHT")

    async def _down():
        return await _move("DOWN")

    def _state():
        web_manager.get_state()
        return "State loaded."

    with gr.Blocks(css=_CSS, title="MazeBench UI") as demo:

        gr.HTML(f"""
        <div id="mz-head" style="
            display:flex;
            flex-direction:column;
            align-items:center;
            justify-content:center;
            text-align:center;
            padding:18px 12px;
            gap:6px;
        ">

            <div id="mz-title" style="
                font-size:34px;
                font-weight:900;
                letter-spacing:2px;
                line-height:1.1;
                color:#1e3a5f;
                text-transform:uppercase;
            ">
                ❄️ MAZE BENCH ENVIRONMENT
            </div>

            <div id="mz-sub" style="
                font-size:14px;
                font-weight:600;
                color:#94a3b8;
                letter-spacing:3px;
                text-transform:uppercase;
            ">
                {env_name.upper()}
            </div>

        </div>
        """)

        with gr.Row():

            # LEFT
            with gr.Column(scale=1):

                with gr.Group(elem_classes="mz-card"):
                    with gr.Column(elem_classes="left-stack"):
                        with gr.Group(elem_classes="left-box"):
                            gr.HTML("<div class='left-head'>Controls</div>")
                            with gr.Row():
                                reset = gr.Button("RESET")
                                state = gr.Button("STATE")

                        with gr.Group(elem_classes="left-box"):
                            gr.HTML("<div class='left-head'>Direction Pad</div>")
                            with gr.Column(elem_classes="dpad"):
                                with gr.Row(elem_classes="dpad-row"):
                                    gr.HTML("<div class='dpad-slot'></div>")
                                    up = gr.Button("▲", elem_classes="dir")
                                    gr.HTML("<div class='dpad-slot'></div>")

                                with gr.Row(elem_classes="dpad-row"):
                                    left = gr.Button("◀", elem_classes="dir")
                                    gr.HTML("<div class='dpad-core'>•</div>")
                                    right = gr.Button("▶", elem_classes="dir")

                                with gr.Row(elem_classes="dpad-row"):
                                    gr.HTML("<div class='dpad-slot'></div>")
                                    down = gr.Button("▼", elem_classes="dir")
                                    gr.HTML("<div class='dpad-slot'></div>")

                        with gr.Group(elem_classes="left-box"):
                            gr.HTML("<div class='left-head'>Session Status</div>")
                            status = gr.Textbox(
                                label="Status",
                                value="Ready.",
                                interactive=False,
                                elem_id="status"
                            )

            # CENTER
            with gr.Column(scale=1.2):

                with gr.Group(elem_classes="mz-card"):
                    board = gr.HTML(
                        _render_board(""),
                        elem_id="mz-board"
                    )

            # RIGHT
            with gr.Column(scale=1):

                with gr.Group(elem_classes="mz-card"):
                    gr.HTML("<div class='section'>Telemetry</div>")
                    with gr.Column(elem_classes="right-stack"):
                        metrics = gr.HTML("<div class='right-box'><div class='right-head'>Live Stats</div><div style='color:#94a3b8;font-weight:700;'>Waiting for reset...</div></div>")
                        obs = gr.HTML("<div class='right-box'><div class='right-head'>Observation</div><div style='color:#94a3b8;font-weight:700;'>Waiting for reset...</div></div>")

        outputs = [board, metrics, obs, status]

        reset.click(_reset, outputs=outputs)

        up.click(_up, outputs=outputs)
        left.click(_left, outputs=outputs)
        right.click(_right, outputs=outputs)
        down.click(_down, outputs=outputs)

        state.click(_state, outputs=[status])

    return demo

