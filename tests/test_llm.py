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


def _capture_argv(monkeypatch):
    """Patch subprocess.run inside llm to capture argv, and disable stub mode."""
    captured = {}

    class _Result:
        stdout = "ok"

    def fake_run(cmd, *args, **kwargs):
        captured["cmd"] = cmd
        return _Result()

    monkeypatch.delenv("PHANTOM_TUTOR_STUB_LLM", raising=False)
    monkeypatch.setattr(llm.subprocess, "run", fake_run)
    return captured


def test_provider_passthrough_inserts_flag_when_env_set(monkeypatch):
    captured = _capture_argv(monkeypatch)
    monkeypatch.setenv("PHANTOM_PROVIDER", "hermes")
    llm.complete("hello", system="sys")
    cmd = captured["cmd"]
    # --provider <val> appears right after "exec" and before the prompt
    assert cmd[:4] == ["phantom", "exec", "--provider", "hermes"]
    assert "hello" in cmd
    assert "--provider" in cmd and cmd[cmd.index("--provider") + 1] == "hermes"


def test_no_provider_flag_when_env_unset(monkeypatch):
    captured = _capture_argv(monkeypatch)
    monkeypatch.delenv("PHANTOM_PROVIDER", raising=False)
    llm.complete("hello", system="sys")
    cmd = captured["cmd"]
    assert "--provider" not in cmd
    # byte-for-byte unchanged default behavior
    assert cmd == ["phantom", "exec", "hello", "--system", "sys"]


def test_no_provider_flag_when_env_empty(monkeypatch):
    captured = _capture_argv(monkeypatch)
    monkeypatch.setenv("PHANTOM_PROVIDER", "")
    llm.complete("hello")
    cmd = captured["cmd"]
    assert "--provider" not in cmd
    assert cmd == ["phantom", "exec", "hello"]
