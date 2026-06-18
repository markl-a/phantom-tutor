import os
from pathlib import Path
from phantom_tutor import paths


def test_data_root_honors_tutor_home(tmp_path, monkeypatch):
    monkeypatch.setenv("PHANTOM_TUTOR_HOME", str(tmp_path / "t"))
    root = paths.data_root()
    assert root == tmp_path / "t"
    assert root.is_dir()  # created


def test_data_root_falls_back_to_phantom_home(tmp_path, monkeypatch):
    monkeypatch.delenv("PHANTOM_TUTOR_HOME", raising=False)
    monkeypatch.setenv("PHANTOM_HOME", str(tmp_path / "ph"))
    assert paths.data_root() == tmp_path / "ph" / "tutor"
