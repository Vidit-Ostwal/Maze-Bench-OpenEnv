"""Render Maze rollout observations as a styled animated GIF — redesigned UI."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ─── Palette ────────────────────────────────────────────────────────────────
BG            = "#080C18"
PANEL_TOP     = "#0D1525"
PANEL_BORDER  = "#1C2B4A"

WALL_DARK     = "#0E1623"
WALL_LIGHT    = "#182236"
WALL_EDGE     = "#263554"

ICE_DARK      = "#12213D"
ICE_LIGHT     = "#1A2E50"
ICE_SHIMMER   = "#2A4880"
ICE_INNER     = "#0F1B30"

EXIT_GLOW     = "#00FFB0"
EXIT_BASE     = "#00C47A"
EXIT_DARK     = "#006644"

AGENT_CORE    = "#4E8EFF"
AGENT_RING    = "#A0C4FF"
AGENT_GLOW    = "#1A3A80"
AGENT_WIN     = "#BE7FFF"
AGENT_WIN_RING= "#E0B8FF"

ARROW_BRIGHT  = "#00EEFF"
ARROW_DIM     = "#1A4A55"

GRID_LINE     = "#0E1C35"

TEXT_HEAD     = "#E8F4FF"
TEXT_BODY     = "#7A9BC8"
TEXT_DIM      = "#3A5070"
TEXT_ACCENT   = "#00EEFF"
TEXT_GOLD     = "#FFD166"
TEXT_GREEN    = "#3BF0A0"

BADGE_BG      = "#0D1930"
BADGE_BORDER  = "#1E3460"


# Font candidates per role — tried in order, first found wins.
_FONT_CANDIDATES: dict[str, list[str]] = {
    "bold": [
        # Linux (DejaVu)
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        # macOS system fonts
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSDisplay.ttf",
        "/Library/Fonts/Arial Bold.ttf",
    ],
    "mono_bold": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Courier New Bold.ttf",
        "/System/Library/Fonts/Courier.ttc",
        "/Library/Fonts/Courier New Bold.ttf",
    ],
    "mono": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/System/Library/Fonts/Supplemental/Courier New.ttf",
        "/System/Library/Fonts/Courier.ttc",
        "/Library/Fonts/Courier New.ttf",
    ],
    "regular": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ],
}


def _lf(role: str, size: int) -> ImageFont.FreeTypeFont:
    """Load the first available font for the given role."""
    for path in _FONT_CANDIDATES.get(role, []):
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    # Last resort: PIL's built-in bitmap font (no size control, but never fails)
    return ImageFont.load_default()  # type: ignore[return-value]


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    if not records:
        raise ValueError(f"No records in {path}")
    return records


def _parse_board(board: str) -> list[list[str]]:
    rows = [r.strip() for r in board.splitlines() if r.strip()]
    return [r.split() for r in rows]


def _find_agent(board: list[list[str]]) -> tuple[int, int] | None:
    for r, row in enumerate(board):
        for c, sym in enumerate(row):
            if sym in ("a", "b"):
                return (r, c)
    return None


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))  # type: ignore


def lerp_color(c1: str, c2: str, t: float) -> tuple[int, int, int]:
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    return (int(r1 + (r2 - r1) * t), int(g1 + (g2 - g1) * t), int(b1 + (b2 - b1) * t))


def _draw_rounded_rect(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    radius: int,
    fill: str | tuple | None = None,
    outline: str | tuple | None = None,
    width: int = 1,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def _draw_wall_cell(draw: ImageDraw.ImageDraw, x: int, y: int, cs: int) -> None:
    # Rich dark wall with subtle bevel
    pad = 1
    draw.rectangle([x+pad, y+pad, x+cs-pad, y+cs-pad], fill=WALL_DARK)
    # Top/left highlight
    draw.line([(x+pad, y+pad), (x+cs-pad, y+pad)], fill=WALL_EDGE, width=1)
    draw.line([(x+pad, y+pad), (x+pad, y+cs-pad)], fill=WALL_EDGE, width=1)
    # Inner cross-hatch pattern for depth
    inner = cs - 6
    ix, iy = x + 3, y + 3
    draw.rectangle([ix, iy, ix+inner, iy+inner], fill=WALL_LIGHT)
    # Small dot in center for texture
    cx2, cy2 = x + cs//2, y + cs//2
    draw.ellipse([cx2-1, cy2-1, cx2+1, cy2+1], fill=WALL_EDGE)


def _draw_ice_cell(draw: ImageDraw.ImageDraw, x: int, y: int, cs: int) -> None:
    pad = 1
    draw.rectangle([x+pad, y+pad, x+cs-pad, y+cs-pad], fill=ICE_DARK)
    # Subtle inner gradient effect via rectangle layers
    inner_pad = 4
    draw.rectangle([x+inner_pad, y+inner_pad, x+cs-inner_pad, y+cs-inner_pad], fill=ICE_INNER)
    # Thin shimmer line on top-left corner
    draw.line([(x+2, y+2), (x+cs//3, y+2)], fill=ICE_SHIMMER, width=1)
    draw.line([(x+2, y+2), (x+2, y+cs//3)], fill=ICE_SHIMMER, width=1)


def _draw_exit_cell(draw: ImageDraw.ImageDraw, x: int, y: int, cs: int) -> None:
    pad = 1
    # Base fill
    draw.rectangle([x+pad, y+pad, x+cs-pad, y+cs-pad], fill=EXIT_DARK)
    # Pulsing inner glow simulation
    inner = 6
    draw.rectangle([x+inner, y+inner, x+cs-inner, y+cs-inner], fill=EXIT_BASE)
    # Diamond/star marker in center
    cx2, cy2 = x + cs//2, y + cs//2
    r = cs//4
    pts = [(cx2, cy2-r), (cx2+r//2, cy2), (cx2, cy2+r), (cx2-r//2, cy2)]
    draw.polygon(pts, fill=EXIT_GLOW)
    # Outer glow ring
    draw.ellipse([cx2-r-2, cy2-r-2, cx2+r+2, cy2+r+2], outline=EXIT_BASE, width=1)


def _draw_agent(draw: ImageDraw.ImageDraw, x: int, y: int, cs: int, on_exit: bool) -> None:
    cx2, cy2 = x + cs//2, y + cs//2
    core = AGENT_WIN if on_exit else AGENT_CORE
    ring = AGENT_WIN_RING if on_exit else AGENT_RING
    glow_col = "#4A1A80" if on_exit else AGENT_GLOW

    # Outer glow
    gr = cs//2 - 2
    draw.ellipse([cx2-gr, cy2-gr, cx2+gr, cy2+gr], fill=glow_col)
    # Middle ring
    mr = int(cs * 0.28)
    draw.ellipse([cx2-mr, cy2-mr, cx2+mr, cy2+mr], fill=core, outline=ring, width=2)
    # Inner dot
    ir = int(cs * 0.10)
    draw.ellipse([cx2-ir, cy2-ir, cx2+ir, cy2+ir], fill=ring)


def _draw_cell(draw: ImageDraw.ImageDraw, x: int, y: int, cs: int, sym: str) -> None:
    if sym == "#":
        _draw_wall_cell(draw, x, y, cs)
    elif sym in ("a", "b"):
        _draw_ice_cell(draw, x, y, cs)
        _draw_agent(draw, x, y, cs, on_exit=(sym == "b"))
    elif sym in ("e",):
        _draw_exit_cell(draw, x, y, cs)
    else:
        _draw_ice_cell(draw, x, y, cs)


def _draw_arrow(
    draw: ImageDraw.ImageDraw,
    action: str,
    agent_rc: tuple[int, int] | None,
    ox: int,
    oy: int,
    cs: int,
    bright: bool,
) -> None:
    if agent_rc is None:
        return
    vectors = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}
    dx, dy = vectors.get(action, (0, 0))
    if dx == 0 and dy == 0:
        return

    ar, ac = agent_rc
    cx2 = ox + ac * cs + cs // 2
    cy2 = oy + ar * cs + cs // 2
    color = ARROW_BRIGHT if bright else ARROW_DIM

    shaft = int(cs * 1.5)
    tip = int(cs * 0.32)
    ex = cx2 + dx * shaft
    ey = cy2 + dy * shaft

    draw.line([(cx2, cy2), (ex, ey)], fill=color, width=5)
    if dx != 0:
        tri = [(ex + dx*tip, ey), (ex - dx*tip, ey - tip), (ex - dx*tip, ey + tip)]
    else:
        tri = [(ex, ey + dy*tip), (ex - tip, ey - dy*tip), (ex + tip, ey - dy*tip)]
    draw.polygon(tri, fill=color)


def _progress_bar(
    draw: ImageDraw.ImageDraw,
    x: int, y: int, w: int, h: int,
    frac: float,
    bar_color: str = TEXT_ACCENT,
    bg_color: str = BADGE_BG,
    radius: int = 4,
) -> None:
    _draw_rounded_rect(draw, (x, y, x+w, y+h), radius, fill=bg_color, outline=BADGE_BORDER, width=1)
    if frac > 0:
        fill_w = max(radius*2, int(w * frac))
        _draw_rounded_rect(draw, (x, y, x+fill_w, y+h), radius, fill=bar_color)


def _build_frame(
    record: dict[str, Any],
    *,
    fw: int,
    fh: int,
    cs: int,
    margin: int,
    top_h: int,
    bot_h: int,
    ox: int,
    oy: int,
    fonts: dict[str, ImageFont.FreeTypeFont],
    action_override: str | None = None,
    show_arrow: bool = False,
    arrow_bright: bool = True,
    phase: str | None = None,
) -> Image.Image:
    obs = record.get("observation", {})
    meta = record.get("metadata", {})

    level     = meta.get("level_index", obs.get("level_index", "?"))
    model     = meta.get("model", "unknown")
    step      = obs.get("step_count", record.get("step_index", 0))
    max_steps = obs.get("max_steps", 20)
    action    = action_override or record.get("chosen_action") or "—"
    done      = obs.get("done", False)
    reward    = obs.get("reward", 0.0)
    message   = obs.get("message") or ""
    thought   = record.get("model_thought") or ""

    board     = _parse_board(obs.get("board", ""))
    agent_rc  = _find_agent(board)

    img = Image.new("RGB", (fw, fh), BG)
    draw = ImageDraw.Draw(img)

    # ── background grid pattern ──────────────────────────────────────────────
    for gx in range(0, fw, 20):
        draw.line([(gx, 0), (gx, fh)], fill="#0B1020", width=1)
    for gy in range(0, fh, 20):
        draw.line([(0, gy), (fw, gy)], fill="#0B1020", width=1)

    # ── top panel ────────────────────────────────────────────────────────────
    draw.rectangle([0, 0, fw, top_h], fill=PANEL_TOP)
    draw.line([(0, top_h), (fw, top_h)], fill=PANEL_BORDER, width=2)

    # Title + model pill
    title_y = 16
    draw.text((margin, title_y), "◈  MAZE REPLAY", fill=TEXT_ACCENT, font=fonts["title"])
    # model badge
    model_str = f"  {model}  "
    mbbox = draw.textbbox((0, 0), model_str, font=fonts["small"])
    mw = mbbox[2] - mbbox[0]
    mh = mbbox[3] - mbbox[1]
    mx = fw - margin - mw - 8
    my = title_y + 2
    _draw_rounded_rect(draw, (mx-4, my-2, mx+mw+4, my+mh+2), 6, fill=BADGE_BG, outline=BADGE_BORDER, width=1)
    draw.text((mx, my), model_str, fill=TEXT_BODY, font=fonts["small"])

    # ── stats row ────────────────────────────────────────────────────────────
    stats_y = title_y + 36
    # Level badge
    _draw_rounded_rect(draw, (margin, stats_y, margin+90, stats_y+26), 5, fill=BADGE_BG, outline=BADGE_BORDER, width=1)
    draw.text((margin+8, stats_y+5), f"LVL {level}", fill=TEXT_HEAD, font=fonts["mono"])

    # Step counter
    _draw_rounded_rect(draw, (margin+100, stats_y, margin+230, stats_y+26), 5, fill=BADGE_BG, outline=BADGE_BORDER, width=1)
    step_color = TEXT_GOLD if step > max_steps * 0.7 else TEXT_BODY
    draw.text((margin+108, stats_y+5), f"STEP  {step:>2} / {max_steps}", fill=step_color, font=fonts["mono"])

    # Reward
    reward_color = TEXT_GREEN if reward > 0 else (TEXT_GOLD if reward < 0 else TEXT_DIM)
    _draw_rounded_rect(draw, (margin+240, stats_y, margin+350, stats_y+26), 5, fill=BADGE_BG, outline=BADGE_BORDER, width=1)
    draw.text((margin+248, stats_y+5), f"RWD  {reward:+.2f}", fill=reward_color, font=fonts["mono"])

    # Done pill
    if done:
        _draw_rounded_rect(draw, (margin+360, stats_y, margin+460, stats_y+26), 5, fill="#1A3A20", outline=EXIT_BASE, width=1)
        draw.text((margin+368, stats_y+5), "● SOLVED!", fill=TEXT_GREEN, font=fonts["mono"])

    # ── action badge (right side) ─────────────────────────────────────────────
    ACTION_ICONS = {"UP": "▲", "DOWN": "▼", "LEFT": "◀", "RIGHT": "▶"}
    icon = ACTION_ICONS.get(action, "·")
    act_label = f"{icon}  {action}"
    abbox = draw.textbbox((0, 0), act_label, font=fonts["mono_lg"])
    aw = abbox[2] - abbox[0]
    ax = fw - margin - aw - 24
    ay = stats_y - 2
    _draw_rounded_rect(draw, (ax-10, ay, ax+aw+14, ay+34), 8, fill="#071A30", outline=ARROW_BRIGHT if show_arrow and arrow_bright else BADGE_BORDER, width=2)
    act_col = ARROW_BRIGHT if show_arrow and arrow_bright else TEXT_BODY
    draw.text((ax, ay+7), act_label, fill=act_col, font=fonts["mono_lg"])

    # ── step progress bar ─────────────────────────────────────────────────────
    pb_y = stats_y + 34
    frac = step / max_steps if max_steps else 0
    bar_col = TEXT_GREEN if done else (TEXT_GOLD if frac > 0.7 else TEXT_ACCENT)
    _progress_bar(draw, margin, pb_y, fw - margin*2, 6, frac, bar_color=bar_col)

    # ── model thought bubble ──────────────────────────────────────────────────
    # The thought panel occupies the space between pb_y and oy (board origin).
    # We measure the available height so text never bleeds into the board.
    thought_area_h = oy - pb_y - 8   # pixels available below progress bar
    if thought and thought_area_h > 30:
        max_chars = max(20, (fw - margin * 2 - 100) // 7)
        words = thought.split()
        lines: list[str] = []
        cur = ""
        for word in words:
            test = (cur + " " + word).strip()
            if len(test) <= max_chars:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        line_h = 16
        max_lines = max(1, (thought_area_h - 20) // line_h)
        lines = lines[:max_lines]
        panel_h = min(thought_area_h - 4, len(lines) * line_h + 18)
        ty = pb_y + 6
        _draw_rounded_rect(draw, (margin, ty, fw - margin, ty + panel_h),
                           6, fill="#060F1E", outline="#1A2E50", width=1)
        draw.text((margin + 10, ty + 5), "THOUGHT:", fill="#3A6080", font=fonts["small"])
        lw = draw.textbbox((0, 0), "THOUGHT:", font=fonts["small"])[2] + 14
        for i, line in enumerate(lines):
            lx = margin + 10 + lw if i == 0 else margin + 10
            ly = ty + 5 + i * line_h
            if ly + line_h <= ty + panel_h:   # clip to panel
                draw.text((lx, ly), line, fill="#5A8EB8", font=fonts["small"])

    # ── message ───────────────────────────────────────────────────────────────
    if message:
        msg_y = oy - 18   # pin message just above the board
        draw.text((margin, msg_y), f"  {message[:100]}", fill=TEXT_DIM, font=fonts["small"])

    # ── board cells ──────────────────────────────────────────────────────────
    rows_n = len(board)
    cols_n = len(board[0]) if board else 0
    # board background with border
    bpad = 4
    _draw_rounded_rect(
        draw,
        (ox - bpad, oy - bpad, ox + cols_n*cs + bpad, oy + rows_n*cs + bpad),
        6,
        fill=GRID_LINE,
        outline=PANEL_BORDER,
        width=2,
    )
    for r, row in enumerate(board):
        for c, sym in enumerate(row):
            _draw_cell(draw, ox + c*cs, oy + r*cs, cs, sym)

    # Arrow overlay
    if show_arrow:
        _draw_arrow(draw, action, agent_rc, ox, oy, cs, arrow_bright)

    # ── bottom legend ─────────────────────────────────────────────────────────
    leg_y = fh - bot_h + 10
    draw.line([(0, fh - bot_h), (fw, fh - bot_h)], fill=PANEL_BORDER, width=1)
    legend_items = [
        ("■", WALL_LIGHT, "wall"),
        ("■", ICE_LIGHT, "ice"),
        ("◆", EXIT_GLOW, "exit"),
        ("●", AGENT_CORE, "agent"),
        ("●", AGENT_WIN, "on exit"),
    ]
    lx = margin
    for icon_sym, col, label in legend_items:
        draw.text((lx, leg_y), icon_sym, fill=col, font=fonts["small"])
        draw.text((lx + 14, leg_y), label, fill=TEXT_DIM, font=fonts["small"])
        lx += 80

    if phase:
        pbbox = draw.textbbox((0, 0), phase, font=fonts["small"])
        pw = pbbox[2] - pbbox[0]
        draw.text((fw - margin - pw, leg_y), phase, fill=TEXT_DIM, font=fonts["small"])

    return img


def render_rollout_gif(
    input_jsonl: Path,
    output_gif: Path,
    *,
    frame_duration_ms: int = 700,
    cell_size: int = 48,
    level_index: int | None = None,
) -> None:
    records = _load_jsonl(input_jsonl)
    if level_index is not None:
        records = [
            r for r in records
            if r.get("metadata", {}).get("level_index") == level_index
            or r.get("observation", {}).get("level_index") == level_index
        ]
        if not records:
            raise ValueError(f"No records found for level_index={level_index}")
    first_board = _parse_board(records[0].get("observation", {}).get("board", ""))
    if not first_board:
        raise ValueError("Empty board in first record.")

    rows_n = len(first_board)
    cols_n = len(first_board[0])

    margin   = 28
    bot_h    = 38
    board_w  = cols_n * cell_size
    board_h  = rows_n * cell_size
    fw       = board_w + margin * 2

    # Measure worst-case thought panel height across all records so every
    # frame has the same dimensions (GIF requires uniform frame size).
    BASE_TOP_H   = 155   # title + stats + progress bar + message
    THOUGHT_LINE_H = 16
    THOUGHT_MAX_LINES = 3
    THOUGHT_PADDING   = 18  # top/bottom padding inside the thought box
    THOUGHT_MARGIN    = 10  # gap above thought box

    has_any_thought = any(r.get("model_thought") for r in records)
    thought_panel_h = (THOUGHT_MAX_LINES * THOUGHT_LINE_H + THOUGHT_PADDING + THOUGHT_MARGIN) if has_any_thought else 0
    top_h    = BASE_TOP_H + thought_panel_h
    fh       = top_h + board_h + bot_h + 10
    ox       = margin
    oy       = top_h

    fonts = {
        "title":   _lf("bold",      18),
        "mono":    _lf("mono_bold", 13),
        "mono_lg": _lf("mono_bold", 15),
        "small":   _lf("mono",      12),
        "body":    _lf("regular",   13),
    }

    common = dict(fw=fw, fh=fh, cs=cell_size, margin=margin, top_h=top_h,
                  bot_h=bot_h, ox=ox, oy=oy, fonts=fonts)

    frames: list[Image.Image] = []
    durations: list[int] = []

    # Frame 0: initial state
    frames.append(_build_frame(records[0], **common, phase="Initial state"))
    durations.append(frame_duration_ms)

    for i in range(1, len(records)):
        prev   = records[i - 1]
        curr   = records[i]
        action = curr.get("chosen_action") or "RESET"

        # Flash 1 — bright arrow
        frames.append(_build_frame(prev, **common,
                                   action_override=action,
                                   show_arrow=True, arrow_bright=True,
                                   phase="Model chose action"))
        durations.append(max(160, frame_duration_ms // 3))

        # Flash 2 — dim arrow (blink)
        frames.append(_build_frame(prev, **common,
                                   action_override=action,
                                   show_arrow=True, arrow_bright=False,
                                   phase="Model chose action"))
        durations.append(max(120, frame_duration_ms // 4))

        # Result frame
        frames.append(_build_frame(curr, **common,
                                   action_override=action,
                                   show_arrow=False,
                                   phase="After move"))
        durations.append(frame_duration_ms)

    output_gif.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        output_gif,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        disposal=2,
        optimize=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",  default="rollout_observations.jsonl")
    parser.add_argument("--output", default="rollout.gif")
    parser.add_argument("--frame-duration-ms", type=int, default=700)
    parser.add_argument("--cell-size", type=int, default=48)
    parser.add_argument("--level-index", type=int, default=None,
                        help="Only render records for this level index.")
    args = parser.parse_args()
    render_rollout_gif(
        Path(args.input), Path(args.output),
        frame_duration_ms=args.frame_duration_ms,
        cell_size=args.cell_size,
        level_index=args.level_index,
    )
    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()