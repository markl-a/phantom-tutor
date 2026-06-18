from phantom_tutor import memory


def test_record_attempt_persists_and_updates_mastery_and_due():
    rec = memory.record_attempt("transformer", "ML", score=0.4, now_iso="2026-06-12")
    assert rec["topic"] == "transformer"
    assert rec["dimension"] == "ML"
    assert rec["attempts"] == 1
    assert rec["due"] == "2026-06-13"   # fail -> 1 day later
    # a pass grows the interval and raises mastery
    rec2 = memory.record_attempt("transformer", "ML", score=1.0, now_iso="2026-06-13")
    assert rec2["attempts"] == 2
    assert rec2["mastery"] > rec["mastery"]
    assert rec2["due"] > "2026-06-14"   # interval grew


def test_due_topics_and_list_weak():
    memory.record_attempt("a", "ML", score=0.2, now_iso="2026-06-10")   # weak, due 06-11
    memory.record_attempt("b", "ML", score=1.0, now_iso="2026-06-10")   # strong, due later
    due = memory.due_topics(now_iso="2026-06-12")
    assert "a" in [d["key"] for d in due]
    assert "b" not in [d["key"] for d in due]   # not yet due
    weak = memory.list_weak(n=1)
    assert weak[0]["key"] == "a"   # weakest first
