"""Deterministic learning-plan and evidence-tracker artifacts.

This module consumes the synthetic career demo bundle and derives a public,
practice-side learning plan. It deliberately excludes raw answers, resumes,
application history, private interview notes, network output, and live LLM text.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1


def write_learning_plan_bundle(
    *,
    source_bundle: str | Path,
    out_root: str | Path,
    horizon_days: int = 14,
) -> Path:
    """Write a deterministic synthetic learning-plan bundle."""
    if horizon_days <= 0:
        raise ValueError("horizon-days must be positive")

    source = Path(source_bundle)
    out = Path(out_root)
    source_root, manifest = _load_source_manifest(source)
    _validate_source_manifest(manifest)

    artifacts = manifest.get("artifacts") or {}
    weak_spots = _load_json_artifact(source_root, artifacts, "weak_spots", default={})
    gap_report = _load_json_artifact(source_root, artifacts, "gap_report", default={})
    review_result = _load_json_artifact(source_root, artifacts, "review_result", default={})
    attempts = _load_jsonl_artifact(source_root, artifacts, "attempts")

    plan = _build_learning_plan(
        now=str(manifest.get("now", "")),
        horizon_days=horizon_days,
        weak_spots=weak_spots,
        gap_report=gap_report,
    )
    evidence = _build_evidence_tracker(
        now=str(manifest.get("now", "")),
        review_result=review_result,
        attempts=attempts,
    )

    out.mkdir(parents=True, exist_ok=True)
    plan_path = out / "learning-plan.json"
    evidence_path = out / "evidence-tracker.json"
    summary_path = out / "summary.md"
    plan_path.write_text(_json(plan), encoding="utf-8")
    evidence_path.write_text(_json(evidence), encoding="utf-8")
    summary_path.write_text(_summary(plan, evidence), encoding="utf-8")

    out_manifest = {
        "schema_version": SCHEMA_VERSION,
        "mode": "synthetic_learning_plan_bundle",
        "source_mode": manifest.get("mode", ""),
        "now": manifest.get("now", ""),
        "horizon_days": horizon_days,
        "data_policy": "synthetic_only",
        "private_data_included": False,
        "external_network": False,
        "llm_provider": "stub_or_disabled",
        "anti_cheating_boundary": "practice_only_no_live_interview_assistance",
        "artifacts": {
            "evidence_tracker": _rel(out, evidence_path),
            "learning_plan": _rel(out, plan_path),
            "summary": _rel(out, summary_path),
        },
    }
    manifest_path = out / "manifest.json"
    manifest_path.write_text(_json(out_manifest), encoding="utf-8")
    return manifest_path


def _load_source_manifest(source: Path) -> tuple[Path, dict[str, Any]]:
    manifest_path = source if source.is_file() else source / "manifest.json"
    if not manifest_path.exists():
        raise RuntimeError("learning-plan-demo requires a demo-loop manifest.json")
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise RuntimeError("learning-plan-demo manifest must be a JSON object")
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
            "learning-plan-demo only accepts safe synthetic demo-loop bundles"
        )


def _load_json_artifact(
    source: Path,
    artifacts: dict[str, Any],
    key: str,
    *,
    default: Any,
) -> Any:
    rel = artifacts.get(key)
    if not isinstance(rel, str):
        return default
    path = _bundle_path(source, rel)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl_artifact(
    source: Path,
    artifacts: dict[str, Any],
    key: str,
) -> list[dict[str, Any]]:
    rel = artifacts.get(key)
    if not isinstance(rel, str):
        return []
    path = _bundle_path(source, rel)
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _build_learning_plan(
    *,
    now: str,
    horizon_days: int,
    weak_spots: dict[str, dict[str, Any]],
    gap_report: dict[str, Any],
) -> dict[str, Any]:
    start = date.fromisoformat(now)
    due_topics = gap_report.get("due") or []
    if not isinstance(due_topics, list):
        due_topics = []
    candidates = due_topics or [{"key": k, **v} for k, v in weak_spots.items()]
    candidates = sorted(
        (c for c in candidates if isinstance(c, dict)),
        key=lambda c: (
            float(c.get("mastery", 0.0)),
            str(c.get("topic") or c.get("key") or ""),
        ),
    )

    items = [
        _plan_item(record, index=idx, start=start)
        for idx, record in enumerate(candidates[:5])
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": "synthetic_learning_plan",
        "start_date": now,
        "end_date": (start + timedelta(days=horizon_days)).isoformat(),
        "horizon_days": horizon_days,
        "data_policy": "synthetic_only",
        "private_data_included": False,
        "external_network": False,
        "llm_provider": "stub_or_disabled",
        "anti_cheating_boundary": "practice_only_no_live_interview_assistance",
        "source_counts": {
            "weak_spots": len(weak_spots),
            "due_topics": len(candidates),
            "items": len(items),
        },
        "items": items,
    }


def _plan_item(record: dict[str, Any], *, index: int, start: date) -> dict[str, Any]:
    topic = str(record.get("topic") or record.get("key") or "")
    mastery = round(float(record.get("mastery", 0.0)), 4)
    mode = _practice_mode(topic, str(record.get("dimension", "")))
    return {
        "topic": topic,
        "dimension": str(record.get("dimension", "")),
        "priority": index + 1,
        "mastery": mastery,
        "due": str(record.get("due", "")),
        "scheduled_date": (start + timedelta(days=index * 2)).isoformat(),
        "practice_mode": mode,
        "source": "synthetic_job_gap",
        "success_criteria": "complete one practice attempt and record the score locally",
        "command_hint": _command_hint(mode, topic),
    }


def _practice_mode(topic: str, dimension: str) -> str:
    lowered = f"{topic} {dimension}".lower()
    if "python" in lowered:
        return "code"
    if "platform" in lowered or "governance" in lowered:
        return "design"
    return "quiz"


def _command_hint(mode: str, topic: str) -> str:
    if mode == "code":
        return "tutor code --id c-two-sum --solution <local-file>"
    if mode == "design":
        return f"tutor design --id d-{_slug(topic)} --answer <local-notes>"
    return f"tutor quiz --id k-{_slug(topic)} --answer <local-answer>"


def _build_evidence_tracker(
    *,
    now: str,
    review_result: dict[str, Any],
    attempts: list[dict[str, Any]],
) -> dict[str, Any]:
    item = review_result.get("item") or {}
    record = review_result.get("record") or {}
    evidence_items: list[dict[str, Any]] = []
    if review_result:
        evidence_items.append(
            {
                "kind": "practice_result",
                "topic": str(item.get("topic") or record.get("topic") or ""),
                "dimension": str(item.get("dimension") or record.get("dimension") or ""),
                "score": float(review_result.get("score", 0.0)),
                "mastery_after": float(record.get("mastery", 0.0)),
                "attempts_after": int(record.get("attempts", 0)),
                "recorded_at": now,
                "raw_answer_included": False,
                "raw_question_included": False,
            }
        )
    for row in attempts:
        evidence_items.append(
            {
                "kind": "attempt_log",
                "topic": str(row.get("key", "")),
                "dimension": str(row.get("dimension", "")),
                "score": float(row.get("score", 0.0)),
                "recorded_at": str(row.get("at", "")),
                "raw_answer_included": False,
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": "synthetic_evidence_tracker",
        "data_policy": "synthetic_only",
        "private_data_included": False,
        "external_network": False,
        "llm_provider": "stub_or_disabled",
        "anti_cheating_boundary": "practice_only_no_live_interview_assistance",
        "items": evidence_items,
    }


def _summary(plan: dict[str, Any], evidence: dict[str, Any]) -> str:
    topics = ", ".join(item["topic"] for item in plan["items"])
    return (
        "# Synthetic learning plan bundle\n\n"
        f"- Learning plan items: {len(plan['items'])}\n"
        f"- Learning plan topics: {topics}\n"
        f"- Evidence tracker items: {len(evidence['items'])}\n"
        "- Boundary: practice-side learning only; no scraping, submission, "
        "or hidden assistance.\n"
    )


def _slug(value: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in value.lower()).strip("-")


def _bundle_path(root: Path, rel: str) -> Path:
    candidate = Path(rel)
    if candidate.is_absolute():
        raise RuntimeError("learning-plan-demo artifact paths must be bundle-relative")
    root_resolved = root.resolve()
    path = (root / candidate).resolve()
    try:
        path.relative_to(root_resolved)
    except ValueError as exc:
        raise RuntimeError("learning-plan-demo artifact paths must stay inside the bundle") from exc
    return path


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


__all__ = ["SCHEMA_VERSION", "write_learning_plan_bundle"]
