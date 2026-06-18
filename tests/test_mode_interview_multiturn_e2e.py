"""Phase-2 slice 3: multi-turn interview. `tutor interview --turns N` runs N
ask->answer->follow-up rounds (the LLM, stubbed, asks a follow-up each round
reading weak_spots), grades the session, records to weak_spots. Without --turns
(or --turns 1) behavior matches the Phase-1 single-turn e2e (kept passing)."""
from phantom_tutor.cli import main
from phantom_tutor import memory


def test_interview_multiturn_asks_n_questions_and_records_session(capsys):
    memory.record_attempt("rag", "LLM", score=0.2, now_iso="2026-06-10", topic="rag")
    rc = main(["interview", "--focus", "LLM", "--turns", "3",
               "--answer", "RAG retrieves docs and grounds the answer"])
    assert rc == 0
    out = capsys.readouterr().out
    # N questions asked across the session (Q1..Q3 each shown)
    assert out.count("Q") >= 3
    assert "Q1" in out and "Q3" in out
    assert "score=" in out
    # a single session record landed in weak_spots
    store = memory.load_store()
    assert store["interview:LLM"]["attempts"] >= 1


def test_interview_single_turn_default_unchanged(capsys):
    """No --turns => Phase-1 single-turn shape (Q: ... score= ... FEEDBACK: ...)."""
    memory.record_attempt("rag", "LLM", score=0.2, now_iso="2026-06-10", topic="rag")
    rc = main(["interview", "--focus", "LLM", "--answer", "RAG grounds answers"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.startswith("Q:")  # exact Phase-1 single-turn header
    assert "score=" in out and "FEEDBACK" in out.upper()
    assert "Q1" not in out  # single-turn does not number rounds
    assert memory.load_store()["interview:LLM"]["attempts"] >= 1
