from __future__ import annotations

import subprocess
import sys
import tomllib
from importlib import resources
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _pyproject() -> dict:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_pyproject_metadata_matches_public_release_gate() -> None:
    project = _pyproject()["project"]

    assert project["name"] == "phantom-tutor"
    assert project["version"] == "0.1.0a0"
    assert project["license"] == "Apache-2.0"
    assert project["requires-python"] == ">=3.11"
    assert project["authors"]
    assert "Topic :: Education" in project["classifiers"]
    assert "Homepage" in project["urls"]
    assert "Repository" in project["urls"]
    assert "fsrs>=6.3.1,<7" in project["dependencies"]


def test_console_entrypoint_is_declared() -> None:
    scripts = _pyproject()["project"]["scripts"]

    assert scripts["tutor"] == "phantom_tutor.cli:main"


def test_seed_content_is_packaged() -> None:
    package_data = _pyproject()["tool"]["setuptools"]["package-data"]

    assert package_data["content.knowledge"] == ["*.json"]
    assert package_data["content.coding"] == ["*.json"]
    assert package_data["content.design"] == ["*.json"]
    assert resources.files("content.knowledge").joinpath("seed.json").is_file()
    assert resources.files("content.coding").joinpath("seed.json").is_file()
    assert resources.files("content.design").joinpath("seed.json").is_file()


def test_module_help_is_available_without_network() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "phantom_tutor.cli", "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "demo-loop" in result.stdout
