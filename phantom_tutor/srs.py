"""Spaced-repetition scheduling via FSRS (open-spaced-repetition/fsrs). Day-level
(learning_steps disabled) to fit the date-granularity daily loop; fuzzing off so
scheduling is deterministic and tests stay hermetic. A 0-1 score maps to an FSRS
Rating; the FSRS card state lives in the weak_spot record."""
from __future__ import annotations

from datetime import date, datetime, timezone

from fsrs import Card, Rating, Scheduler

PASS_THRESHOLD = 0.6  # score >= this counts as a streak pass (used by memory)

_scheduler = Scheduler(learning_steps=(), relearning_steps=(), enable_fuzzing=False)


def score_to_rating(score: float) -> Rating:
    """Map a 0-1 grade to an FSRS rating."""
    if score < 0.6:
        return Rating.Again
    if score < 0.75:
        return Rating.Hard
    if score < 0.9:
        return Rating.Good
    return Rating.Easy


def review(card: dict | None, score: float, now_iso: str) -> tuple[dict, str]:
    """Apply one graded review to an FSRS card (or a fresh one). Returns the
    updated card dict (for storage) and the next due date as YYYY-MM-DD. A None
    card seeds a fresh one — smoothly upgrading legacy SM-2 records on next review."""
    # Deterministic card_id (date-derived) so stored card state is reproducible and
    # we skip fsrs.Card()'s wall-clock id + its per-card sleep. card_id is unused by
    # the scheduler and we key cards by topic, so same-day collisions are harmless.
    c = Card.from_dict(card) if card else Card(card_id=int(now_iso.replace("-", "")))
    when = datetime.fromisoformat(now_iso).replace(tzinfo=timezone.utc)
    c, _ = _scheduler.review_card(c, score_to_rating(score), review_datetime=when)
    return c.to_dict(), c.due.date().isoformat()


def is_due(due_iso: str, now_iso: str) -> bool:
    """True if due_iso (YYYY-MM-DD) is on or before now_iso."""
    return date.fromisoformat(due_iso) <= date.fromisoformat(now_iso)
