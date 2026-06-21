"""weak_spots store — the owned-memory spine. Phase-1 backend = local JSON;
the public fns (record_attempt/due_topics/list_weak) are the swappable interface
that Phase-2 re-points at phantom core owned-memory."""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from . import paths, srs


def load_store(path: Path | None = None) -> dict[str, dict[str, Any]]:
    p = path or paths.weak_spots_path()
    if not p.exists():
        return {}
    raw = p.read_text(encoding="utf-8").strip()
    return json.loads(raw) if raw else {}


def save_store(store: dict, path: Path | None = None) -> None:
    p = path or paths.weak_spots_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(store, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")


def record_attempt(key: str, dimension: str, score: float, now_iso: str,
                   *, topic: str | None = None, path: Path | None = None) -> dict:
    """Record one graded attempt: update mastery (EMA), streak, attempts, last_seen=now,
    and schedule due via srs. Returns the updated record (with 'key')."""
    store = load_store(path)
    rec = store.get(key, {"topic": topic or key, "dimension": dimension,
                          "mastery": 0.0, "interval": 0, "streak": 0,
                          "attempts": 0, "last_seen": now_iso, "due": now_iso})
    rec["topic"] = topic or rec.get("topic", key)
    rec["dimension"] = dimension
    rec["attempts"] += 1
    rec["mastery"] = round(0.6 * rec["mastery"] + 0.4 * float(score), 4)
    rec["streak"] = rec["streak"] + 1 if score >= srs.PASS_THRESHOLD else 0
    rec["last_seen"] = now_iso
    interval = srs.next_interval_days(rec.get("interval", 0), float(score))
    rec["interval"] = interval
    rec["due"] = (date.fromisoformat(now_iso) + timedelta(days=interval)).isoformat()
    store[key] = rec
    save_store(store, path)
    _append_attempt(key, dimension, float(score), now_iso)
    return {"key": key, **rec}


def seed_weak_spot(key: str, dimension: str, mastery: float, now_iso: str,
                   *, topic: str | None = None, path: Path | None = None) -> dict:
    """Seed/refresh a weak_spot due immediately (for gap seeding from job demand).
    Sets due=now_iso so `tutor today` surfaces it the same day; mastery reflects
    current strength (lower = weaker = surfaced first). Unlike record_attempt this
    does NOT count as a graded attempt or advance the SRS interval."""
    store = load_store(path)
    rec = store.get(key, {"topic": topic or key, "dimension": dimension,
                          "mastery": 0.0, "interval": 0, "streak": 0,
                          "attempts": 0, "last_seen": now_iso, "due": now_iso})
    rec["topic"] = topic or rec.get("topic", key)
    rec["dimension"] = dimension
    rec["mastery"] = round(float(mastery), 4)
    rec["due"] = now_iso
    store[key] = rec
    save_store(store, path)
    return {"key": key, **rec}


def _append_attempt(key: str, dimension: str, score: float, now_iso: str) -> None:
    """Append one append-only attempt line (review history; feeds future FSRS)."""
    p = paths.attempts_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps({"key": key, "dimension": dimension, "score": score, "at": now_iso},
                      ensure_ascii=False)
    with p.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def due_topics(now_iso: str, path: Path | None = None) -> list[dict]:
    """Records due on/before now_iso, weakest (lowest mastery) first."""
    store = load_store(path)
    due = [{"key": k, **v} for k, v in store.items() if srs.is_due(v["due"], now_iso)]
    return sorted(due, key=lambda r: r["mastery"])


def list_weak(n: int | None = None, path: Path | None = None) -> list[dict]:
    store = load_store(path)
    items = sorted(({"key": k, **v} for k, v in store.items()), key=lambda r: r["mastery"])
    return items[:n] if n else items
