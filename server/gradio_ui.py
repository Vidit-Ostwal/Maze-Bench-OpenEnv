from __future__ import annotations

import html
import json
from typing import Any

import gradio as gr


# ==========================================================
# ICE OPS UI
# ==========================================================

_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

:root{
    --bg1:#f7fbff;
    --bg2:#dfeeff;
    --panel:#ffffffd9;
    --line:#d8e9ff;
    --text:#17324d;
    --muted:#6f89a8;
    --blue:#2f8fff;
    --blue2:#71c2ff;
    --green:#11c989;
}

body, .gradio-container{
    background:
        radial-gradient(circle at top left,#ffffff 0%,transparent 30%),
        radial-gradient(circle at bottom right,#d8ebff 0%,transparent 35%),
        linear-gradient(135deg,var(--bg1),var(--bg2));
    font-family:Inter,sans-serif!important;
    color:var(--text)!important;
}

footer{display:none!important;}

.block-container{
    max-width:1480px!important;
    padding-top:22px!important;
}

.mz-card{
    background:var(--panel);
    backdrop-filter:blur(14px);
    border:1px solid var(--line);
    border-radius:24px;
    padding:18px;
    box-shadow:0 12px 28px rgba(40,90,170,.08);
}

#mz-head{
    background:linear-gradient(135deg,#ffffff,#eef7ff);
    border:1px solid var(--line);
    border-radius:24px;
    padding:18px 24px;
    margin-bottom:14px;
}

#mz-title{
    font-size:1.55rem;
    font-weight:900;
    color:#16324f;
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
    background:linear-gradient(180deg,#ffffff,#edf7ff);
    border:1px solid var(--line);
    padding:18px;
}

button{
    min-height:58px!important;
    border-radius:18px!important;
    border:1px solid #d5e8ff!important;
    background:linear-gradient(180deg,#ffffff,#f3f9ff)!important;
    color:#17324d!important;
    font-weight:800!important;
    transition:.18s ease!important;
}

button:hover{
    transform:translateY(-2px);
    box-shadow:0 10px 18px rgba(40,90,170,.12);
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
    border:1px dashed #d9e9ff;
    background:linear-gradient(180deg,#f8fcff,#eef6ff);
}

.dpad-core{
    height:76px;
    border-radius:22px;
    border:1px solid #d8e8ff;
    background:linear-gradient(180deg,#ffffff,#f4faff);
    display:flex;
    align-items:center;
    justify-content:center;
    color:#8aa8c8;
    font-weight:900;
    letter-spacing:.1em;
}

.section{
    font-size:1rem;
    font-weight:900;
    color:#17324d;
    margin-bottom:10px;
}

.grid{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:10px;
}

.card{
    background:linear-gradient(180deg,#ffffff,#f8fbff);
    border:1px solid #dbeaff;
    border-radius:18px;
    padding:14px;
}

.label{
    font-size:.72rem;
    color:#6e88a7;
    font-weight:900;
    letter-spacing:.04em;
}

.value{
    margin-top:7px;
    font-size:1.2rem;
    font-weight:900;
    color:#17324d;
}

.info{
    margin-top:12px;
    background:linear-gradient(180deg,#ffffff,#f8fbff);
    border:1px solid #dbeaff;
    border-radius:18px;
    padding:14px;
}

.right-stack{
    display:flex;
    flex-direction:column;
    gap:12px;
}

.right-box{
    background:linear-gradient(180deg,#ffffff,#f8fbff);
    border:1px solid #dbeaff;
    border-radius:18px;
    padding:14px;
}

.right-head{
    font-size:.78rem;
    color:#6f88a8;
    font-weight:900;
    letter-spacing:.06em;
    margin-bottom:8px;
    text-transform:uppercase;
}

.kv-table{
    border:1px solid #dbeaff;
    border-radius:14px;
    overflow:hidden;
    background:#ffffff;
}

.kv-row{
    display:grid;
    grid-template-columns: 42% 58%;
    border-top:1px solid #e6f0ff;
}

.kv-row:first-child{
    border-top:none;
}

.kv-key{
    padding:10px 12px;
    background:#f4f9ff;
    font-size:.74rem;
    font-weight:900;
    color:#6887ab;
    letter-spacing:.04em;
    text-transform:uppercase;
    border-right:1px solid #e6f0ff;
}

.kv-val{
    padding:10px 12px;
    font-size:.88rem;
    font-weight:700;
    color:#1b3a5a;
    word-break:break-word;
    line-height:1.45;
}

.kv-val.status-ok{ color:#0f9b6c; }
.kv-val.status-run{ color:#2f8fff; }

.chip{
    display:inline-block;
    padding:8px 12px;
    border-radius:999px;
    margin:6px 8px 0 0;
    font-size:.82rem;
    font-weight:900;
    border:1px solid #d8e8ff;
    background:#eef6ff;
    color:#24548e;
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
    background:#ffffff!important;
    border:1px solid #dbeaff!important;
    border-radius:14px!important;
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
        "<div class='solve'>PUZZLE SOLVED ✨</div>"
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
            "<td style='width:42%;padding:10px 12px;background:#f4f9ff;border:1px solid #dbeaff;"
            "font-size:12px;font-weight:900;color:#5f82a8;text-transform:uppercase;letter-spacing:.04em;'>"
            f"{key}</td>"
            "<td style='width:58%;padding:10px 12px;background:#ffffff;border:1px solid #dbeaff;"
            "font-size:14px;font-weight:700;color:#1b3a5a;word-break:break-word;'>"
            f"{value}</td>"
            "</tr>"
        )
    return (
        "<table style='width:100%;border-collapse:collapse;border:1px solid #dbeaff;"
        "border-radius:12px;overflow:hidden;background:#ffffff;'>"
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
                f"<span style='font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;color:#0f2740;font-weight:800;'>{player}</span>",
            ),
            (
                "Exit Position",
                f"<span style='font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;color:#0f2740;font-weight:800;'>{exits}</span>",
            ),
            (
                "Recent Moves",
                f"<span style='font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;color:#0f2740;font-weight:800;'>{moves_text}</span>",
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
            json.dumps(payload, indent=2),
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
            json.dumps(payload, indent=2),
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
        state = web_manager.get_state()
        return json.dumps(state, indent=2), "State loaded."

    with gr.Blocks(css=_CSS, title="MazeBench UI") as demo:

        gr.HTML(f"""
        <div id='mz-head'>
            <div id='mz-title'>❄️ MAZEBENCH // ICE OPS</div>
            <div id='mz-sub'>
                {env_name.upper()} • Premium puzzle dashboard
            </div>
        </div>
        """)

        with gr.Row():

            # LEFT
            with gr.Column(scale=1):

                with gr.Group(elem_classes="mz-card"):

                    gr.Markdown("## Controls")

                    with gr.Row():
                        reset = gr.Button("RESET")
                        state = gr.Button("STATE")

                    gr.Markdown("## Move")

                    with gr.Row():
                        gr.HTML("<div class='section'>Direction Pad</div>")

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

                    status = gr.Textbox(
                        label="Status",
                        value="Ready.",
                        interactive=False,
                        elem_id="status"
                    )

            # CENTER
            with gr.Column(scale=1.45):

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
                        metrics = gr.HTML("<div class='right-box'><div class='right-head'>Live Stats</div><div style='color:#7a91ac;font-weight:700;'>Waiting for reset...</div></div>")
                        obs = gr.HTML("<div class='right-box'><div class='right-head'>Observation</div><div style='color:#7a91ac;font-weight:700;'>Waiting for reset...</div></div>")

        with gr.Accordion("Raw Payload", open=False):
            payload_box = gr.Code(language="json")

        outputs = [board, metrics, obs, payload_box, status]

        reset.click(_reset, outputs=outputs)

        up.click(_up, outputs=outputs)
        left.click(_left, outputs=outputs)
        right.click(_right, outputs=outputs)
        down.click(_down, outputs=outputs)

        state.click(_state, outputs=[payload_box, status])

    return demo