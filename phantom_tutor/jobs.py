"""jobs data layer: ingest target postings, compute skill demand, seed weak_spots
from demand-supply gaps, and surface side-hustle (sellable) skills. All data lives
under paths.data_root() and never enters the repo."""
from __future__ import annotations

import json
from collections import Counter

from . import paths


def load_jobs() -> list[dict]:
    p = paths.jobs_path()
    if not p.exists():
        return []
    raw = p.read_text(encoding="utf-8").strip()
    return json.loads(raw) if raw else []


def ingest(src_path: str) -> list[dict]:
    """Read a top200-style JSON list -> dedup by job_id -> drop agency noise ->
    persist to jobs.json. Returns the written records."""
    raw = json.loads(open(src_path, encoding="utf-8").read())
    seen: set[str] = set()
    out: list[dict] = []
    for rec in raw:
        jid = rec.get("job_id")
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
