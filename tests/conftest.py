import pytest


@pytest.fixture(autouse=True)
def isolated_tutor_home(tmp_path, monkeypatch):
    """Every test gets its own tutor home + stubbed LLM — never the real ~/.phantom-mesh."""
    monkeypatch.setenv("PHANTOM_TUTOR_HOME", str(tmp_path / "tutor"))
    monkeypatch.delenv("PHANTOM_HOME", raising=False)
    monkeypatch.setenv("PHANTOM_TUTOR_STUB_LLM", "1")
    return tmp_path
