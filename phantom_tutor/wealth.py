"""wealth-score — pure four-axis life-wealth objective on top of match_score.
No I/O. score = 3*W1 + 2.5*W2 + 2*W3 + 2*W4 (max 47.5). W1/W2 weighted to
deliberately outweigh raw salary (portfolio leverage + durability beat pay)."""
from __future__ import annotations

W1_HIGH = {"agent", "runtime", "platform", "governance", "mlops", "infra"}
W1_MID = {"llm", "rag"}
W2_HIGH = {"agent", "platform", "infra", "system-design", "governance", "architect", "mlops"}
W2_MID = {"rag", "application"}

_MONTHS = 14  # TWD annual estimate = monthly * 14 (12 + ~2 months bonus)


def _text(job: dict) -> str:
    parts = [job.get("title", ""), *job.get("skills_norm", []), *job.get("themes", [])]
    return " ".join(parts).lower()


def _axis(text: str, high: set[str], mid: set[str]) -> int:
    if any(tok in text for tok in high):
        return 5
    if any(tok in text for tok in mid):
        return 3
    return 1


def _w3(job: dict) -> int:
    hi = job.get("salary_hi", 0)
    if not job.get("salary_disclosed") or hi <= 0 or hi >= 9_999_999:
        return 1
    annual = hi * _MONTHS
    if annual >= 1_600_000:
        return 5
    if annual >= 1_000_000:
        return 4
    if annual >= 800_000:
        return 2
    return 1


def _w4(job: dict) -> int:
    match = float(job.get("match_score", 0))
    tier = job.get("company_tier", "small")
    if match >= 60 and tier == "big":
        return 5
    if match >= 60 or tier in {"big", "mid"}:
        return 3
    return 1


def wealth_score(job: dict) -> dict:
    text = _text(job)
    w1 = _axis(text, W1_HIGH, W1_MID)
    w2 = _axis(text, W2_HIGH, W2_MID)
    w3 = _w3(job)
    w4 = _w4(job)
    score = round(3 * w1 + 2.5 * w2 + 2 * w3 + 2 * w4, 2)
    return {"w1": w1, "w2": w2, "w3": w3, "w4": w4, "score": score}


def rank(jobs: list[dict]) -> list[dict]:
    """Each job gets a 'wealth' sub-dict; sorted by wealth score descending.
    This is the job-switch target list ('which job to move to')."""
    scored = [{**j, "wealth": wealth_score(j)} for j in jobs]
    return sorted(scored, key=lambda j: j["wealth"]["score"], reverse=True)
