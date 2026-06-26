"""Synthetic weak-spot to practice scenario artifacts.

The scenario proves the P3 career-learning loop: pick a weak spot produced by a
synthetic job gap, run a deterministic practice outcome, record evidence, and
schedule the next review. It exports only aggregate practice evidence and never
copies raw answers, full prompts, resumes, private notes, or live job data.
"""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any

from . import srs

SCHEMA_VERSION = 1
PRACTICE_SCORE = 0.72


def write_practice_scenario_bundle(
    *,
    source_bundle: str | Path,
    out_root: str | Path,
) -> Path:
    """Write a deterministic P3 practice scenario bundle."""
    source = Path(source_bundle)
    out = Path(out_root)
    source_root, manifest = _load_source_manifest(source)
    _validate_source_manifest(manifest)

    artifacts = manifest.get("artifacts") or {}
    weak_spots = _load_json_artifact(source_root, artifacts, "weak_spots", default={})
    gap_report = _load_json_artifact(source_root, artifacts, "gap_report", default={})

    selected = _select_weak_spot(weak_spots=weak_spots, gap_report=gap_report)
    scenario = _build_scenario(manifest=manifest, selected=selected)
    evidence = _build_evidence(scenario)

    out.mkdir(parents=True, exist_ok=True)
    scenario_path = out / "practice-scenario.json"
    evidence_path = out / "practice-evidence.json"
    summary_path = out / "summary.md"
    scenario_path.write_text(_json(scenario), encoding="utf-8")
    evidence_path.write_text(_json(evidence), encoding="utf-8")
    summary_path.write_text(_summary(scenario), encoding="utf-8")

    out_manifest = {
        "schema_version": SCHEMA_VERSION,
        "mode": "synthetic_practice_scenario_bundle",
        "source_mode": manifest.get("mode", ""),
        "now": manifest.get("now", ""),
        "data_policy": "synthetic_only",
        "private_data_included": False,
        "external_network": False,
        "llm_provider": "stub_or_disabled",
        "anti_cheating_boundary": "practice_only_no_live_interview_assistance",
        "artifacts": {
            "evidence": _rel(out, evidence_path),
            "scenario": _rel(out, scenario_path),
            "summary": _rel(out, summary_path),
        },
    }
    manifest_path = out / "manifest.json"
    manifest_path.write_text(_json(out_manifest), encoding="utf-8")
    return manifest_path


def _load_source_manifest(source: Path) -> tuple[Path, dict[str, Any]]:
    manifest_path = source if source.is_file() else source / "manifest.json"
    if not manifest_path.exists():
        raise RuntimeError("practice-scenario requires a demo-loop manifest.json")
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise RuntimeError("practice-scenario manifest must be a JSON object")
    return manifest_path.parent, raw


def _validate_source_manifest(manifest: dict[str, Any]) -> None:
    if (
        manifest.get("mode") != "synthetic_career_learning_loop"
        or manifest.get("data_policy") != "synthetic_only"
        or manifest.get("private_data_included") is not False
        or manifest.get("external_network") is not False
        or manifest.get("llm_provider") != "stub_or_disabled"
        or manifest.get("anti_cheating_boundary")
        != "practice_only_no_live_interview_assistance"
    ):
        raise RuntimeError(
            "practice-scenario only accepts safe synthetic demo-loop bundles"
        )


def _load_json_artifact(
    source_root: Path,
    artifacts: dict[str, Any],
    key: str,
    *,
    default: Any,
) -> Any:
    rel = artifacts.get(key)
    if not isinstance(rel, str):
        return default
    path = _bundle_path(source_root, rel)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _select_weak_spot(
    *,
    weak_spots: dict[str, dict[str, Any]],
    gap_report: dict[str, Any],
) -> dict[str, Any]:
    due = gap_report.get("due")
    if not isinstance(due, list):
        due = []
    candidates: list[dict[str, Any]] = []
    for row in due:
        if isinstance(row, dict):
            candidates.append({**row, "source": "synthetic_job_gap"})
    if not candidates:
        candidates = [
            {"key": key, **value, "source": "synthetic_job_gap"}
            for key, value in weak_spots.items()
            if isinstance(value, dict)
        ]
    if not candidates:
        raise RuntimeError("practice-scenario requires at least one weak spot")
    return sorted(
        candidates,
        key=lambda row: (
            float(row.get("mastery", 0.0)),
            str(row.get("topic") or row.get("key") or ""),
        ),
    )[0]


