from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_readme_documents_demo_loop_and_safety_boundary() -> None:
    text = _read("README.md")
    normalized = " ".join(text.split())

    assert "demo-loop" in text
    assert "learning-plan-demo" in text
    assert "practice-scenario" in text
    assert "docs/SYNTHETIC_CAREER_LOOP.md" in text
    assert "docs/LEARNING_PLAN_BUNDLE.md" in text
    assert "docs/PRACTICE_SCENARIO_BUNDLE.md" in text
    assert "synthetic" in text.lower()
    assert "Anti-cheating policy" in text
    assert "covert live interview assistant" in normalized


def test_synthetic_career_loop_contract_documents_manifest_and_artifacts() -> None:
    text = _read("docs/SYNTHETIC_CAREER_LOOP.md")

    assert "demo-loop" in text
    assert "manifest.json" in text
    assert "synthetic_career_learning_loop" in text
    assert "synthetic_only" in text
    assert "private_data_included" in text
    assert "external_network" in text
    assert "practice_only_no_live_interview_assistance" in text
    for artifact in (
        "jobs.json",
        "operator_skills.json",
        "gap-report.json",
        "review-result.json",
        "weak_spots.json",
        "attempts.jsonl",
        "summary.md",
    ):
        assert artifact in text


def test_learning_plan_contract_documents_plan_and_evidence_boundaries() -> None:
    text = _read("docs/LEARNING_PLAN_BUNDLE.md")

    assert "learning-plan-demo" in text
    assert "manifest.json" in text
    assert "learning-plan.json" in text
    assert "evidence-tracker.json" in text
    assert "synthetic_learning_plan_bundle" in text
    assert "synthetic_only" in text
    assert "private_data_included=false" in text
    assert "external_network=false" in text
    assert "stub_or_disabled" in text
    assert "practice_only_no_live_interview_assistance" in text
    assert "raw answers" in text
    assert "private interview notes" in text
    assert "byte-stable" in text


def test_practice_scenario_contract_documents_p3_bundle_boundaries() -> None:
    text = _read("docs/PRACTICE_SCENARIO_BUNDLE.md")

    assert "practice-scenario" in text
    assert "manifest.json" in text
    assert "practice-scenario.json" in text
    assert "practice-evidence.json" in text
    assert "synthetic_practice_scenario_bundle" in text
    assert "synthetic_only" in text
    assert "private_data_included=false" in text
    assert "external_network=false" in text
    assert "stub_or_disabled" in text
    assert "practice_only_no_live_interview_assistance" in text
    assert "raw answers" in text
    assert "covert live interview assistance" in text
    assert "byte-stable" in text
