from __future__ import annotations

import json
from pathlib import Path

from phantom_tutor.cli import main


def test_demo_loop_cli_writes_synthetic_career_learning_artifacts(
    tmp_path: Path,
    capsys,
) -> None:
    out = tmp_path / "bundle"

    rc = main(
        [
            "demo-loop",
            "--out",
            str(out),
            "--now",
            "2026-06-26",
        ]
    )

    assert rc == 0
    manifest_path = Path(capsys.readouterr().out.strip())
    assert manifest_path == out / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["schema_version"] == 1
    assert manifest["mode"] == "synthetic_career_learning_loop"
    assert manifest["now"] == "2026-06-26"
    assert manifest["data_policy"] == "synthetic_only"
    assert manifest["private_data_included"] is False
    assert manifest["external_network"] is False
    assert manifest["llm_provider"] == "stub_or_disabled"
    assert manifest["anti_cheating_boundary"] == "practice_only_no_live_interview_assistance"

    expected = {
        "source_jobs",
        "source_profile",
        "jobs",
        "profile",
        "gap_report",
        "review_result",
        "weak_spots",
        "attempts",
        "summary",
    }
    assert set(manifest["artifacts"]) == expected
    for rel in manifest["artifacts"].values():
        assert (out / rel).exists()

    weak = json.loads((out / manifest["artifacts"]["weak_spots"]).read_text(encoding="utf-8"))
    assert "mlops" in weak
    assert "rag" in weak
    assert weak["softmax"]["attempts"] == 1
    assert weak["softmax"]["mastery"] == 0.0

    summary = (out / manifest["artifacts"]["summary"]).read_text(encoding="utf-8")
    assert "Synthetic career learning loop" in summary
    assert "job gap" in summary.lower()
    assert "practice review" in summary.lower()
    forbidden = ("resume", "real interview", "live interview", "application submission")
    assert all(term not in summary.lower() for term in forbidden)


def test_demo_loop_is_byte_stable_for_same_inputs(tmp_path: Path, capsys) -> None:
    a = tmp_path / "a"
    b = tmp_path / "b"

    assert main(["demo-loop", "--out", str(a), "--now", "2026-06-26"]) == 0
    capsys.readouterr()
    assert main(["demo-loop", "--out", str(b), "--now", "2026-06-26"]) == 0
    capsys.readouterr()

    rels = (
        "manifest.json",
        "artifacts/source-jobs.json",
        "artifacts/source-operator-skills.json",
        "artifacts/jobs.json",
        "artifacts/operator_skills.json",
        "artifacts/gap-report.json",
        "artifacts/review-result.json",
        "artifacts/weak_spots.json",
        "artifacts/attempts.jsonl",
        "artifacts/summary.md",
    )
    for rel in rels:
        assert (a / rel).read_text(encoding="utf-8") == (b / rel).read_text(
            encoding="utf-8"
        )


def test_demo_loop_is_idempotent_when_reusing_output_directory(
    tmp_path: Path,
    capsys,
) -> None:
    out = tmp_path / "bundle"

    assert main(["demo-loop", "--out", str(out), "--now", "2026-06-26"]) == 0
    capsys.readouterr()
    first_attempts = (out / "artifacts" / "attempts.jsonl").read_text(encoding="utf-8")
    first_weak_spots = (out / "artifacts" / "weak_spots.json").read_text(encoding="utf-8")
    first_manifest = (out / "manifest.json").read_text(encoding="utf-8")

    assert main(["demo-loop", "--out", str(out), "--now", "2026-06-26"]) == 0
    capsys.readouterr()

    assert (out / "artifacts" / "attempts.jsonl").read_text(encoding="utf-8") == first_attempts
    assert (out / "artifacts" / "weak_spots.json").read_text(encoding="utf-8") == first_weak_spots
    assert (out / "manifest.json").read_text(encoding="utf-8") == first_manifest
    weak = json.loads(first_weak_spots)
    assert weak["softmax"]["attempts"] == 1
