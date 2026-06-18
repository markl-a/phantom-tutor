from phantom_tutor import llm


def test_stub_is_deterministic_and_parseable():
    # In stub mode the grader prompt yields a deterministic SCORE/FEEDBACK block.
    out = llm.complete("Grade this answer.\n[[GRADE]]", system="grader")
    assert "SCORE:" in out
    score, feedback = llm.parse_grade(out)
    assert 0.0 <= score <= 1.0
    assert isinstance(feedback, str) and feedback


def test_stub_interview_question_marker():
    out = llm.complete("Ask an interview question about RAG.\n[[ASK]]")
    assert out.strip()  # non-empty deterministic question
