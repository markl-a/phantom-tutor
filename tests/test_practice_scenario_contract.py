from __future__ import annotations

import json
from pathlib import Path

from phantom_tutor.cli import main


def test_practice_scenario_writes_weak_spot_to_practice_bundle(
    tmp_path: Path,
    capsys,
) -> None:
    source = tmp_path / "career-loop"
    out = tmp_path / "practice-scenario"

    assert main(["demo-loop", "--out", str(source), "--now", "2026-06-26"]) == 0
    capsys.readouterr()

    assert main(["practice-scenario", "--source", str(source), "--out", str(out)]) == 0
    manifest_path = Path(capsys.readouterr().out.strip())
    assert manifest_path == out / "manifest.json"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    scenario = json.loads((out / "practice-scenario.json").read_text(encoding="utf-8"))
    evidence = json.loads((out / "practice-evidence.json").read_text(encoding="utf-8"))
    summary = (out / "summary.md").read_text(encoding="utf-8")

    assert manifest["schema_version"] == 1
    assert manifest["mode"] == "synthetic_practice_scenario_bundle"
    assert manifest["source_mode"] == "synthetic_career_learning_loop"
    assert manifest["data_policy"] == "synthetic_only"
    assert manifest["private_data_included"] is False
    assert manifest["external_network"] is False
    assert manifest["llm_provider"] == "stub_or_disabled"
    assert manifest["anti_cheating_boundary"] == "practice_only_no_live_interview_assistance"
    assert manifest["artifacts"] == {
        "evidence": "practice-evidence.json",
        "scenario": "practice-scenario.json",
        "summary": "summary.md",
    }

    assert scenario["mode"] == "synthetic_weak_spot_to_practice_scenario"
    assert scenario["selected_weak_spot"]["topic"] == "governance"
    assert scenario["selected_weak_spot"]["source"] == "synthetic_job_gap"
    assert scenario["practice"]["mode"] == "design"
    assert scenario["practice"]["score"] == 0.72
    assert scenario["practice"]["raw_answer_included"] is False
    assert scenario["practice"]["full_prompt_included"] is False
    assert scenario["srs_update"]["attempts_before"] == 0
    assert scenario["srs_update"]["attempts_after"] == 1
    assert scenario["srs_update"]["mastery_after"] > scenario["srs_update"]["mastery_before"]
    assert scenario["readiness"]["weak_spot_selected"] is True
    assert scenario["readiness"]["practice_completed"] is True
    assert scenario["readiness"]["evidence_recorded"] is True
    assert scenario["readiness"]["next_review_scheduled"] is True
    assert scenario["boundaries"]["covert_live_interview_assistance"] == "not_supported"
    assert scenario["boundaries"]["job_board_scraping"] == "not_supported"
    assert scenario["boundaries"]["application_submission"] == "not_supported"

    assert evidence["mode"] == "synthetic_practice_evidence"
    assert evidence["items"][0]["kind"] == "weak_spot_selection"
    assert evidence["items"][1]["kind"] == "practice_result"
    assert evidence["items"][1]["raw_answer_included"] is False
    assert evidence["items"][2]["kind"] == "srs_update"

    assert "Weak spot to practice scenario" in summary
    assert "governance" in summary


def test_practice_scenario_is_byte_stable_and_excludes_private_payloads(
    tmp_path: Path,
    capsys,
) -> None:
    source = tmp_path / "career-loop"
    a = tmp_path / "a"
    b = tmp_path / "b"

    assert main(["demo-loop", "--out", str(source), "--now", "2026-06-26"]) == 0
    capsys.readouterr()

    private_note = "PRIVATE_INTERVIEW_NOTE_DO_NOT_EXPORT_ef91"
    (source / "artifacts" / "private-notes.md").write_text(
        f"# {private_note}\nreal resume\n",
        encoding="utf-8",
    )

    assert main(["practice-scenario", "--source", str(source), "--out", str(a)]) == 0
    capsys.readouterr()
    assert main(["practice-scenario", "--source", str(source), "--out", str(b)]) == 0
    capsys.readouterr()

    for rel in ("manifest.json", "practice-scenario.json", "practice-evidence.json", "summary.md"):
        assert (a / rel).read_text(encoding="utf-8") == (b / rel).read_text(
            encoding="utf-8"
        )

    exported_text = "\n".join(
        path.read_text(encoding="utf-8") for path in a.iterdir() if path.is_file()
    )
    forbidden = (
        private_note,
        "real resume",
        "Subtracting the per-axis max",
        "application submission",
        "live interview assistant",
        "job-board scraping",
        "private-notes.md",
    )
    assert all(term.lower() not in exported_text.lower() for term in forbidden)


def test_practice_scenario_rejects_source_artifact_paths_outside_bundle(
    tmp_path: Path,
    capsys,
) -> None:
    source = tmp_path / "career-loop"

    assert main(["demo-loop", "--out", str(source), "--now", "2026-06-26"]) == 0
    capsys.readouterr()
    manifest_path = source / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifacts"]["weak_spots"] = "../outside-weak-spots.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    rc = main(["practice-scenario", "--source", str(source), "--out", str(tmp_path / "out")])

    assert rc == 1
    assert "artifact paths must stay inside the bundle" in capsys.readouterr().err
