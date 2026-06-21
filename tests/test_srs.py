from datetime import date

from fsrs import Rating

from phantom_tutor import srs


def test_score_to_rating_maps_bands():
    assert srs.score_to_rating(0.5) == Rating.Again
    assert srs.score_to_rating(0.6) == Rating.Hard
    assert srs.score_to_rating(0.7) == Rating.Hard
    assert srs.score_to_rating(0.8) == Rating.Good
    assert srs.score_to_rating(0.95) == Rating.Easy


def test_review_first_pass_is_day_level_and_future():
    card, due = srs.review(None, 1.0, "2026-06-10")
    assert due > "2026-06-10"               # scheduled into the future
    assert len(due) == 10                    # day-level YYYY-MM-DD, not a datetime
    assert isinstance(card, dict) and "stability" in card   # FSRS card state stored


def test_review_fail_schedules_one_day_out():
    _, due = srs.review(None, 0.2, "2026-06-10")
    assert due == "2026-06-11"


def test_review_interval_grows_on_repeated_pass():
    card1, due1 = srs.review(None, 1.0, "2026-06-10")
    _, due2 = srs.review(card1, 1.0, due1)
    i1 = (date.fromisoformat(due1) - date(2026, 6, 10)).days
    i2 = (date.fromisoformat(due2) - date.fromisoformat(due1)).days
    assert i2 > i1                           # stability grows -> longer interval


def test_review_is_deterministic():
    # full card dict + due are reproducible (deterministic card_id, no fuzzing)
    assert srs.review(None, 1.0, "2026-06-10") == srs.review(None, 1.0, "2026-06-10")


def test_is_due():
    assert srs.is_due("2026-06-10", "2026-06-12") is True   # past due
    assert srs.is_due("2026-06-12", "2026-06-12") is True   # due today
    assert srs.is_due("2026-06-20", "2026-06-12") is False  # future
