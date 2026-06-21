"""Data-root resolution. NEVER hardcode ~/.phantom-mesh in callers — go through here."""
from __future__ import annotations

import os
from pathlib import Path


def data_root() -> Path:
    """The tutor data dir. Honors PHANTOM_TUTOR_HOME, else PHANTOM_HOME/tutor,
    else ~/.phantom-mesh/tutor. Created if absent."""
    if os.environ.get("PHANTOM_TUTOR_HOME"):
        p = Path(os.environ["PHANTOM_TUTOR_HOME"])
    elif os.environ.get("PHANTOM_HOME"):
        p = Path(os.environ["PHANTOM_HOME"]) / "tutor"
    else:
        p = Path.home() / ".phantom-mesh" / "tutor"
    p.mkdir(parents=True, exist_ok=True)
    return p


def weak_spots_path() -> Path:
    return data_root() / "weak_spots.json"


def attempts_path() -> Path:
    return data_root() / "attempts.jsonl"


def jobs_path() -> Path:
    return data_root() / "jobs.json"


def operator_profile_path() -> Path:
    return data_root() / "operator_skills.json"
