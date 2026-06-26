"""Deterministic synthetic career-learning demo artifacts."""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from . import jobs, memory, paths
from .modes import knowledge

SCHEMA_VERSION = 1


def write_synthetic_demo_loop(
    *,
    out_root: str | Path,
    now: str = "2026-06-26",
) -> Path:
    """Write a local-only job-gap -> practice-review artifact bundle."""
    out = Path(out_root)
    artifacts = out / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)

    with _tutor_home(artifacts):
        _reset_store_files()
        job_records = _synthetic_jobs()
        profile = _synthetic_profile()
        source_jobs = artifacts / "source-jobs.json"
        source_profile = artifacts / "source-operator-skills.json"
        source_jobs.write_text(
            json.dumps(job_records, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        source_profile.write_text(
            json.dumps(profile, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        ingested = jobs.ingest_records(job_records)
        paths.jobs_path().write_text(
            json.dumps(ingested, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        paths.operator_profile_path().write_text(
            json.dumps(profile, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        seeded = jobs.seed_weak_spots(ingested, profile, now, top_n=5)
        gap_report = {
            "now": now,
            "jobs_ingested": len(ingested),
            "seeded": seeded,
            "due": memory.due_topics(now),
        }
        gap_path = artifacts / "gap-report.json"
        gap_path.write_text(
            json.dumps(gap_report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        review_result = knowledge.run_quiz(
            "k-softmax",
            "no idea",
            now,
            use_llm=False,
        )
        paths.weak_spots_path().write_text(
            json.dumps(memory.load_store(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        review_path = artifacts / "review-result.json"
        review_path.write_text(
            json.dumps(review_result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        summary_path = artifacts / "summary.md"
        summary_path.write_text(_summary(now, gap_report, review_result), encoding="utf-8")

        manifest = {
            "schema_version": SCHEMA_VERSION,
            "mode": "synthetic_career_learning_loop",
            "now": now,
            "data_policy": "synthetic_only",
            "private_data_included": False,
            "external_network": False,
            "llm_provider": "stub_or_disabled",
            "anti_cheating_boundary": "practice_only_no_live_interview_assistance",
            "artifacts": {
                "source_jobs": _rel(out, source_jobs),
                "source_profile": _rel(out, source_profile),
                "jobs": _rel(out, paths.jobs_path()),
                "profile": _rel(out, paths.operator_profile_path()),
                "gap_report": _rel(out, gap_path),
                "review_result": _rel(out, review_path),
                "weak_spots": _rel(out, paths.weak_spots_path()),
                "attempts": _rel(out, paths.attempts_path()),
                "summary": _rel(out, summary_path),
            },
        }

    manifest_path = out / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _synthetic_jobs() -> list[dict]:
    return [
        {
            "job_id": "synthetic-ai-platform",
            "title": "AI Platform Engineer",
            "company_tier": "big",
            "skills_norm": ["python", "mlops", "rag"],
            "themes": ["governance", "platform"],
            "salary_hi": 90000,
            "salary_disclosed": True,
            "match_score": 72,
        },
        {
            "job_id": "synthetic-agent-product",
            "title": "Agent Product Engineer",
            "company_tier": "mid",
            "skills_norm": ["python", "rag", "evaluation"],
            "themes": ["product", "governance"],
            "salary_hi": 78000,
            "salary_disclosed": True,
            "match_score": 68,
        },
        {
            "job_id": "synthetic-agency-noise",
            "title": "Agency Posting",
            "company_tier": "agency",
            "skills_norm": ["sales"],
            "themes": ["outsourcing"],
            "match_score": 0,
        },
    ]


def _reset_store_files() -> None:
    for path in (
        paths.jobs_path(),
        paths.operator_profile_path(),
        paths.weak_spots_path(),
        paths.attempts_path(),
    ):
        if path.exists():
            path.unlink()


def _synthetic_profile() -> dict:
    return {
        "has_skills": ["python"],
        "weak_or_missing": ["mlops", "rag", "governance"],
    }


def _summary(now: str, gap_report: dict, review_result: dict) -> str:
    seeded = ", ".join(s["topic"] for s in gap_report["seeded"])
    topic = review_result["item"]["topic"]
    score = review_result["score"]
    mastery = review_result["record"]["mastery"]
    due = review_result["record"]["due"]
    return (
        "# Synthetic career learning loop\n\n"
        f"- Date: {now}\n"
        f"- Synthetic jobs ingested: {gap_report['jobs_ingested']}\n"
        f"- Job gap weak spots seeded: {seeded}\n"
        f"- Practice review updated: {topic} score={score:.2f}, "
        f"mastery={mastery:.2f}, next due={due}\n"
        "- Boundary: practice-side learning only; no scraping, submission, or "
        "real-time hidden assistance.\n"
    )


@contextmanager
def _tutor_home(path: Path) -> Iterator[None]:
    old = os.environ.get("PHANTOM_TUTOR_HOME")
    os.environ["PHANTOM_TUTOR_HOME"] = str(path)
    try:
        yield
    finally:
        if old is None:
            os.environ.pop("PHANTOM_TUTOR_HOME", None)
        else:
            os.environ["PHANTOM_TUTOR_HOME"] = old


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


__all__ = ["SCHEMA_VERSION", "write_synthetic_demo_loop"]
