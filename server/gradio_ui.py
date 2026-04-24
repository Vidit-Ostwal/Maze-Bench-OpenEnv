from __future__ import annotations

import html
from typing import Any

import gradio as gr

MAZE_GRADIO_THEME = gr.themes.Soft(
    primary_hue=gr.themes.colors.sky,
    secondary_hue=gr.themes.colors.blue,
    neutral_hue=gr.themes.colors.slate,
).set(
    body_background_fill="#111827",
    body_background_fill_dark="#111827",
    background_fill_primary="#1a2235",
    background_fill_secondary="#151e2e",
    block_background_fill="#1a2235",
    block_border_color="#2a3a52",
    block_label_text_color="#64748b",
    block_title_text_color="#93c5fd",
    border_color_primary="#2a3a52",
    input_background_fill="#0f172a",
    input_border_color="#2a3a52",
    button_primary_background_fill="#0ea5e9",
    button_primary_background_fill_hover="#0284c7",
    button_primary_text_color="#ffffff",
    button_secondary_background_fill="#1e2d42",
    button_secondary_background_fill_hover="#253348",
    button_secondary_text_color="#93c5fd",
    button_secondary_border_color="#2a3a52",
)


# ==========================================================
# CSS — dark, cohesive, no white surfaces
# ==========================================================

_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

:root{
    --bg-deep:#0d1525;
    --bg1:#111827;
    --bg2:#151e2e;
    --panel:#1a2438;
    --panel-mid:#1e2a40;
    --panel-inset:#0f1929;
    --line:#2a3a52;
    --line-soft:#1e2d42;
    --text:#c8daf0;
    --text-head:#e2eeff;
    --muted:#4a6080;
    --blue:#38bdf8;
    --blue-dim:#1e6fa8;
    --green:#10b981;
    --green-dim:#065f46;
    --amber:#f59e0b;
    --red:#f87171;
    --cell-wall-a:#2563a8;
    --cell-wall-b:#1a4a80;
    --cell-path-a:#1e2d42;
    --cell-path-b:#192638;
}

html, body {
    background: var(--bg-deep) !important;
    background-color: var(--bg-deep) !important;
    font-family: Inter, sans-serif !important;
    color: var(--text) !important;
}

gradio-app {
    background: var(--bg-deep) !important;
    background-color: var(--bg-deep) !important;
    --body-background-fill: var(--bg-deep);
    --background-fill-primary: var(--bg1);
    --background-fill-secondary: var(--bg2);
    --block-background-fill: var(--panel);
}

body .gradio-container {
    background: transparent !important;
    font-family: Inter, sans-serif !important;
    color: var(--text) !important;
}

footer { display: none !important; }

.block-container {
    max-width: 1480px !important;
    padding-top: 22px !important;
    background: transparent !important;
}

/* ── Card shell ── */
.mz-card {
    background: linear-gradient(180deg, var(--panel) 0%, var(--panel-mid) 100%);
    border: 1px solid var(--line);
    border-radius: 24px;
    padding: 18px;
    box-shadow: 0 8px 32px rgba(0,0,0,.45);
}

/* ── Header ── */
#mz-head {
    background: linear-gradient(135deg, var(--panel-inset), var(--bg2));
    border: 1px solid var(--line);
    border-radius: 24px;
    padding: 18px 24px;
    margin-bottom: 14px;
}

/* ── Board ── */
#mz-board {
    min-height: 640px;
    display: flex;
    justify-content: center;
    align-items: center;
    border-radius: 24px;
    background: linear-gradient(180deg, var(--panel-inset) 0%, var(--bg2) 100%);
    border: 1px solid var(--line);
    padding: 18px;
}

/* ── Buttons ── */
button {
    min-height: 58px !important;
    border-radius: 18px !important;
    border: 1px solid var(--line) !important;
    background: linear-gradient(180deg, var(--panel-mid), var(--panel-inset)) !important;
    color: var(--text-head) !important;
    font-weight: 800 !important;
    transition: .18s ease !important;
}

button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0,0,0,.4);
    border-color: var(--blue-dim) !important;
}

.dir button {
    min-height: 76px !important;
    min-width: 76px !important;
    font-size: 1.45rem !important;
    font-weight: 900 !important;
    border-radius: 22px !important;
    color: var(--blue) !important;
}

/* ── D-pad ── */
.dpad {
    display: flex;
    flex-direction: column;
    gap: 10px;
    background: var(--panel-inset);
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 10px;
}

.dpad-row {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 10px;
    align-items: center;
}

.dpad-slot {
    height: 76px;
    border-radius: 22px;
    border: 1px dashed var(--line-soft);
    background: var(--bg-deep);
}

