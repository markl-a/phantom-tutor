from __future__ import annotations

import json
from pathlib import Path

from phantom_tutor.cli import main


def test_learning_plan_demo_writes_synthetic_plan_and_evidence_bundle(
    tmp_path: Path,
    capsys,
) -> None:
    source = tmp_path / "career-loop"
    out = tmp_path / "learning-plan"

    assert main(["demo-loop", "--out", str(source), "--now", "2026-06-26"]) == 0
    capsys.readouterr()

    assert main(
        [
            "learning-plan-demo",
            "--source",
            str(source),
            "--out",
            str(out),
            "--horizon-days",
            "14",
        ]
    ) == 0
    manifest_path = Path(capsys.readouterr().out.strip())
    assert manifest_path == out / "manifest.json"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    plan = json.loads((out / "learning-plan.json").read_text(encoding="utf-8"))
    evidence = json.loads((out / "evidence-tracker.json").read_text(encoding="utf-8"))
    summary = (out / "summary.md").read_text(encoding="utf-8")

    assert manifest["schema_version"] == 1
    assert manifest["mode"] == "synthetic_learning_plan_bundle"
    assert manifest["source_mode"] == "synthetic_career_learning_loop"
    assert manifest["data_policy"] == "synthetic_only"
    assert manifest["private_data_included"] is False
    assert manifest["external_network"] is False
    assert manifest["llm_provider"] == "stub_or_disabled"
    assert manifest["anti_cheating_boundary"] == "practice_only_no_live_interview_assistance"
    assert manifest["artifacts"] == {
        "evidence_tracker": "evidence-tracker.json",
        "learning_plan": "learning-plan.json",
        "summary": "summary.md",
    }

    assert plan["mode"] == "synthetic_learning_plan"
    assert plan["horizon_days"] == 14
    assert plan["start_date"] == "2026-06-26"
    assert plan["end_date"] == "2026-07-10"
    assert plan["source_counts"]["weak_spots"] >= 5
    assert [item["topic"] for item in plan["items"][:3]] == ["governance", "mlops", "rag"]
    assert {item["practice_mode"] for item in plan["items"]} <= {
        "quiz",
        "design",
        "code",
    }
    assert all(item["source"] == "synthetic_job_gap" for item in plan["items"])
    assert all("tutor " in item["command_hint"] for item in plan["items"])

    assert evidence["mode"] == "synthetic_evidence_tracker"
    assert evidence["private_data_included"] is False
    assert evidence["items"][0]["kind"] == "practice_result"
    assert evidence["items"][0]["topic"] == "softmax"
    assert evidence["items"][0]["score"] == 0.0
    assert evidence["items"][0]["raw_answer_included"] is False

    exported_text = "\n".join(
        path.read_text(encoding="utf-8") for path in out.iterdir() if path.is_file()
    )
    forbidden = (
        "Subtracting the per-axis max",
        "real resume",
        "application submission",
        "private interview",
        "live interview assistant",
        "job-board scraping",
    )
    assert all(term.lower() not in exported_text.lower() for term in forbidden)
    assert "Learning plan" in summary
    assert "Evidence tracker" in summary


def test_learning_plan_demo_rejects_private_or_network_source_manifest(
    tmp_path: Path,
    capsys,
) -> None:
    source = tmp_path / "bad-source"
    source.mkdir()
    (source / "manifest.json").write_text(
        json.dumps(
            {
                "mode": "synthetic_career_learning_loop",
                "data_policy": "synthetic_only",
                "private_data_included": False,
                "external_network": True,
                "llm_provider": "stub_or_disabled",
                "anti_cheating_boundary": "practice_only_no_live_interview_assistance",
                "artifacts": {},
            }
        ),
        encoding="utf-8",
    )

    rc = main(["learning-plan-demo", "--source", str(source), "--out", str(tmp_path / "out")])

    assert rc == 1
    assert "only accepts safe synthetic demo-loop bundles" in capsys.readouterr().err


def test_learning_plan_demo_rejects_source_artifact_paths_outside_bundle(
    tmp_path: Path,
    capsys,
) -> None:
    source = tmp_path / "career-loop"

    assert main(["demo-loop", "--out", str(source), "--now", "2026-06-26"]) == 0
    capsys.readouterr()
    manifest_path = source / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifacts"]["review_result"] = "../private-review.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    rc = main(["learning-plan-demo", "--source", str(source), "--out", str(tmp_path / "out")])

    assert rc == 1
    assert "artifact paths must stay inside the bundle" in capsys.readouterr().err


def test_learning_plan_demo_is_byte_stable_for_same_inputs(
    tmp_path: Path,
    capsys,
) -> None:
    source = tmp_path / "career-loop"
    a = tmp_path / "a"
    b = tmp_path / "b"

    assert main(["demo-loop", "--out", str(source), "--now", "2026-06-26"]) == 0
    capsys.readouterr()

    assert main(["learning-plan-demo", "--source", str(source), "--out", str(a)]) == 0
    capsys.readouterr()
    assert main(["learning-plan-demo", "--source", str(source), "--out", str(b)]) == 0
    capsys.readouterr()

    for rel in ("manifest.json", "learning-plan.json", "evidence-tracker.json", "summary.md"):
        assert (a / rel).read_text(encoding="utf-8") == (b / rel).read_text(
            encoding="utf-8"
        )