def _build_scenario(*, manifest: dict[str, Any], selected: dict[str, Any]) -> dict[str, Any]:
    now = str(manifest.get("now") or "")
    before = deepcopy(selected)
    mastery_before = round(float(before.get("mastery", 0.0)), 4)
    attempts_before = int(before.get("attempts", 0))
    card_dict, due_iso = srs.review(before.get("fsrs"), PRACTICE_SCORE, now)
    mastery_after = round(0.6 * mastery_before + 0.4 * PRACTICE_SCORE, 4)
    attempts_after = attempts_before + 1
    topic = str(before.get("topic") or before.get("key") or "")
    dimension = str(before.get("dimension") or _dimension_for_topic(topic))
    mode = _practice_mode(topic, dimension)

    return {
        "schema_version": SCHEMA_VERSION,
        "mode": "synthetic_weak_spot_to_practice_scenario",
        "source_mode": manifest.get("mode", ""),
        "now": now,
        "data_policy": {
            "synthetic_only": True,
            "private_data_included": False,
            "external_network": False,
            "llm_provider": "stub_or_disabled",
            "anti_cheating_boundary": "practice_only_no_live_interview_assistance",
        },
        "selected_weak_spot": {
            "key": str(before.get("key") or topic),
            "topic": topic,
            "dimension": dimension,
            "mastery": mastery_before,
            "due": str(before.get("due", "")),
            "source": str(before.get("source", "synthetic_job_gap")),
        },
        "practice": {
            "mode": mode,
            "score": PRACTICE_SCORE,
            "graded_by": "deterministic_rubric_stub",
            "raw_answer_included": False,
            "full_prompt_included": False,
            "command_hint": _command_hint(mode, topic),
        },
        "srs_update": {
            "attempts_before": attempts_before,
            "attempts_after": attempts_after,
            "mastery_before": mastery_before,
            "mastery_after": mastery_after,
            "streak_after": 1 if PRACTICE_SCORE >= srs.PASS_THRESHOLD else 0,
            "next_due": due_iso,
            "interval_days": (date.fromisoformat(due_iso) - date.fromisoformat(now)).days,
            "fsrs_state_included": False,
            "fsrs_state_hash": _stable_state_hash(card_dict),
        },
        "readiness": {
            "weak_spot_selected": True,
            "practice_completed": True,
            "evidence_recorded": True,
            "next_review_scheduled": bool(due_iso),
        },
        "boundaries": {
            "covert_live_interview_assistance": "not_supported",
            "job_board_scraping": "not_supported",
            "application_submission": "not_supported",
            "raw_private_export": "not_supported",
            "cloud_llm_default": "not_supported",
        },
    }


def _build_evidence(scenario: dict[str, Any]) -> dict[str, Any]:
    selected = scenario["selected_weak_spot"]
    practice = scenario["practice"]
    srs_update = scenario["srs_update"]
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": "synthetic_practice_evidence",
        "data_policy": scenario["data_policy"],
        "items": [
            {
                "kind": "weak_spot_selection",
                "topic": selected["topic"],
                "dimension": selected["dimension"],
                "source": selected["source"],
                "mastery": selected["mastery"],
            },
            {
                "kind": "practice_result",
                "topic": selected["topic"],
                "dimension": selected["dimension"],
                "mode": practice["mode"],
                "score": practice["score"],
                "raw_answer_included": False,
                "full_prompt_included": False,
            },
            {
                "kind": "srs_update",
                "topic": selected["topic"],
                "attempts_after": srs_update["attempts_after"],
                "mastery_after": srs_update["mastery_after"],
                "next_due": srs_update["next_due"],
                "fsrs_state_included": False,
            },
        ],
    }


def _practice_mode(topic: str, dimension: str) -> str:
    lowered = f"{topic} {dimension}".lower()
    if "python" in lowered:
        return "code"
    if "platform" in lowered or "governance" in lowered:
        return "design"
    return "quiz"


def _dimension_for_topic(topic: str) -> str:
    return "career_gap" if topic else ""


def _command_hint(mode: str, topic: str) -> str:
    slug = _slug(topic)
    if mode == "code":
        return "tutor code --id c-two-sum --solution <local-file>"
    if mode == "design":
        return f"tutor design --id d-{slug} --answer <local-notes>"
    return f"tutor quiz --id k-{slug} --answer <local-answer>"


def _summary(scenario: dict[str, Any]) -> str:
    selected = scenario["selected_weak_spot"]
    practice = scenario["practice"]
    update = scenario["srs_update"]
    return (
        "# Weak spot to practice scenario\n\n"
        f"- Selected weak spot: {selected['topic']} ({selected['dimension']})\n"
        f"- Practice mode: {practice['mode']} with deterministic score {practice['score']:.2f}\n"
        f"- Mastery moved: {update['mastery_before']:.4f} -> {update['mastery_after']:.4f}\n"
        f"- Next review: {update['next_due']}\n"
        "- Boundary: practice-side learning only; no scraping, submission, "
        "hidden interview assistance, raw private export, or cloud LLM default.\n"
    )


def _stable_state_hash(value: dict[str, Any]) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return f"json-bytes:{len(raw)}"


def _bundle_path(root: Path, rel: str) -> Path:
    candidate = Path(rel)
    if candidate.is_absolute():
        raise RuntimeError("practice-scenario artifact paths must be bundle-relative")
    root_resolved = root.resolve()
    path = (root / candidate).resolve()
    try:
        path.relative_to(root_resolved)
    except ValueError as exc:
        raise RuntimeError("practice-scenario artifact paths must stay inside the bundle") from exc
    return path


def _slug(value: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in value.lower()).strip("-")


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


__all__ = [
    "PRACTICE_SCORE",
    "SCHEMA_VERSION",
    "write_practice_scenario_bundle",
]