.dpad-core {
    height: 76px;
    border-radius: 22px;
    border: 1px solid var(--line);
    background: var(--panel);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--muted);
    font-weight: 900;
}

/* ── Typography helpers ── */
.section {
    font-size: 1rem;
    font-weight: 900;
    color: var(--text-head);
    margin-bottom: 10px;
}

.left-stack, .right-stack { display: flex; flex-direction: column; gap: 12px; }

.left-box, .right-box {
    background: linear-gradient(180deg, var(--panel-inset), var(--panel));
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 14px;
}

.left-head, .right-head {
    font-size: .78rem;
    color: var(--muted);
    font-weight: 900;
    letter-spacing: .06em;
    margin-bottom: 10px;
    text-transform: uppercase;
}

/* ── Status textbox ── */
#status textarea, #status input {
    background: var(--bg-deep) !important;
    border: 1px solid var(--line) !important;
    border-radius: 14px !important;
    color: var(--text) !important;
    font-weight: 700 !important;
}

/* ── Solve banner ── */
.solve {
    margin-top: 12px;
    text-align: center;
    font-weight: 900;
    color: var(--green);
}

/* ── Step history scroll strip ── */
.step-strip-wrap {
    display: block;             /* explicit block so it doesn't collapse */
    width: 100%;
    min-width: 0;               /* allow shrink inside flex parents */
    overflow-x: auto;
    overflow-y: hidden;
    /* fixed height = one row of chips + scrollbar; never grows vertically */
    height: 38px;
    scrollbar-width: thin;
    scrollbar-color: var(--line) transparent;
    box-sizing: border-box;
}
.step-strip-wrap::-webkit-scrollbar { height: 4px; }
.step-strip-wrap::-webkit-scrollbar-track { background: transparent; }
.step-strip-wrap::-webkit-scrollbar-thumb { background: var(--line); border-radius: 99px; }

.step-strip {
    display: inline-flex;       /* inline-flex → width hugs content, enabling scroll */
    flex-direction: row;
    flex-wrap: nowrap;
    gap: 6px;
    align-items: center;
    height: 30px;               /* match chip height so no vertical overflow */
    padding: 0 2px;
}

.step-chip {
    display: inline-flex;
    align-items: center;
    flex-shrink: 0;
    padding: 4px 11px;
    border-radius: 999px;
    font-size: .76rem;
    font-weight: 900;
    letter-spacing: .04em;
    white-space: nowrap;
    border: 1px solid var(--line);
    background: var(--panel-inset);
    color: var(--blue);
    line-height: 1;
}

.step-chip.step-old {
    color: var(--muted);
    background: var(--bg-deep);
    border-color: var(--line-soft);
}


