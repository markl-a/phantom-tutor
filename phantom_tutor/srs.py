"""Pure spaced-repetition scheduling (SM-2-lite). No I/O."""
from __future__ import annotations

from datetime import date

PASS_THRESHOLD = 0.6
EASE = 2.0


def next_interval_days(prev_interval: int, score: float) -> int:
    """New review interval in days. Pass (score>=0.6) multiplies the interval
    (min 1 day); fail resets to 1 day."""
    if score < PASS_THRESHOLD:
        return 1
    base = max(prev_interval, 1)
    return max(1, round(base * EASE))


def is_due(due_iso: str, now_iso: str) -> bool:
    """True if due_iso (YYYY-MM-DD) is on or before now_iso."""
    return date.fromisoformat(due_iso) <= date.fromisoformat(now_iso)
