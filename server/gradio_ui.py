from __future__ import annotations

import html
import traceback
from typing import Any

import gradio as gr

MAZE_GRADIO_THEME = gr.themes.Base(
    primary_hue=gr.themes.colors.amber,
    secondary_hue=gr.themes.colors.stone,
    neutral_hue=gr.themes.colors.stone,
    font=[gr.themes.GoogleFont("Press Start 2P"), "monospace"],
).set(
    body_background_fill="#1a1209",
    body_background_fill_dark="#1a1209",
    background_fill_primary="#221a0d",
    background_fill_secondary="#2a2010",
    block_background_fill="#221a0d",
    block_border_color="#5c4a1e",
    block_label_text_color="#b89a4a",
    block_title_text_color="#e8c86a",
    border_color_primary="#5c4a1e",
    input_background_fill="#2a2010",
    input_border_color="#6b5520",
    button_primary_background_fill="#7a5c20",
    button_primary_background_fill_hover="#9a7428",
    button_primary_text_color="#ffe99a",
    button_secondary_background_fill="#2a2010",
    button_secondary_background_fill_hover="#3a2e14",
    button_secondary_text_color="#c8a84a",
    button_secondary_border_color="#5c4a1e",
)


_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=VT323:wght@400&display=swap');

:root {
    /* Core palette — earthy retro */
    --bg-deepest:   #0e0b05;
    --bg-deep:      #1a1209;
    --bg1:          #221a0d;
    --bg2:          #2a2010;
    --panel:        #2e2410;
    --panel-mid:    #352a12;
    --panel-inset:  #1e1609;
    --line:         #5c4a1e;
    --line-soft:    #3d2e10;
    --scanline:     rgba(0,0,0,.18);

    /* Text */
    --text:         #d4b86a;
    --text-head:    #f0d080;
    --muted:        #7a6030;

    /* Accent colours */
    --amber:        #d4960a;
    --amber-bright: #f0b820;
    --green:        #5a8a2a;
    --green-bright: #7ec832;
    --red:          #c04a2a;
    --red-bright:   #e86040;
    --teal:         #3a7a6a;
    --teal-bright:  #52b09a;

    /* Cell colours */
    --cell-wall:    #4a3510;
    --cell-wall-hi: #6a4d18;
    --cell-floor:   #1e1609;
    --cell-floor-hi:#261e0c;
    --cell-exit:    #1a3010;
    --cell-agent:   #2a1e08;
    --pixel-border: 2px solid;

    --font-pixel: 'Press Start 2P', monospace;
    --font-vt:    'VT323', monospace;
}

/* ── Reset & base ── */
html, body {
    background: var(--bg-deepest) !important;
    color: var(--text) !important;
    font-family: var(--font-pixel) !important;
    image-rendering: pixelated;
}

gradio-app {
    background: var(--bg-deepest) !important;
    --body-background-fill: var(--bg-deepest);
    --background-fill-primary: var(--bg1);
    --background-fill-secondary: var(--bg2);
    --block-background-fill: var(--panel);
}

body .gradio-container {
    background: transparent !important;
    font-family: var(--font-pixel) !important;
    color: var(--text) !important;
}

footer { display: none !important; }

.block-container {
    max-width: min(1520px, 96vw) !important;
    padding-top: 18px !important;
    padding-left: clamp(8px, 1.8vw, 22px) !important;
    padding-right: clamp(8px, 1.8vw, 22px) !important;
    background: transparent !important;
}

/* ── Scanline overlay on the whole page ── */
body::after {
    content: '';
    position: fixed;
    inset: 0;
    pointer-events: none;
    background: repeating-linear-gradient(
        0deg,
        var(--scanline) 0px,
        var(--scanline) 1px,
        transparent 1px,
        transparent 3px
    );
    z-index: 9999;
}

/* ── Pixel-border mixin (simulate retro bevel) ── */
.px-box {
    border: 3px solid var(--line);
    border-radius: 0 !important;
    box-shadow:
        inset 2px 2px 0 rgba(255,220,100,.08),
        inset -2px -2px 0 rgba(0,0,0,.5),
        3px 3px 0 #000;
    background: var(--panel);
    image-rendering: pixelated;
}

/* ── Header ── */
#mz-head {
    background: var(--bg-deepest);
    border: 3px solid var(--amber);
    border-radius: 0 !important;
    padding: 20px 24px 16px;
    margin-bottom: 16px;
    box-shadow: 4px 4px 0 #000, 0 0 40px rgba(212,150,10,.15);
    position: relative;
    overflow: hidden;
    text-align: center;
}

#mz-head::before {
    content: '';
    position: absolute;
    inset: 0;
    background: repeating-linear-gradient(
        90deg,
        transparent 0px,
        transparent 3px,
        rgba(212,150,10,.03) 3px,
        rgba(212,150,10,.03) 6px
    );
    pointer-events: none;
}

#mz-title {
    font-family: var(--font-pixel) !important;
    font-size: 22px !important;
    letter-spacing: 3px !important;
    color: var(--amber-bright) !important;
    text-shadow:
        2px 2px 0 #000,
        0 0 20px rgba(240,184,32,.4),
        0 0 40px rgba(240,184,32,.15);
    animation: flicker 6s infinite;
    line-height: 1.6 !important;
}

#mz-sub {
    font-family: var(--font-vt) !important;
    font-size: 20px !important;
    color: var(--teal-bright) !important;
    letter-spacing: 4px !important;
    text-shadow: 1px 1px 0 #000;
    margin-top: 4px;
}

@keyframes flicker {
    0%, 94%, 96%, 98%, 100% { opacity: 1; }
    95%, 97%, 99%            { opacity: .85; }
}

/* ── Buttons ── */
button {
    font-family: var(--font-pixel) !important;
    font-size: 9px !important;
    min-height: 52px !important;
    border-radius: 0 !important;
    border: 3px solid var(--line) !important;
    background: var(--panel-mid) !important;
    color: var(--text-head) !important;
    font-weight: 400 !important;
    transition: background .1s, transform .05s !important;
    box-shadow: 3px 3px 0 #000 !important;
    letter-spacing: .5px !important;
    text-transform: uppercase !important;
    image-rendering: pixelated;
}

button:hover {
    background: var(--bg2) !important;
    border-color: var(--amber) !important;
    color: var(--amber-bright) !important;
    transform: translate(-1px, -1px) !important;
    box-shadow: 4px 4px 0 #000 !important;
}

button:active {
    transform: translate(2px, 2px) !important;
    box-shadow: 1px 1px 0 #000 !important;
}

/* ── D-pad specific ── */
.dir button {
    min-height: clamp(56px, 9vw, 72px) !important;
    min-width: clamp(56px, 9vw, 72px) !important;
    font-size: clamp(12px, 2.1vw, 14px) !important;
    color: var(--amber-bright) !important;
    border-color: var(--amber) !important;
}

