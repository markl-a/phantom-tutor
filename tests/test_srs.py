from phantom_tutor import srs


def test_next_interval_grows_on_pass_and_resets_on_fail():
    # score >= 0.6 grows the interval; below resets to 1 day
    assert srs.next_interval_days(prev_interval=1, score=1.0) > 1
    assert srs.next_interval_days(prev_interval=10, score=0.9) > 10
    assert srs.next_interval_days(prev_interval=10, score=0.3) == 1
    assert srs.next_interval_days(prev_interval=0, score=1.0) >= 1


def test_is_due():
    assert srs.is_due("2026-06-10", "2026-06-12") is True   # past due
    assert srs.is_due("2026-06-12", "2026-06-12") is True   # due today
    assert srs.is_due("2026-06-20", "2026-06-12") is False  # future
