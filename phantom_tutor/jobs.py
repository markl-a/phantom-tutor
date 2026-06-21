"""jobs data layer: ingest target postings, compute skill demand, seed weak_spots
from demand-supply gaps, and surface side-hustle (sellable) skills. All data lives
under paths.data_root() and never enters the repo."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from . import memory, paths


def load_jobs() -> list[dict]:
    p = paths.jobs_path()
    if not p.exists():
        return []
    raw = p.read_text(encoding="utf-8").strip()
    return json.loads(raw) if raw else []


def ingest(src_path: str) -> list[dict]:
    """Read a top200-style JSON list -> dedup by job_id -> drop agency noise ->
    persist to jobs.json. Returns the written records."""
    raw = json.loads(Path(src_path).read_text(encoding="utf-8"))
    seen: set[str] = set()
    out: list[dict] = []
    for rec in raw:
        jid = rec.get("job_id")
        if jid is None:
            continue
        if jid in seen or rec.get("company_tier") == "agency":
            continue
        seen.add(jid)
        out.append(rec)
    p = paths.jobs_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def demand(jobs: list[dict]) -> dict[str, int]:
    """Frequency of each skill/theme across all jobs, descending by count."""
    c: Counter[str] = Counter()
    for j in jobs:
        c.update(j.get("skills_norm", []))
        c.update(j.get("themes", []))
    return dict(c.most_common())


def load_profile() -> dict:
    p = paths.operator_profile_path()
    if not p.exists():
        return {"has_skills": [], "weak_or_missing": []}
    data = json.loads(p.read_text(encoding="utf-8"))
    data.setdefault("has_skills", [])
    data.setdefault("weak_or_missing", [])
    return data


def _coverage(skill: str, profile: dict) -> float:
    if skill in profile.get("has_skills", []):
        return 0.7
    if skill in profile.get("weak_or_missing", []):
        return 0.0
    return 0.4


def seed_weak_spots(jobs: list[dict], profile: dict, now_iso: str,
                    *, top_n: int = 10) -> list[dict]:
    """Seed weak_spots from demand-supply gaps: priority = demand*(1-coverage).
    Top-N gaps get a seed_weak_spot(mastery=coverage) due immediately so
    `tutor today` surfaces them the same day weakest-first. Returns seeded records."""
    d = demand(jobs)
    scored = sorted(
        ((skill, freq, _coverage(skill, profile)) for skill, freq in d.items()),
        key=lambda t: t[1] * (1 - t[2]), reverse=True,
    )
    seeded: list[dict] = []
    for skill, _freq, cov in scored[:top_n]:
        rec = memory.seed_weak_spot(skill, "job-gap", cov, now_iso, topic=skill)
        seeded.append(rec)
    return seeded


def side_hustle(jobs: list[dict], profile: dict, *, top_n: int = 10) -> list[dict]:
    """Side-hustle analysis: sellable = demand * coverage (hot market x you're
    strong). Symmetric to gap seeding. Real gaps (coverage 0) score 0 and drop
    off the top. Returns top-N {skill, demand, coverage, score} descending."""
    d = demand(jobs)
    out = []
    for skill, freq in d.items():
        cov = _coverage(skill, profile)
        score = round(freq * cov, 4)
        if score > 0:
            out.append({"skill": skill, "demand": freq, "coverage": cov, "score": score})
    out.sort(key=lambda r: r["score"], reverse=True)
    return out[:top_n]