.dir button:hover {
    background: var(--amber) !important;
    color: #000 !important;
}

.dpad {
    display: flex;
    flex-direction: column;
    gap: 8px;
    background: var(--panel-inset);
    border: 3px solid var(--line);
    padding: 12px;
    box-shadow: inset 2px 2px 0 rgba(0,0,0,.5), 3px 3px 0 #000;
}

.dpad-row {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 8px;
    align-items: center;
}

.dpad-slot {
    height: clamp(56px, 9vw, 72px);
    background: var(--bg-deepest);
    border: 2px dashed var(--line-soft);
}

.dpad-core {
    height: clamp(56px, 9vw, 72px);
    background: var(--bg-deepest);
    border: 2px solid var(--line);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--muted);
    font-family: var(--font-vt);
    font-size: 26px;
    box-shadow: inset 2px 2px 0 rgba(0,0,0,.5);
}

/* ── Board container ── */
#mz-board {
    min-height: clamp(360px, 58vh, 600px);
    display: flex;
    justify-content: center;
    align-items: center;
    background: var(--bg-deepest);
    border: 3px solid var(--line);
    padding: clamp(10px, 2vw, 20px);
    box-shadow: inset 3px 3px 0 rgba(0,0,0,.6), 4px 4px 0 #000;
    position: relative;
    overflow: auto;
}

#mz-board::before {
    content: 'MAZE BOARD';
    position: absolute;
    top: 6px; left: 10px;
    font-family: var(--font-vt);
    font-size: 14px;
    color: var(--muted);
    letter-spacing: 2px;
}

/* ── Card shells ── */
.mz-card {
    background: var(--panel);
    border: 3px solid var(--line);
    border-radius: 0 !important;
    padding: 16px;
    box-shadow: 4px 4px 0 #000;
}

.left-stack, .right-stack { display: flex; flex-direction: column; gap: 14px; }

.left-box, .right-box {
    background: var(--panel-inset);
    border: 2px solid var(--line-soft);
    padding: 14px;
    box-shadow: inset 1px 1px 0 rgba(0,0,0,.4);
}

.left-head, .right-head {
    font-family: var(--font-pixel);
    font-size: 7px;
    color: var(--amber);
    font-weight: 400;
    letter-spacing: .1em;
    margin-bottom: 12px;
    text-transform: uppercase;
    text-shadow: 1px 1px 0 #000;
    border-bottom: 1px solid var(--line-soft);
    padding-bottom: 8px;
}

.section {
    font-family: var(--font-pixel);
    font-size: 8px;
    font-weight: 400;
    color: var(--amber-bright);
    margin-bottom: 10px;
    text-shadow: 1px 1px 0 #000;
    letter-spacing: .08em;
}

/* ── Status banner ── */
#status textarea, #status input {
    background: var(--bg-deepest) !important;
    border: 2px solid var(--line) !important;
    color: var(--text) !important;
    font-family: var(--font-vt) !important;
    font-size: 16px !important;
}

.mz-status {
    border: 2px solid var(--line);
    background: var(--bg-deepest);
    padding: 12px;
    line-height: 1.5;
    box-shadow: inset 1px 1px 0 rgba(0,0,0,.6);
}

.mz-status-head {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 6px;
}

.mz-status-tone {
    font-family: var(--font-pixel);
    font-size: 7px;
    font-weight: 400;
    letter-spacing: .08em;
    text-transform: uppercase;
}

.mz-status-msg {
    font-family: var(--font-vt);
    font-size: 17px;
    color: var(--text-head);
    white-space: pre-wrap;
}

.mz-status.ok  { border-color: var(--green);       box-shadow: inset 0 0 0 1px rgba(94,138,42,.2); }
.mz-status.ok  .mz-status-tone { color: var(--green-bright); }
.mz-status.err { border-color: var(--red);          box-shadow: inset 0 0 0 1px rgba(192,74,42,.2); }
.mz-status.err .mz-status-tone { color: var(--red-bright); }
.mz-status.info .mz-status-tone { color: var(--teal-bright); }

.mz-status details { margin-top: 8px; color: var(--muted); font-family: var(--font-vt); }
.mz-status pre {
    margin: 6px 0 0 0; padding: 8px;
    background: var(--bg-deepest); border: 1px solid var(--line-soft);
    color: var(--text); max-height: 180px; overflow: auto;
    font-family: var(--font-vt); font-size: 14px;
}

