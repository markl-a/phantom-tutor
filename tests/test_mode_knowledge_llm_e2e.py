"""Phase-2 slice 2: `tutor quiz --llm` grades a free-text answer through the
LLM (stubbed) instead of keyword overlap, and records the LLM score to weak_spots.
The keyword path (no --llm) must stay byte-unchanged (covered by the Phase-1 e2e)."""
from phantom_tutor.cli import main
from phantom_tutor import memory


def test_quiz_llm_grades_freetext_and_records(capsys):
    # An answer with ZERO keyword overlap would score 0 under keyword grading,
    # but the stub LLM grader returns a deterministic positive score from the
    # prompt length -> proves the LLM path (not keyword) was taken.
    rc = main(["quiz", "--id", "k-softmax", "--llm",
               "--answer", "completely off-topic prose with none of the magic terms present here"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "softmax" in out.lower()
    store = memory.load_store()
    assert "softmax" in store and store["softmax"]["attempts"] == 1
    # stub GRADE returns a positive score for this (long) answer; keyword would be 0
    assert store["softmax"]["mastery"] > 0.0


def test_quiz_llm_score_differs_from_keyword(capsys):
    """Same off-topic answer: keyword grade == 0, LLM grade > 0 -> the flag changes the path."""
    # keyword path
    main(["quiz", "--id", "k-softmax",
          "--answer", "off-topic prose with none of the magic terms present here at all really"])
    kw_mastery = memory.load_store()["softmax"]["mastery"]
    assert kw_mastery == 0.0  # no keyword hit

    # llm path on a fresh topic so the EMA does not carry over
    main(["quiz", "--id", "k-rag", "--llm",
          "--answer", "off-topic prose with none of the magic terms present here at all really"])
    llm_mastery = memory.load_store()["rag"]["mastery"]
    assert llm_mastery > 0.0  # LLM stub gave it credit
