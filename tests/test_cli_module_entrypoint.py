from __future__ import annotations

import subprocess
import sys


def test_python_m_phantom_tutor_cli_shows_help():
    proc = subprocess.run(
        [sys.executable, "-m", "phantom_tutor.cli", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0
    assert "usage: tutor" in proc.stdout
    assert "weak-spots" in proc.stdout