/* ── Reward panel ── */
.reward-total {
    font-family: var(--font-pixel);
    font-size: 18px;
    color: var(--green-bright);
    letter-spacing: .05em;
    text-shadow: 2px 2px 0 #000, 0 0 16px rgba(126,200,50,.3);
}
.reward-total.neg { color: var(--red-bright); text-shadow: 2px 2px 0 #000, 0 0 16px rgba(232,96,64,.3); }
.reward-step-val { font-family: var(--font-vt); font-size: 26px; font-weight: 400; }
.reward-step-val.pos  { color: var(--green-bright); }
.reward-step-val.neg  { color: var(--red-bright); }
.reward-step-val.zero { color: var(--muted); }

/* ── KV table ── */
table { border-collapse: collapse; width: 100%; }
.kv-key {
    width: 42%; padding: 8px 10px;
    background: var(--bg-deepest); border: 1px solid var(--line-soft);
    font-family: var(--font-pixel); font-size: 6px;
    color: var(--muted); text-transform: uppercase; letter-spacing: .06em;
}
.kv-val {
    width: 58%; padding: 8px 10px;
    background: var(--panel-inset); border: 1px solid var(--line-soft);
    font-family: var(--font-vt); font-size: 16px;
    color: var(--text-head); word-break: break-word;
}

/* ── Message banner ── */
.mz-msg {
    margin-top: 10px; padding: 10px 12px;
    background: var(--bg-deepest); border: 2px solid var(--line-soft);
    font-family: var(--font-vt); font-size: 16px;
    color: var(--text); line-height: 1.4;
    display: flex; align-items: center; gap: 8px;
}

/* ── Step strip ── */
.step-strip-wrap {
    display: block; width: 100%; min-width: 0;
    overflow-x: auto; overflow-y: hidden;
    height: 36px; scrollbar-width: thin;
    scrollbar-color: var(--line) transparent;
    box-sizing: border-box;
}
.step-strip-wrap::-webkit-scrollbar { height: 3px; }
.step-strip-wrap::-webkit-scrollbar-track { background: transparent; }
.step-strip-wrap::-webkit-scrollbar-thumb { background: var(--amber); }

.step-strip {
    display: inline-flex; flex-direction: row; flex-wrap: nowrap;
    gap: 5px; align-items: center; height: 28px; padding: 0 2px;
}

.step-chip {
    display: inline-flex; align-items: center; flex-shrink: 0;
    padding: 4px 10px;
    font-family: var(--font-pixel); font-size: 7px;
    border: 2px solid var(--amber); background: var(--panel-inset);
    color: var(--amber-bright); white-space: nowrap; letter-spacing: .04em;
    box-shadow: 1px 1px 0 #000;
}

.step-chip.step-old {
    color: var(--muted); background: var(--bg-deepest);
    border-color: var(--line-soft);
}

/* ── Solve banner ── */
.solve-banner {
    margin: 16px 0 8px;
    padding: 16px 24px;
    background: var(--green);
    border: 3px solid var(--green-bright);
    text-align: center;
    font-family: var(--font-pixel);
    font-size: 13px;
    color: #fff;
    letter-spacing: 2px;
    text-transform: uppercase;
    text-shadow: 2px 2px 0 #000;
    box-shadow: 4px 4px 0 #000, 0 0 30px rgba(126,200,50,.3);
    animation: pulse-solve .8s ease-in-out infinite alternate;
}

@keyframes pulse-solve {
    from { box-shadow: 4px 4px 0 #000, 0 0 20px rgba(126,200,50,.2); }
    to   { box-shadow: 4px 4px 0 #000, 0 0 50px rgba(126,200,50,.5); }
}

/* ── Number input label ── */
label span, .label-wrap span {
    font-family: var(--font-pixel) !important;
    font-size: 7px !important;
    color: var(--muted) !important;
    letter-spacing: .06em !important;
}

input[type=number] {
    font-family: var(--font-vt) !important;
    font-size: 18px !important;
    background: var(--bg-deepest) !important;
    border: 2px solid var(--line) !important;
    color: var(--amber-bright) !important;
    border-radius: 0 !important;
}

/* ── Equal-height columns ── */
.col-equal {
    height: 100%;
    box-sizing: border-box;
}

/* Gradio wraps Groups in divs — make the row itself stretch children */
.gradio-row {
    align-items: stretch !important;
}
.gradio-row > .gradio-column > .gradio-group.col-equal {
    height: 100%;
}

.mz-main-row { align-items: stretch !important; }
.mz-col-left, .mz-col-center, .mz-col-right { min-width: 0 !important; }

.mz-gh-link {
    display:inline-flex;
    align-items:center;
    gap:8px;
    padding:10px 16px;
    font-family:'Press Start 2P',monospace;
    font-size:7px;
    color:#d4960a;
    background:#0e0b05;
    border:2px solid #d4960a;
    text-decoration:none;
    letter-spacing:.08em;
    text-transform:uppercase;
    box-shadow:3px 3px 0 #000;
    white-space: nowrap;
}

.mz-gh-link:hover {
    background:#d4960a;
    color:#000;
    transform:translate(-1px, -1px);
    box-shadow:4px 4px 0 #000;
}

/* ── Responsive ── */
@media (max-width: 1100px) {
    #mz-board { min-height: 480px; }
    .dir button { min-height: 62px !important; min-width: 62px !important; }
}
@media (max-width: 1220px) {
    .mz-main-row { flex-wrap: wrap; }
    .mz-col-center { order: 1; }
    .mz-col-left { order: 2; }
    .mz-col-right { order: 3; }
}
@media (max-width: 760px) {
    #mz-title { font-size: 14px !important; letter-spacing: 1px !important; }
    #mz-sub   { font-size: 16px !important; }
    #mz-board { min-height: 350px; padding: 10px; }
    .block-container { padding-top: 10px !important; }
    #mz-head { padding: 14px 12px 12px !important; }
    .mz-gh-link {
        width: 100%;
        justify-content: center;
        margin-top: 8px;
        font-size: 6.5px;
    }
}
"""


MAZE_GRADIO_CSS = _CSS


# ==========================================================
# BOARD RENDERER — chunky pixel cells
# ==========================================================

def _cell(symbol: str) -> str:
    """Render a single maze cell as a chunky pixel tile."""

    # Base square — no border-radius, crisp pixel look
    base = (
        "width:clamp(24px,4.5vw,44px);height:clamp(24px,4.5vw,44px);"
        "display:flex;justify-content:center;align-items:center;"
        "flex-shrink:0;image-rendering:pixelated;"
        "box-sizing:border-box;position:relative;"
    )

    if symbol == "#":
        # Wall — dark earthy brown with bevel
        return (
            f'<div style="{base}'
            'background:#3d2a0c;'
            'border-top:3px solid #6b4a1a;border-left:3px solid #5c3e12;'
            'border-bottom:3px solid #1a0f03;border-right:3px solid #231408;'
            'box-shadow:inset 1px 1px 0 rgba(255,200,80,.06);">'
            # tiny dot texture
            '<div style="width:6px;height:6px;background:rgba(0,0,0,.3);'
            'position:absolute;top:6px;left:6px;"></div>'
            '<div style="width:4px;height:4px;background:rgba(255,200,80,.06);'
            'position:absolute;bottom:8px;right:8px;"></div>'
            '</div>'
        )

    if symbol == ".":
        # Floor — very dark with subtle grid
        return (
            f'<div style="{base}'
            'background:#1a1209;'
            'border:1px solid #2a1e0a;">'
            '</div>'
        )

    if symbol == "e":
        # Exit — green glow, diamond icon
        return (
            f'<div style="{base}'
            'background:#162610;'
            'border-top:3px solid #3a6a18;border-left:3px solid #2e5412;'
            'border-bottom:3px solid #0a1205;border-right:3px solid #0e1a08;">'
            '<div style="width:16px;height:16px;transform:rotate(45deg);'
            'background:#5a9a28;'
            'box-shadow:0 0 8px rgba(90,154,40,.8),0 0 16px rgba(90,154,40,.4);">'
            '</div>'
            '</div>'
        )

    if symbol == "a":
        # Agent A — amber glowing orb
        return (
            f'<div style="{base}'
            'background:#1a1209;'
            'border:1px solid #2a1e0a;">'
            '<div style="width:22px;height:22px;'
            'background:#d4960a;'
            'box-shadow:0 0 10px rgba(212,150,10,.9),0 0 20px rgba(212,150,10,.5);">'
            '</div>'
            '</div>'
        )

    if symbol == "b":
        # Agent B — teal glowing orb, on exit
        return (
            f'<div style="{base}'
            'background:#162610;'
            'border-top:3px solid #3a6a18;border-left:3px solid #2e5412;'
            'border-bottom:3px solid #0a1205;border-right:3px solid #0e1a08;">'
            '<div style="width:22px;height:22px;'
            'background:#3a9a80;'
            'box-shadow:0 0 10px rgba(58,154,128,.9),0 0 20px rgba(58,154,128,.5);">'
            '</div>'
            '</div>'
        )

    # fallback
    return f'<div style="{base}background:#120d05;border:1px solid #1e1508;"></div>'


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
            f"<div style='display:flex;gap:3px;margin-bottom:3px'>{cells}</div>"
        )

    solved = ""
    if done:
        solved = """
        <div class='solve-banner'>★ LEVEL COMPLETE ★</div>
        """

    return (
        f"<div style='display:flex;flex-direction:column;align-items:center;'>"
        f"{''.join(rows)}{solved}"
        f"</div>"
    )


# ==========================================================
# RIGHT PANEL HELPERS
# ==========================================================

def _kv_table(rows: list[tuple[str, str]]) -> str:
    body = [
        f"<tr>"
        f"<td class='kv-key'>{k}</td>"
        f"<td class='kv-val'>{v}</td>"
        f"</tr>"
        for k, v in rows
    ]
    return f"<table>{''.join(body)}</table>"


def _metrics_html(payload, reward_history: list[float]) -> str:
    obs = payload.get("observation", payload)
    done = payload.get("done", False)
    step_reward = payload.get("reward", obs.get("reward", 0))
    running_total = sum(reward_history) if reward_history else 0.0

    total_cls = "neg" if running_total < 0 else ""
    step_cls = "pos" if step_reward > 0 else ("neg" if step_reward < 0 else "zero")
    step_sign = "+" if isinstance(step_reward, (int, float)) and step_reward >= 0 else ""
    status_text = "SOLVED" if done else "RUNNING"
    status_color = "var(--green-bright)" if done else "var(--teal-bright)"

    table = _kv_table([
        ("Level",  html.escape(str(obs.get("level_index", "?")))),
        ("Moves",  html.escape(f"{obs.get('step_count', 0)}/{obs.get('max_steps', 0)}")),
        ("Status", f"<span style='color:{status_color};'>{status_text}</span>"),
    ])

    reward_breakdown = ""
    if reward_history:
        recent = reward_history[-8:]
        pills = []
        for r in reversed(recent):
            col = "var(--green-bright)" if r > 0 else ("var(--red-bright)" if r < 0 else "var(--muted)")
            sign = "+" if r >= 0 else ""
            pills.append(
                f"<span style='display:inline-block;padding:3px 8px;"
                f"border:1px solid var(--line-soft);"
                f"font-family:var(--font-vt);font-size:14px;"
                f"color:{col};margin:2px 3px 0 0;background:var(--bg-deepest);'>"
                f"{sign}{r:.2f}</span>"
            )
        reward_breakdown = (
            "<div style='margin-top:10px;'>"
            "<div style='font-family:var(--font-pixel);font-size:6px;color:var(--muted);"
            "letter-spacing:.06em;text-transform:uppercase;margin-bottom:6px;'>"
            "Recent rewards</div>"
            "<div>" + "".join(pills) + "</div>"
            "</div>"
        )

    return f"""
    <div class='right-box'>
        <div class='right-head'>◈ Live Stats</div>
        {table}
        <div style='margin-top:12px;background:var(--bg-deepest);border:2px solid var(--line-soft);padding:12px;'>
            <div style='display:grid;grid-template-columns:1fr 1fr;gap:12px;'>
                <div>
                    <div style='font-family:var(--font-pixel);font-size:6px;color:var(--muted);
                                text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px;'>
                        Total Reward</div>
                    <div class='reward-total {total_cls}'>{running_total:+.3f}</div>
                </div>
                <div>
                    <div style='font-family:var(--font-pixel);font-size:6px;color:var(--muted);
                                text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px;'>
                        Last Step</div>
                    <div class='reward-step-val {step_cls}'>
                        {step_sign}{step_reward:.3f}
                    </div>
                </div>
            </div>
            {reward_breakdown}
        </div>
    </div>
    """


_MAX_STEP_HISTORY = 30
_DIR_ICON = {"UP": "▲", "DOWN": "▼", "LEFT": "◀", "RIGHT": "▶"}


def _obs_html(payload, step_history: list[str]) -> str:
    obs = payload.get("observation", payload)
    player = html.escape(str(obs.get("agent_positions", [])))
    exits  = html.escape(str(obs.get("exit_positions", [])))

    raw_msg = obs.get("message", "") or ""
    msg_html = ""
    if raw_msg:
        msg_html = (
            f"<div class='mz-msg'>"
            f"<span style='color:var(--teal-bright);'>▶</span>"
            f"<span>{html.escape(str(raw_msg))}</span>"
            f"</div>"
        )

    table = _kv_table([
        ("Players",   html.escape(str(obs.get("num_players", 1)))),
        ("Agent Pos", f"<span style='color:var(--amber-bright);font-family:var(--font-vt);font-size:15px;'>{player}</span>"),
        ("Exit Pos",  f"<span style='color:var(--green-bright);font-family:var(--font-vt);font-size:15px;'>{exits}</span>"),
    ])

    visible = step_history[:_MAX_STEP_HISTORY]
    if visible:
        chips = []
        for i, step in enumerate(visible):
            icon = _DIR_ICON.get(step, step)
            cls  = "step-chip" if i < 3 else "step-chip step-old"
            chips.append(f"<span class='{cls}'>{icon}</span>")
        strip_inner = "".join(chips)
    else:
        strip_inner = (
            "<span style='color:var(--muted);font-family:var(--font-pixel);font-size:7px;'>"
            "NO MOVES YET</span>"
        )

    total_moves = len(step_history)
    shown_note = (
        f"<span style='color:var(--muted);font-family:var(--font-vt);font-size:13px;margin-left:4px;'>"
        f"({min(total_moves, _MAX_STEP_HISTORY)}/{total_moves})</span>"
        if total_moves > _MAX_STEP_HISTORY else ""
    )

    return f"""
    <div class='right-box'>
        <div class='right-head'>◈ Observation</div>
        {table}
        {msg_html}
        <div style='margin-top:12px;'>
            <div style='font-family:var(--font-pixel);font-size:6px;color:var(--muted);
                        text-transform:uppercase;letter-spacing:.06em;
                        margin-bottom:6px;display:flex;align-items:baseline;flex-wrap:wrap;gap:4px;'>
                Move History {shown_note}
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


def _how_to_win_html() -> str:
    return """
    <div class='right-box' style='margin-top:0;'>
        <div class='right-head'>◈ HOW TO WIN</div>

        <!-- Objective -->
        <div style='margin-bottom:12px;'>
            <div style='font-family:var(--font-pixel);font-size:7px;color:var(--amber);
                        letter-spacing:.06em;margin-bottom:8px;text-shadow:1px 1px 0 #000;'>
                OBJECTIVE
            </div>
            <div style='font-family:var(--font-vt);font-size:16px;color:var(--text-head);line-height:1.6;'>
                Move <span style='color:var(--amber-bright);'>●</span> the agent onto
                <span style='color:var(--green-bright);'>◆</span> the exit tile.<br>
                On <em>ice</em> — you slide until you hit a wall, so plan ahead!
            </div>
        </div>

        <!-- Legend -->
        <div style='display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:12px;'>
            <div style='background:var(--bg-deepest);border:1px solid var(--line-soft);
                        padding:7px 10px;display:flex;align-items:center;gap:8px;'>
                <span style='font-size:16px;'>⬛</span>
                <span style='font-family:var(--font-vt);font-size:14px;color:var(--muted);'>Wall</span>
            </div>
            <div style='background:var(--bg-deepest);border:1px solid var(--line-soft);
                        padding:7px 10px;display:flex;align-items:center;gap:8px;'>
                <span style='font-size:16px;color:#1a1209;background:#1a1209;width:16px;height:16px;display:inline-block;border:1px solid #2a1e0a;'></span>
                <span style='font-family:var(--font-vt);font-size:14px;color:var(--muted);'>Floor / Ice</span>
            </div>
            <div style='background:var(--bg-deepest);border:1px solid var(--line-soft);
                        padding:7px 10px;display:flex;align-items:center;gap:8px;'>
                <span style='font-size:16px;color:var(--amber-bright);'>●</span>
                <span style='font-family:var(--font-vt);font-size:14px;color:var(--muted);'>Your Agent</span>
            </div>
            <div style='background:var(--bg-deepest);border:1px solid var(--line-soft);
                        padding:7px 10px;display:flex;align-items:center;gap:8px;'>
                <span style='font-size:16px;color:var(--green-bright);'>◆</span>
                <span style='font-family:var(--font-vt);font-size:14px;color:var(--muted);'>Exit</span>
            </div>
        </div>

        <!-- Reward table -->
        <div style='font-family:var(--font-pixel);font-size:7px;color:var(--amber);
                    letter-spacing:.06em;margin-bottom:8px;text-shadow:1px 1px 0 #000;'>
            REWARD STRUCTURE
        </div>
        <table style='width:100%;border-collapse:collapse;margin-bottom:4px;'>
            <tr>
                <td style='padding:7px 10px;background:var(--bg-deepest);border:1px solid var(--line-soft);
                            font-family:var(--font-vt);font-size:15px;color:var(--green-bright);
                            white-space:nowrap;'>+10.0</td>
                <td style='padding:7px 10px;background:var(--panel-inset);border:1px solid var(--line-soft);
                            font-family:var(--font-vt);font-size:15px;color:var(--text-head);'>
                    Reach the exit 🏁
                </td>
            </tr>
            <tr>
                <td style='padding:7px 10px;background:var(--bg-deepest);border:1px solid var(--line-soft);
                            font-family:var(--font-vt);font-size:15px;color:var(--red-bright);
                            white-space:nowrap;'>−1.0</td>
                <td style='padding:7px 10px;background:var(--panel-inset);border:1px solid var(--line-soft);
                            font-family:var(--font-vt);font-size:15px;color:var(--text-head);'>
                    Repeat the same direction
                </td>
            </tr>
            <tr>
                <td style='padding:7px 10px;background:var(--bg-deepest);border:1px solid var(--line-soft);
                            font-family:var(--font-vt);font-size:15px;color:var(--red-bright);
                            white-space:nowrap;'>−1.0</td>
                <td style='padding:7px 10px;background:var(--panel-inset);border:1px solid var(--line-soft);
                            font-family:var(--font-vt);font-size:15px;color:var(--text-head);'>
                    Reverse direction (e.g. UP → DOWN)
                </td>
            </tr>
            <tr>
                <td style='padding:7px 10px;background:var(--bg-deepest);border:1px solid var(--line-soft);
                            font-family:var(--font-vt);font-size:15px;color:var(--red-bright);
                            white-space:nowrap;'>−1.0×N</td>
                <td style='padding:7px 10px;background:var(--panel-inset);border:1px solid var(--line-soft);
                            font-family:var(--font-vt);font-size:15px;color:var(--text-head);'>
                    Revisit a board state (×prior visits)
                </td>
            </tr>
            <tr>
                <td style='padding:7px 10px;background:var(--bg-deepest);border:1px solid var(--line-soft);
                            font-family:var(--font-vt);font-size:15px;color:var(--red-bright);
                            white-space:nowrap;'>−0.1×S</td>
                <td style='padding:7px 10px;background:var(--panel-inset);border:1px solid var(--line-soft);
                            font-family:var(--font-vt);font-size:15px;color:var(--text-head);'>
                    Steps wasted since last visit to that state (capped at 50)
                </td>
            </tr>
        </table>

        <!-- Tips -->
        <div style='font-family:var(--font-pixel);font-size:7px;color:var(--amber);
                    letter-spacing:.06em;margin:12px 0 8px;text-shadow:1px 1px 0 #000;'>
            PRO TIPS
        </div>
        <div style='display:flex;flex-direction:column;gap:5px;'>
            <div style='font-family:var(--font-vt);font-size:15px;color:var(--text);
                        background:var(--bg-deepest);border-left:3px solid var(--amber);
                        padding:6px 10px;line-height:1.4;'>
                ▶ Plan slides — you stop only at walls
            </div>
            <div style='font-family:var(--font-vt);font-size:15px;color:var(--text);
                        background:var(--bg-deepest);border-left:3px solid var(--amber);
                        padding:6px 10px;line-height:1.4;'>
                ▶ Avoid back-and-forth moves (−1 each)
            </div>
            <div style='font-family:var(--font-vt);font-size:15px;color:var(--text);
                        background:var(--bg-deepest);border-left:3px solid var(--green-bright);
                        padding:6px 10px;line-height:1.4;'>
                ▶ New board states = no penalty, explore!
            </div>
            <div style='font-family:var(--font-vt);font-size:15px;color:var(--text);
                        background:var(--bg-deepest);border-left:3px solid var(--green-bright);
                        padding:6px 10px;line-height:1.4;'>
                ▶ Solve in fewer steps = cleaner score
            </div>
        </div>
    </div>
    """


def build_maze_gradio_app(
    web_manager: Any,
    action_fields: list[dict[str, Any]],
    metadata: Any,
    is_chat_env: bool,
    title: str,
    quick_start_md: str,
):
    env_name = getattr(metadata, "name", "maze_env")

    _state: dict = {"reward_history": [], "step_history": [], "last_payload": None}

    def _status_html(message: str, tone: str = "info", detail: str | None = None) -> str:
        tone_cls = {"success": "ok", "error": "err"}.get(tone, "info")
        badge    = {"success": "SUCCESS", "error": "ERROR"}.get(tone, "INFO")
        icon     = {"success": "◆", "error": "✖"}.get(tone, "►")
        detail_html = ""
        if detail:
            detail_html = (
                "<details><summary>Debug details</summary>"
                f"<pre>{html.escape(detail)}</pre></details>"
            )
        return (
            f"<div class='mz-status {tone_cls}'>"
            f"<div class='mz-status-head'>"
            f"<span style='color:inherit;'>{icon}</span>"
            f"<span class='mz-status-tone'>{badge}</span></div>"
            f"<div class='mz-status-msg'>{html.escape(message)}</div>"
            f"{detail_html}</div>"
        )

    def _pack(payload, status_msg, tone: str = "info", detail: str | None = None):
        obs  = payload.get("observation", payload)
        done = payload.get("done", False)
        _state["last_payload"] = payload
        return (
            _render_board(obs.get("board", ""), done),
            _metrics_html(payload, _state["reward_history"]),
            _obs_html(payload, _state["step_history"]),
            _status_html(status_msg, tone=tone, detail=detail),
        )

    def _pack_error(status_msg: str, detail: str | None = None):
        prev = _state.get("last_payload")
        if prev:
            return _pack(prev, status_msg, tone="error", detail=detail)
        empty = {"observation": {"board": ""}, "done": False, "reward": 0.0}
        return (
            _render_board("", False),
            _metrics_html(empty, _state["reward_history"]),
            _obs_html(empty, _state["step_history"]),
            _status_html(status_msg, tone="error", detail=detail),
        )

    def _current_payload() -> dict[str, Any]:
        prev = _state.get("last_payload")
        if isinstance(prev, dict):
            return prev
        return {"observation": {"board": ""}, "done": False, "reward": 0.0}

    def _merge_runtime_state_into_payload(st: dict[str, Any]) -> dict[str, Any]:
        import copy
        base = _state.get("last_payload")
        if base is None:
            return {
                "observation": {
                    "board":           st.get("current_board") or "",
                    "step_count":      st.get("step_count", 0),
                    "max_steps":       0,
                    "level_index":     st.get("level_index", -1),
                    "agent_positions": st.get("agent_positions") or [],
                    "exit_positions":  st.get("exit_positions") or [],
                    "num_players":     st.get("num_players", 1),
                    "message":         "",
                },
                "done":   bool(st.get("done", False)),
                "reward": None,
            }
        payload = copy.deepcopy(base)
        obs = payload.setdefault("observation", {})
        for k, sk in [("board","current_board"),("step_count","step_count"),
                      ("level_index","level_index"),("agent_positions","agent_positions"),
                      ("exit_positions","exit_positions"),("num_players","num_players")]:
            if sk in st and st[sk] is not None:
                obs[k] = st[sk]
        hist = st.get("action_history")
        if isinstance(hist, list) and hist:
            note = f"Moves so far ({len(hist)}): {' '.join(map(str, hist[-12:]))}"
            obs["message"] = ((obs.get("message") or "") + "\n\n" + note).strip()
        payload["done"] = bool(st.get("done", payload.get("done", False)))
        return payload

    def _normalized_level_arg(raw: Any) -> dict[str, Any]:
        if raw is None: return {}
        if isinstance(raw, float):
            import math
            if math.isnan(raw): return {}
        try:
            if raw == "": return {}
        except TypeError:
            pass
        try:
            idx = int(raw)
        except (TypeError, ValueError):
            return {}
        return {"level_index": idx}

    # ── callbacks ────────────────────────────────────────────────
    async def _reset(level_idx: Any):
        try:
            _state["reward_history"].clear()
            _state["step_history"].clear()
            kwargs = _normalized_level_arg(level_idx)
            payload = await web_manager.reset_environment(kwargs or None)
            # Auto-increment: if a level was specified, bump it for next reset
            next_level = gr.update()
            if kwargs and "level_index" in kwargs:
                next_level = gr.update(value=kwargs["level_index"] + 1)
            board_h, metrics_h, obs_h, status_h = _pack(payload, "Environment reset.", tone="success")
            return board_h, metrics_h, obs_h, status_h, next_level
        except Exception as exc:
            board_h, metrics_h, obs_h, status_h = _pack_error(f"Reset failed: {exc}", detail=traceback.format_exc(limit=6))
            return board_h, metrics_h, obs_h, status_h, gr.update()

    async def _move(direction: str):
        try:
            payload = await web_manager.step_environment({"direction": direction})
        except Exception as exc:
            return _pack_error(f"Step failed: {exc}", detail=traceback.format_exc(limit=6))
        step_reward = payload.get("reward", payload.get("observation", {}).get("reward", 0))
        _state["reward_history"].append(float(step_reward) if isinstance(step_reward, (int, float)) else 0.0)
        _state["step_history"].insert(0, direction)
        if len(_state["step_history"]) > _MAX_STEP_HISTORY:
            _state["step_history"] = _state["step_history"][:_MAX_STEP_HISTORY]
        return _pack(payload, f"Moved {direction}")

    async def _up():    return await _move("UP")
    async def _left():  return await _move("LEFT")
    async def _right(): return await _move("RIGHT")
    async def _down():  return await _move("DOWN")

    async def _keyboard_move(direction: str):
        key = str(direction or "").strip().upper()
        if key in _DIR_ICON:
            board_html, metrics_html, obs_html, status_html = await _move(key)
            return board_html, metrics_html, obs_html, status_html, ""
        payload = _current_payload()
        board_html, metrics_html, obs_html, _ = _pack(payload, "Keyboard controls ready.")
        return board_html, metrics_html, obs_html, _status_html("Keyboard controls ready."), ""

    def _refresh_from_state():
        try:
            st = web_manager.get_state()
            if not isinstance(st, dict):
                st = st.model_dump() if hasattr(st, "model_dump") else dict(st)
            merged = _merge_runtime_state_into_payload(st)
            return _pack(merged, "Synced from environment state.")
        except Exception as exc:
            return _pack_error(f"State sync failed: {exc}\n{traceback.format_exc()}")

    # ── Layout ────────────────────────────────────────────────────
    with gr.Blocks(title="MazeBench") as demo:

        gr.HTML(f"""
        <div id="mz-head" style="display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:12px;min-height:72px;">
            <div style="display:flex;flex-direction:column;align-items:center;gap:4px;text-align:center;grid-column:2;">
                <div id="mz-title">⬛ MAZE BENCH ⬛</div>
                <div id="mz-sub">{env_name.upper()} · ARCADE EDITION</div>
            </div>
            <a href="https://github.com/Vidit-Ostwal/Maze-Bench-OpenEnv"
               target="_blank" rel="noopener noreferrer"
               class="mz-gh-link" style="grid-column:3;justify-self:end;">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577
                         0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61-.546-1.385-1.335-1.755-1.335-1.755
                         -1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305
                         3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93
                         0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176
                         0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405
                         1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23
                         .645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22
                         0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22
                         0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57
                         C20.565 21.795 24 17.295 24 12c0-6.63-5.37-12-12-12z"/>
              </svg>
              View on GitHub
            </a>
        </div>
        """)

        with gr.Row(elem_classes="mz-main-row"):

            # ── LEFT column ──────────────────────────────────────
            with gr.Column(scale=4, min_width=220, elem_classes="mz-col-left"):
                with gr.Group(elem_classes="mz-card col-equal"):
                    with gr.Column(elem_classes="left-stack"):

                        with gr.Group(elem_classes="left-box"):
                            gr.HTML("<div class='left-head'>◈ Controls</div>")
                            level_idx = gr.Number(
                                label="Level Index",
                                value=None,
                                precision=0,
                                container=True,
                                info="Leave blank for default. Set before RESET.",
                            )
                            with gr.Row():
                                reset_btn = gr.Button("▶ RESET")
                                state_btn = gr.Button("⟳ SYNC")
                            gr.HTML("""
                            <button
                              onclick="document.getElementById('mz-htw-modal').style.display='flex'"
                              style="width:100%;margin-top:6px;cursor:pointer;">
                              ? HOW TO WIN
                            </button>
                            """)

                        with gr.Group(elem_classes="left-box"):
                            gr.HTML("<div class='left-head'>◈ D-Pad</div>")
                            with gr.Column(elem_classes="dpad"):
                                with gr.Row(elem_classes="dpad-row"):
                                    gr.HTML("<div class='dpad-slot'></div>")
                                    up_btn = gr.Button("▲", elem_classes="dir")
                                    gr.HTML("<div class='dpad-slot'></div>")
                                with gr.Row(elem_classes="dpad-row"):
                                    left_btn  = gr.Button("◀", elem_classes="dir")
                                    gr.HTML("<div class='dpad-core'>✦</div>")
                                    right_btn = gr.Button("▶", elem_classes="dir")
                                with gr.Row(elem_classes="dpad-row"):
                                    gr.HTML("<div class='dpad-slot'></div>")
                                    down_btn = gr.Button("▼", elem_classes="dir")
                                    gr.HTML("<div class='dpad-slot'></div>")

                        status = gr.HTML(_status_html("INSERT COIN TO PLAY…"), elem_id="status", visible=False)
                        keybind_input = gr.Textbox(
                            value="", visible=False, elem_id="mz-keybind",
                        )

            # ── CENTER column ─────────────────────────────────────
            with gr.Column(scale=4, min_width=280, elem_classes="mz-col-center"):
                with gr.Group(elem_classes="mz-card col-equal"):
                    board = gr.HTML(_render_board(""), elem_id="mz-board")

            # ── RIGHT column ──────────────────────────────────────
            with gr.Column(scale=4, min_width=220, elem_classes="mz-col-right"):
                with gr.Group(elem_classes="mz-card col-equal"):
                    gr.HTML("<div class='section'>◈ TELEMETRY</div>")
                    with gr.Column(elem_classes="right-stack"):
                        metrics = gr.HTML(
                            "<div class='right-box'>"
                            "<div class='right-head'>◈ Live Stats</div>"
                            "<div style='font-family:var(--font-vt);font-size:17px;"
                            "color:var(--muted);'>Awaiting reset…</div>"
                            "</div>"
                        )
                        obs_panel = gr.HTML(
                            "<div class='right-box'>"
                            "<div class='right-head'>◈ Observation</div>"
                            "<div style='font-family:var(--font-vt);font-size:17px;"
                            "color:var(--muted);'>Awaiting reset…</div>"
                            "</div>"
                        )

        # ── How-To-Win modal ─────────────────────────────────────────
        gr.HTML("""
        <div id="mz-htw-modal" style="
            display:none;position:fixed;inset:0;z-index:99999;
            background:rgba(0,0,0,.82);
            align-items:center;justify-content:center;">
          <div style="
              background:#1a1209;border:3px solid #d4960a;
              box-shadow:6px 6px 0 #000,0 0 60px rgba(212,150,10,.2);
              max-width:480px;width:90%;padding:28px 26px 24px;">
            <div style="
                font-family:'Press Start 2P',monospace;font-size:11px;
                color:#f0b820;letter-spacing:.1em;margin-bottom:18px;
                text-shadow:2px 2px 0 #000;text-align:center;">
              ★ HOW TO WIN ★
            </div>
            <div style="font-family:'VT323',monospace;font-size:18px;color:#d4b86a;line-height:1.7;">
              <div style="margin-bottom:10px;">
                <span style="color:#f0b820;">◆</span>
                Navigate the agent <span style="color:#d4960a;">●</span>
                to the exit <span style="color:#7ec832;">◆</span>
              </div>
              <div style="margin-bottom:10px;">
                <span style="color:#f0b820;">◆</span>
                Use <span style="color:#d4960a;">Arrow Keys</span> or
                <span style="color:#d4960a;">WASD</span> to move
              </div>
              <div style="margin-bottom:10px;">
                <span style="color:#f0b820;">◆</span>
                Fewer steps = higher reward score
              </div>
              <div style="margin-bottom:10px;">
                <span style="color:#f0b820;">◆</span>
                Walls <span style="color:#7a6030;">█</span> block movement — plan your route
              </div>
              <div style="margin-bottom:18px;">
                <span style="color:#f0b820;">◆</span>
                Hit <span style="color:#d4960a;">▶ RESET</span> to start a new level anytime
              </div>
            </div>
            <div style="
                display:grid;grid-template-columns:1fr 1fr;gap:10px;
                font-family:'VT323',monospace;font-size:15px;
                color:#7a6030;border-top:1px solid #3d2e10;
                padding-top:14px;text-align:center;margin-bottom:18px;">
              <div><span style="color:#d4960a;">●</span> Agent = YOU</div>
              <div><span style="color:#7ec832;">◆</span> Exit = GOAL</div>
              <div><span style="color:#6b4a1a;">█</span> Wall = BLOCKED</div>
              <div><span style="color:#52b09a;">✦</span> Floor = WALKABLE</div>
            </div>
            <button onclick="document.getElementById('mz-htw-modal').style.display='none'"
                    style="width:100%;cursor:pointer;">
              ✖ CLOSE
            </button>
          </div>
        </div>
        """)

        outputs          = [board, metrics, obs_panel, status]
        outputs_with_key = [board, metrics, obs_panel, status, keybind_input]
        outputs_reset    = [board, metrics, obs_panel, status, level_idx]

        reset_btn.click(_reset, inputs=[level_idx], outputs=outputs_reset)
        up_btn.click(_up,                  outputs=outputs)
        left_btn.click(_left,              outputs=outputs)
        right_btn.click(_right,            outputs=outputs)
        down_btn.click(_down,              outputs=outputs)
        state_btn.click(_refresh_from_state, outputs=outputs)
        keybind_input.change(
            _keyboard_move, inputs=[keybind_input], outputs=outputs_with_key
        )

        demo.load(
            None, None, None,
            js="""
            () => {
              /* ── Favicon: pixel maze icon as inline SVG data URI ── */
              (function() {
                const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">
                  <rect width="16" height="16" fill="#1a1209"/>
                  <rect x="0" y="0" width="2" height="2" fill="#d4960a"/>
                  <rect x="2" y="0" width="2" height="2" fill="#d4960a"/>
                  <rect x="4" y="0" width="2" height="2" fill="#d4960a"/>
                  <rect x="6" y="0" width="2" height="2" fill="#d4960a"/>
                  <rect x="8" y="0" width="2" height="2" fill="#d4960a"/>
                  <rect x="10" y="0" width="2" height="2" fill="#d4960a"/>
                  <rect x="12" y="0" width="2" height="2" fill="#d4960a"/>
                  <rect x="14" y="0" width="2" height="2" fill="#d4960a"/>
                  <rect x="0" y="2" width="2" height="2" fill="#d4960a"/>
                  <rect x="4" y="2" width="2" height="2" fill="#d4960a"/>
                  <rect x="8" y="2" width="2" height="2" fill="#d4960a"/>
                  <rect x="12" y="2" width="2" height="2" fill="#d4960a"/>
                  <rect x="14" y="2" width="2" height="2" fill="#d4960a"/>
                  <rect x="0" y="4" width="2" height="2" fill="#d4960a"/>
                  <rect x="2" y="4" width="2" height="2" fill="#d4960a"/>
                  <rect x="4" y="4" width="2" height="2" fill="#d4960a"/>
                  <rect x="8" y="4" width="2" height="2" fill="#d4960a"/>
                  <rect x="10" y="4" width="2" height="2" fill="#d4960a"/>
                  <rect x="12" y="4" width="2" height="2" fill="#d4960a"/>
                  <rect x="0" y="6" width="2" height="2" fill="#d4960a"/>
                  <rect x="8" y="6" width="2" height="2" fill="#d4960a"/>
                  <rect x="14" y="6" width="2" height="2" fill="#d4960a"/>
                  <rect x="0" y="8" width="2" height="2" fill="#d4960a"/>
                  <rect x="2" y="8" width="2" height="2" fill="#d4960a"/>
                  <rect x="4" y="8" width="2" height="2" fill="#d4960a"/>
                  <rect x="6" y="8" width="2" height="2" fill="#d4960a"/>
                  <rect x="8" y="8" width="2" height="2" fill="#d4960a"/>
                  <rect x="12" y="8" width="2" height="2" fill="#d4960a"/>
                  <rect x="14" y="8" width="2" height="2" fill="#d4960a"/>
                  <rect x="0" y="10" width="2" height="2" fill="#d4960a"/>
                  <rect x="10" y="10" width="2" height="2" fill="#d4960a"/>
                  <rect x="14" y="10" width="2" height="2" fill="#d4960a"/>
                  <rect x="0" y="12" width="2" height="2" fill="#d4960a"/>
                  <rect x="2" y="12" width="2" height="2" fill="#d4960a"/>
                  <rect x="4" y="12" width="2" height="2" fill="#d4960a"/>
                  <rect x="6" y="12" width="2" height="2" fill="#d4960a"/>
                  <rect x="10" y="12" width="2" height="2" fill="#d4960a"/>
                  <rect x="12" y="12" width="2" height="2" fill="#d4960a"/>
                  <rect x="14" y="12" width="2" height="2" fill="#d4960a"/>
                  <rect x="0" y="14" width="2" height="2" fill="#d4960a"/>
                  <rect x="14" y="14" width="2" height="2" fill="#d4960a"/>
                  <!-- agent dot -->
                  <rect x="6" y="6" width="2" height="2" fill="#f0b820"/>
                  <!-- exit dot -->
                  <rect x="10" y="14" width="2" height="2" fill="#5a8a2a"/>
                  <rect x="12" y="14" width="2" height="2" fill="#5a8a2a"/>
                </svg>`;
                const encoded = encodeURIComponent(svg);
                const dataUri = "data:image/svg+xml," + encoded;
                let link = document.querySelector("link[rel~='icon']");
                if (!link) {
                  link = document.createElement("link");
                  link.rel = "icon";
                  document.head.appendChild(link);
                }
                link.href = dataUri;
                link.type = "image/svg+xml";
              })();

              if (window.__mazeKeysBound) return;
              window.__mazeKeysBound = true;

              /* Map keys -> button aria-label fragments we can query */
              const btnMap = {
                ArrowUp:    'up_btn',    w: 'up_btn',    W: 'up_btn',
                ArrowDown:  'down_btn',  s: 'down_btn',  S: 'down_btn',
                ArrowLeft:  'left_btn',  a: 'left_btn',  A: 'left_btn',
                ArrowRight: 'right_btn', d: 'right_btn', D: 'right_btn',
              };

              /* Gradio renders buttons inside elem_id wrappers —
                 find them by the elem_classes we gave the Column wrappers.
                 Fallback: just grab all buttons whose text is the arrow glyph. */
              const glyphMap = {
                ArrowUp:'▲', ArrowDown:'▼', ArrowLeft:'◀', ArrowRight:'▶',
                w:'▲', s:'▼', a:'◀', d:'▶',
                W:'▲', S:'▼', A:'◀', D:'▶',
              };

              function clickDir(key) {
                const glyph = glyphMap[key];
                if (!glyph) return false;
                /* Search every button on the page for a matching glyph */
                const btns = Array.from(document.querySelectorAll('button'));
                const match = btns.find(b => b.textContent.trim() === glyph);
                if (match) { match.click(); return true; }
                return false;
              }

              /* Use capture phase so we intercept BEFORE Gradio's own handlers,
                 and always preventDefault for arrow keys to stop page scroll. */
              window.addEventListener('keydown', (ev) => {
                if (ev.repeat) return;
                if (!glyphMap[ev.key]) return;

                /* Always block browser scroll for arrow keys */
                if (ev.key.startsWith('Arrow')) ev.preventDefault();

                /* Blur whatever has focus so the click registers cleanly */
                if (document.activeElement && document.activeElement !== document.body) {
                  document.activeElement.blur();
                }

                clickDir(ev.key);
              }, true /* capture */);

              console.log('[MazeBench] Keyboard controls active — Arrow keys & WASD');
            }
            """,
        )

    return demo