/* ── Last-move message banner ── */
.mz-msg {
    margin-top: 10px;
    padding: 10px 14px;
    border-radius: 12px;
    background: var(--panel-inset);
    border: 1px solid var(--line);
    font-size: .85rem;
    font-weight: 700;
    color: var(--text);
    line-height: 1.45;
    min-height: 38px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.mz-msg-icon {
    font-size: 1rem;
    flex-shrink: 0;
}
/* ── Reward panel ── */
.reward-total {
    font-size: 2rem;
    font-weight: 900;
    color: var(--green);
    letter-spacing: .02em;
}
.reward-total.neg { color: var(--red); }
.reward-step-val {
    font-size: 1rem;
    font-weight: 800;
}
.reward-step-val.pos { color: var(--green); }
.reward-step-val.neg { color: var(--red); }
.reward-step-val.zero { color: var(--muted); }
"""


# ==========================================================
# BOARD RENDERER
# ==========================================================

def _cell(symbol: str) -> str:
    base = (
        "width:46px;height:46px;"
        "border-radius:14px;"
        "display:flex;"
        "justify-content:center;"
        "align-items:center;"
        "flex-shrink:0;"
    )

    if symbol == "#":
        return (
            f'<div style="{base}'
            'background:linear-gradient(135deg,#2563a8,#1a4a80);'
            'border:1px solid #1d3d6e;box-shadow:inset 0 2px 4px rgba(0,0,0,.4);"></div>'
        )

    if symbol == ".":
        return (
            f'<div style="{base}'
            'background:linear-gradient(180deg,#1e2d42,#192638);'
            'border:1px solid #253548;"></div>'
        )

    if symbol == "e":
        return (
            f'<div style="{base}'
            'background:linear-gradient(180deg,#0a2a1e,#052016);'
            'border:1px solid #0d5c38;">'
            '<div style="width:18px;height:18px;transform:rotate(45deg);'
            'background:#10b981;border-radius:3px;'
            'box-shadow:0 0 10px rgba(16,185,129,.6);"></div>'
            '</div>'
        )

    if symbol == "a":
        return (
            f'<div style="{base}'
            'background:linear-gradient(180deg,#1e2d42,#192638);'
            'border:1px solid #253548;">'
            '<div style="width:24px;height:24px;border-radius:50%;'
            'background:radial-gradient(circle,#ffffff,#70c2ff,#2f8fff);'
            'box-shadow:0 0 14px rgba(47,143,255,.55);"></div>'
            '</div>'
        )

    if symbol == "b":
        return (
            f'<div style="{base}'
            'background:linear-gradient(180deg,#0a2a1e,#052016);'
            'border:1px solid #0d5c38;">'
            '<div style="width:24px;height:24px;border-radius:50%;'
            'background:radial-gradient(circle,#ffffff,#70c2ff,#2f8fff);'
            'box-shadow:0 0 10px rgba(47,143,255,.4);"></div>'
            '</div>'
        )

    return f'<div style="{base}background:#0d1525;"></div>'


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

    solved = ""
    if done:
        solved = """
        <div style="display:flex;justify-content:center;align-items:center;margin:18px 0 10px 0;">
            <div style="
                padding:14px 28px;border-radius:16px;
                background:linear-gradient(135deg,#10b981,#059669);
                color:white;font-size:18px;font-weight:800;
                letter-spacing:1.5px;text-transform:uppercase;
                box-shadow:0 10px 30px rgba(16,185,129,.35);
                text-align:center;min-width:320px;">
                ✨ PUZZLE SOLVED ✨
            </div>
        </div>"""

    return f"<div>{''.join(rows)}{solved}</div>"


# ==========================================================
# RIGHT PANEL — metrics, rewards, observations
# ==========================================================

_KV_KEY = (
    "width:42%;padding:10px 12px;"
    "background:var(--panel-inset);border:1px solid var(--line);"
    "font-size:12px;font-weight:900;color:var(--muted);"
    "text-transform:uppercase;letter-spacing:.04em;"
)
_KV_VAL = (
    "width:58%;padding:10px 12px;"
    "background:var(--bg1);border:1px solid var(--line);"
    "font-size:14px;font-weight:700;color:var(--text);"
    "word-break:break-word;"
)
_KV_WRAP = (
    "width:100%;border-collapse:collapse;"
    "border:1px solid var(--line);border-radius:12px;overflow:hidden;"
)


def _kv_table(rows: list[tuple[str, str]]) -> str:
    body = [
        f"<tr><td style='{_KV_KEY}'>{k}</td><td style='{_KV_VAL}'>{v}</td></tr>"
        for k, v in rows
    ]
    return f"<table style='{_KV_WRAP}'>{''.join(body)}</table>"


def _metrics_html(payload, reward_history: list[float]) -> str:
    obs = payload.get("observation", payload)
    done = payload.get("done", False)
    step_reward = payload.get("reward", obs.get("reward", 0))
    running_total = sum(reward_history) if reward_history else 0.0

    total_cls = "neg" if running_total < 0 else ""
    step_cls = "pos" if step_reward > 0 else ("neg" if step_reward < 0 else "zero")
    step_sign = "+" if isinstance(step_reward, (int, float)) and step_reward >= 0 else ""

    status_text = "SOLVED" if done else "RUNNING"
    status_color = "var(--green)" if done else "var(--blue)"

    table = _kv_table([
        ("Level", html.escape(str(obs.get("level_index", "?")))),
        ("Moves", html.escape(f"{obs.get('step_count', 0)}/{obs.get('max_steps', 0)}")),
        ("Status", f"<span style='color:{status_color};font-weight:900'>{status_text}</span>"),
    ])

    reward_breakdown = ""
    if reward_history:
        recent = reward_history[-8:]          # show last 8 pills
        pills = []
        for r in reversed(recent):
            col = "var(--green)" if r > 0 else ("var(--red)" if r < 0 else "var(--muted)")
            sign = "+" if r >= 0 else ""
            pills.append(
                f"<span style='display:inline-block;padding:3px 9px;border-radius:999px;"
                f"background:var(--panel-inset);border:1px solid var(--line);"
                f"font-size:11px;font-weight:800;color:{col};margin:2px 3px 0 0;'>"
                f"{sign}{r:.2f}</span>"
            )
        reward_breakdown = (
            "<div style='margin-top:8px;'>"
            "<div style='font-size:10px;font-weight:900;color:var(--muted);"
            "letter-spacing:.06em;text-transform:uppercase;margin-bottom:5px;'>"
            "Recent step rewards (newest → oldest)</div>"
            "<div style='display:flex;flex-wrap:wrap;'>" + "".join(pills) + "</div>"
            "</div>"
        )

    return f"""
    <div class='right-box'>
        <div class='right-head'>Live Stats</div>
        {table}

        <div style='margin-top:12px;background:var(--panel-inset);border:1px solid var(--line);
                    border-radius:14px;padding:12px;'>

            <div style='display:grid;grid-template-columns:1fr 1fr;gap:10px;'>
                <div>
                    <div style='font-size:10px;font-weight:900;color:var(--muted);
                                text-transform:uppercase;letter-spacing:.06em;
                                margin-bottom:6px;'>Total Reward</div>
                    <div class='reward-total {total_cls}'>{running_total:+.3f}</div>
                </div>
                <div>
                    <div style='font-size:10px;font-weight:900;color:var(--muted);
                                text-transform:uppercase;letter-spacing:.06em;
                                margin-bottom:6px;'>Last Step</div>
                    <div class='reward-step-val {step_cls}' style='font-size:1.5rem;'>
                        {step_sign}{step_reward:.3f}
                    </div>
                </div>
            </div>

            {reward_breakdown}
        </div>
    </div>
    """


# Max step chips to keep — oldest are discarded beyond this limit
_MAX_STEP_HISTORY = 30

# Arrow icons for direction chips
_DIR_ICON = {"UP": "▲", "DOWN": "▼", "LEFT": "◀", "RIGHT": "▶"}


def _obs_html(payload, step_history: list[str]) -> str:
    obs = payload.get("observation", payload)

    player = html.escape(str(obs.get("agent_positions", [])))
    exits  = html.escape(str(obs.get("exit_positions", [])))

    # message field — feedback on the last move
    raw_msg = obs.get("message", "") or ""
    msg_html = ""
    if raw_msg:
        icon = "💬"
        msg_html = (
            f"<div class='mz-msg'>"
            f"<span class='mz-msg-icon'>{icon}</span>"
            f"<span>{html.escape(str(raw_msg))}</span>"
            f"</div>"
        )

    table = _kv_table([
        ("Players",  html.escape(str(obs.get("num_players", 1)))),
        ("Agent Pos",
         f"<span style='font-family:ui-monospace,monospace;color:var(--blue);font-weight:800;'>{player}</span>"),
        ("Exit Pos",
         f"<span style='font-family:ui-monospace,monospace;color:var(--blue);font-weight:800;'>{exits}</span>"),
    ])

    # Cap history — newest-first list, keep only the most recent _MAX_STEP_HISTORY
    visible = step_history[:_MAX_STEP_HISTORY]

    if visible:
        chips = []
        for i, step in enumerate(visible):
            icon = _DIR_ICON.get(step, step)
            cls  = "step-chip" if i < 3 else "step-chip step-old"
            # <span> not <div> — avoids implicit block layout breaking the strip
            chips.append(f"<span class='{cls}'>{icon}</span>")
        strip_inner = "".join(chips)
    else:
        strip_inner = (
            "<span style='color:var(--muted);font-size:.8rem;font-weight:700;'>"
            "No moves yet</span>"
        )

    total_moves = len(step_history)
    shown_note = (
        f"<span style='color:var(--muted);font-size:.72rem;font-weight:600;margin-left:4px;'>"
        f"(showing {min(total_moves, _MAX_STEP_HISTORY)} of {total_moves})</span>"
        if total_moves > _MAX_STEP_HISTORY else ""
    )

    return f"""
    <div class='right-box'>
        <div class='right-head'>Observation</div>
        {table}
        {msg_html}

        <div style='margin-top:12px;'>
            <div style='font-size:10px;font-weight:900;color:var(--muted);
                        text-transform:uppercase;letter-spacing:.06em;
                        margin-bottom:6px;display:flex;align-items:baseline;flex-wrap:wrap;gap:4px;'>
                Move History
                <span style='color:var(--blue-dim);font-weight:700;text-transform:none;letter-spacing:0;'>
                — newest left</span>
                {shown_note}
            </div>
            <div class='step-strip-wrap'>
                <div class='step-strip'>{strip_inner}</div>
            </div>
        </div>
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

    # ── in-memory state ──────────────────────────────────
    _state: dict = {"reward_history": [], "step_history": []}

    # ── helpers ──────────────────────────────────────────
    def _pack(payload, status_msg):
        obs = payload.get("observation", payload)
        done = payload.get("done", False)
        return (
            _render_board(obs.get("board", ""), done),
            _metrics_html(payload, _state["reward_history"]),
            _obs_html(payload, _state["step_history"]),
            status_msg,
        )

    # ── callbacks ─────────────────────────────────────────
    async def _reset():
        _state["reward_history"].clear()
        _state["step_history"].clear()
        payload = await web_manager.reset_environment()
        return _pack(payload, "Environment reset.")

    async def _move(direction: str):
        payload = await web_manager.step_environment({"direction": direction})

        # record reward
        step_reward = payload.get("reward", payload.get("observation", {}).get("reward", 0))
        _state["reward_history"].append(float(step_reward) if isinstance(step_reward, (int, float)) else 0.0)

        # record step — newest first; cap at _MAX_STEP_HISTORY entries
        _state["step_history"].insert(0, direction)
        if len(_state["step_history"]) > _MAX_STEP_HISTORY:
            _state["step_history"] = _state["step_history"][:_MAX_STEP_HISTORY]

        return _pack(payload, f"Moved {direction}")

    async def _up():    return await _move("UP")
    async def _left():  return await _move("LEFT")
    async def _right(): return await _move("RIGHT")
    async def _down():  return await _move("DOWN")

    def _state_btn():
        web_manager.get_state()
        return "State loaded."

    # ── layout ────────────────────────────────────────────
    with gr.Blocks(css=_CSS, title="MazeBench UI", theme=MAZE_GRADIO_THEME) as demo:

        gr.HTML(f"""
        <div id="mz-head" style="
            display:flex;flex-direction:column;
            align-items:center;justify-content:center;
            text-align:center;padding:18px 12px;gap:6px;">
            <div id="mz-title" style="
                font-size:34px;font-weight:900;letter-spacing:2px;
                line-height:1.1;color:#e2eeff;text-transform:uppercase;">
                ❄️ MAZE BENCH ENVIRONMENT
            </div>
            <div id="mz-sub" style="
                font-size:14px;font-weight:600;color:#4a6080;
                letter-spacing:3px;text-transform:uppercase;">
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
                                reset_btn = gr.Button("RESET")
                                state_btn = gr.Button("STATE")

                        with gr.Group(elem_classes="left-box"):
                            gr.HTML("<div class='left-head'>Direction Pad</div>")
                            with gr.Column(elem_classes="dpad"):
                                with gr.Row(elem_classes="dpad-row"):
                                    gr.HTML("<div class='dpad-slot'></div>")
                                    up_btn = gr.Button("▲", elem_classes="dir")
                                    gr.HTML("<div class='dpad-slot'></div>")
                                with gr.Row(elem_classes="dpad-row"):
                                    left_btn  = gr.Button("◀", elem_classes="dir")
                                    gr.HTML("<div class='dpad-core'>•</div>")
                                    right_btn = gr.Button("▶", elem_classes="dir")
                                with gr.Row(elem_classes="dpad-row"):
                                    gr.HTML("<div class='dpad-slot'></div>")
                                    down_btn = gr.Button("▼", elem_classes="dir")
                                    gr.HTML("<div class='dpad-slot'></div>")

                        with gr.Group(elem_classes="left-box"):
                            gr.HTML("<div class='left-head'>Session Status</div>")
                            status = gr.Textbox(
                                label="Status",
                                value="Ready.",
                                interactive=False,
                                elem_id="status",
                            )

            # CENTER
            with gr.Column(scale=1.2):
                with gr.Group(elem_classes="mz-card"):
                    board = gr.HTML(_render_board(""), elem_id="mz-board")

            # RIGHT
            with gr.Column(scale=1):
                with gr.Group(elem_classes="mz-card"):
                    gr.HTML("<div class='section'>Telemetry</div>")
                    with gr.Column(elem_classes="right-stack"):
                        metrics = gr.HTML(
                            "<div class='right-box'>"
                            "<div class='right-head'>Live Stats</div>"
                            "<div style='color:#4a6080;font-weight:700;'>Waiting for reset…</div>"
                            "</div>"
                        )
                        obs_panel = gr.HTML(
                            "<div class='right-box'>"
                            "<div class='right-head'>Observation</div>"
                            "<div style='color:#4a6080;font-weight:700;'>Waiting for reset…</div>"
                            "</div>"
                        )

        outputs = [board, metrics, obs_panel, status]

        reset_btn.click(_reset,   outputs=outputs)
        up_btn.click(_up,         outputs=outputs)
        left_btn.click(_left,     outputs=outputs)
        right_btn.click(_right,   outputs=outputs)
        down_btn.click(_down,     outputs=outputs)
        state_btn.click(_state_btn, outputs=[status])

    return demo