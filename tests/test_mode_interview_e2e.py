from phantom_tutor.cli import main
from phantom_tutor import memory


def test_interview_asks_grades_and_records(capsys):
    # seed a weak spot so the interviewer has context to focus on
    memory.record_attempt("rag", "LLM", score=0.2, now_iso="2026-06-10", topic="rag")
    rc = main(["interview", "--focus", "LLM", "--answer", "RAG retrieves docs and grounds the answer"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Q:" in out and "score=" in out      # asked a question + graded the answer
    assert memory.load_store()["interview:LLM"]["attempts"] >= 1
