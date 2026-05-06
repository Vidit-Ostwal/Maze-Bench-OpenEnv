"""Structured step rewards for the Ice Maze environment."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Direction pairs (must match MazeAction / MazeDirection string values)
# ---------------------------------------------------------------------------

OPPOSITE_DIRECTION: Dict[str, str] = {
    "UP": "DOWN",
    "DOWN": "UP",
    "LEFT": "RIGHT",
    "RIGHT": "LEFT",
}

REWARD_SOLVED: float = 10.0
PENALTY_REPEATED_ACTION: float = -1.0
PENALTY_OPPOSITE_ACTION: float = -1.0
# Revisiting a full-board configuration: -1.0 for each *prior* time this state
# was already recorded in the episode (0 on first time seeing this state).
PENALTY_PER_PRIOR_STATE_VISIT: float = 1.0
# When returning to a configuration seen before, also penalize time since the last
# time the episode was in that state: ``-PENALTY_PER_WASTED_STEP * min(gap, cap)``,
# where ``gap = current step index − last step index in this state`` (capped).
PENALTY_PER_WASTED_STEP: float = 0.1
WASTED_STEPS_REVISIT_CAP: int = 50


def board_fingerprint(grid: List[List[str]]) -> Tuple[str, ...]:
    """
    Stable fingerprint of the full board grid (walls, ice, all players, exits).

    Used as a key to track how often each global configuration has been visited.
    """
    return tuple("".join(row) for row in grid)


def reward_terminal_solve(
    *, done: bool, step_count: int
) -> Optional[Tuple[float, str, Dict[str, float]]]:
    """
    If the step ends the episode successfully, return (reward, message, breakdown).

    Otherwise return ``None`` so the caller can apply non-terminal shaping.
    """
    if not done:
        return None
    message = (
        f"Solved! All players on exits in {step_count} step(s). "
        f"Reward: +{REWARD_SOLVED:g}."
    )
    breakdown = {
        "total": REWARD_SOLVED,
        "solved_bonus": REWARD_SOLVED,
        "repeated_action_penalty": 0.0,
        "opposite_action_penalty": 0.0,
        "revisit_count_penalty": 0.0,
        "revisit_waste_penalty": 0.0,
        "revisit_state_penalty": 0.0,
    }
    return REWARD_SOLVED, message, breakdown


def penalty_repeated_direction(
    *, direction: str, previous_direction: Optional[str]
) -> Tuple[float, Optional[str]]:
    """Same direction as the previous action (ice already slid as far as possible)."""
    if previous_direction is None or direction != previous_direction:
        return 0.0, None
    return PENALTY_REPEATED_ACTION, "same direction as last step (repeat)"


def penalty_opposite_direction(
    *, direction: str, previous_direction: Optional[str]
) -> Tuple[float, Optional[str]]:
    """Current direction is opposite the previous (UP↔DOWN, LEFT↔RIGHT)."""
    if (
        previous_direction is None
        or OPPOSITE_DIRECTION.get(direction) != previous_direction
    ):
        return 0.0, None
    return PENALTY_OPPOSITE_ACTION, "opposite of last step (reversal)"


def penalty_revisit_count(
    *, state_visit_count_before: int
) -> Tuple[float, Optional[str]]:
    """Per prior visit to this full-board fingerprint this episode."""
    if state_visit_count_before <= 0:
        return 0.0, None
    value = -PENALTY_PER_PRIOR_STATE_VISIT * float(state_visit_count_before)
    detail = (
        "revisited a board state seen "
        f"{state_visit_count_before} time(s) before in this episode"
    )
    return value, detail


def penalty_revisit_waste(
    *, state_visit_count_before: int, waste_step_gap: int
) -> Tuple[float, Optional[str]]:
    """
    Penalize the gap in episode steps since we last *ended* a turn in this layout.

    Only applies on revisits; uses ``PENALTY_PER_WASTED_STEP`` and
    ``WASTED_STEPS_REVISIT_CAP``.
    """
    if state_visit_count_before <= 0:
        return 0.0, None
    gap = max(0, waste_step_gap)
    eff_gap = min(gap, WASTED_STEPS_REVISIT_CAP)
    if eff_gap <= 0:
        return 0.0, None
    value = -PENALTY_PER_WASTED_STEP * float(eff_gap)
    cap_note = (
        f" (capped at {WASTED_STEPS_REVISIT_CAP})"
        if gap > WASTED_STEPS_REVISIT_CAP
        else ""
    )
    detail = f"{eff_gap} step(s) since last in this state{cap_note}"
    return value, detail


def compute_maze_step_reward(
    *,
    done: bool,
    direction: str,
    previous_direction: Optional[str],
    state_visit_count_before: int,
    waste_step_gap: int,
    step_count: int,
) -> Tuple[float, str, Dict[str, float]]:
    """
    Compute step reward and a human-readable message by summing components.

    On the terminal (solved) step, only the +10 term applies so the success signal
    stays clear; intermediate shaping penalties are not subtracted on that step.
    """
    terminal = reward_terminal_solve(done=done, step_count=step_count)
    if terminal is not None:
        return terminal

    repeated, rep_detail = penalty_repeated_direction(
        direction=direction, previous_direction=previous_direction
    )
    opposite, opp_detail = penalty_opposite_direction(
        direction=direction, previous_direction=previous_direction
    )
    revisit_count, count_detail = penalty_revisit_count(
        state_visit_count_before=state_visit_count_before
    )
    revisit_waste, waste_detail = penalty_revisit_waste(
        state_visit_count_before=state_visit_count_before,
        waste_step_gap=waste_step_gap,
    )

    total = repeated + opposite + revisit_count + revisit_waste
    parts = [
        d for d in (rep_detail, opp_detail, count_detail, waste_detail) if d is not None
    ]
    if parts:
        detail = "; ".join(parts)
        message = f"Step {step_count}, moved {direction}. {detail}. Reward: {total:g}."
    else:
        message = (
            f"Step {step_count}, moved {direction}. "
            f"No shaping penalties. Reward: {total:g}."
        )

    revisit_state = revisit_count + revisit_waste
    breakdown = {
        "total": total,
        "solved_bonus": 0.0,
        "repeated_action_penalty": repeated,
        "opposite_action_penalty": opposite,
        "revisit_count_penalty": revisit_count,
        "revisit_waste_penalty": revisit_waste,
        "revisit_state_penalty": revisit_state,
    }
    return total, message, breakdown
