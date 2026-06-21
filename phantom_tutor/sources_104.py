"""104 matched_v2 CSV -> top200 source adapter. Reads the operator's job export
(UTF-8 BOM), normalizes each row into the schema jobs.ingest consumes, scores a
composite (05 rubric), and returns the top-N. Pure read — never writes. The raw
CSV holds PII (companies/salaries/urls); only derived top200 reaches data_root."""
from __future__ import annotations

import csv
import re

# Substring name tables (the source CSV has no employee-count column, so tier is
# name-driven). All tunable; operator extends MID/BIG after a real run.
BIG_COMPANIES = {
    "台積", "鴻海", "聯發科", "南亞科", "美光", "Micron", "廣達", "緯創", "和碩",
    "華碩", "宏碁", "技嘉", "研華", "台達", "聯詠", "瑞昱", "日月光", "群聯",
    "世界先進", "力積電", "國泰", "富邦", "中信", "中國信託", "玉山", "台新",
    "永豐", "工研院", "資策會", "趨勢", "LINE", "Appier", "iKala", "Garmin",
    "台灣大哥大", "Google", "Microsoft", "NVIDIA", "Intel", "AWS", "Qualcomm",
    "Synopsys", "Cadence",
}
MID_COMPANIES = {"行動貝果", "神基", "緯穎"}
# Staffing / proxy-recruiting bait (05 §2.1: noise, not a target). 代招/代徵 markers
# usually sit in the title, so _tier checks company + title for these.
AGENCY_KEYWORDS = {"人力", "仲介", "獵頭", "獵才", "派遣", "顧問派遣", "補習", "人資",
                   "代招", "代徵", "招募顧問"}
DIRECTION_KEYWORDS = [
    "agent", "llm", "rag", "mlops", "platform", "infra", "serving", "vllm",
    "triton", "langchain", "k8s", "vector", "embedding", "推論", "平台", "框架",
    "架構師", "pytorch", "tensorflow", "fine-tune", "huggingface", "transformer",
    "distributed",
]

_SENTINEL = 9_999_999
_ANNUAL_THRESHOLD = 300_000  # a salary >= this is annual; convert to monthly
_SPLIT = re.compile(r"[,、/;\s]+")


def _parse_float(s: str) -> float:
    s = (s or "").replace(",", "").strip()
    if not s:
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def _parse_int(s: str) -> int:
    return int(_parse_float(s))


def _to_monthly(raw: int) -> int:
    if raw <= 0 or raw >= _SENTINEL:
        return 0
    return raw // 12 if raw >= _ANNUAL_THRESHOLD else raw


def _split_skills(text: str) -> list[str]:
    out: list[str] = []
    for tok in _SPLIT.split(text or ""):
        t = tok.strip().lower()
        if t and t not in out:
            out.append(t)
    return out


def _themes(text: str) -> list[str]:
    low = (text or "").lower()
    return [kw for kw in DIRECTION_KEYWORDS if kw in low]


def _tier(company: str, title: str = "") -> str:
    c = company or ""
    if any(k in (c + " " + (title or "")) for k in AGENCY_KEYWORDS):
        return "agency"
    if any(k in c for k in BIG_COMPANIES):
        return "big"
    if any(k in c for k in MID_COMPANIES):
        return "mid"
    return "small"


def _composite(raw_hi: int, match_score: float, tier: str, n_themes: int) -> float:
    salary_norm = min(max(raw_hi, 0), 3_000_000) / 3_000_000 if raw_hi < _SENTINEL else 0.0
    match_norm = min(max(match_score, 0.0) / 85, 1.0)
    big = 1 if tier == "big" else 0
    direction = min(n_themes, 15) / 15
    return round(0.30 * salary_norm + 0.30 * match_norm + 0.20 * big + 0.20 * direction, 6)


def _record(row: dict) -> dict:
    raw_lo, raw_hi = _parse_int(row.get("薪資下限", "")), _parse_int(row.get("薪資上限", ""))
    lo, hi = _to_monthly(raw_lo), _to_monthly(raw_hi)
    title = row.get("職稱", "")
    company = row.get("公司", "")
    skills = _split_skills(row.get("需求技能", ""))
    themes = _themes(" ".join([title, row.get("需求技能", ""),
                               row.get("命中明細", ""), row.get("公司產業", "")]))
    tier = _tier(company, title)
    match_score = _parse_float(row.get("匹配分數", ""))
    return {
        "job_id": f"104-{row.get('職缺ID', '').strip()}",
        "title": title,
        "company": company,
        "company_tier": tier,
        "loc": row.get("工作地點", ""),
        "industry": row.get("公司產業", ""),
        "salary_lo": lo,
        "salary_hi": hi,
        "salary_disclosed": hi > 0,
        "skills_norm": skills,
        "themes": themes,
        "match_score": match_score,
        "composite": _composite(raw_hi, match_score, tier, len(themes)),
    }


def to_top200(csv_path: str, *, top_n: int = 200) -> list[dict]:
    """Read a 104 matched_v2 CSV (UTF-8 BOM) -> normalized records -> top-N by
    composite (05 rubric). Returns records ready for jobs.ingest."""
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        records = [_record(row) for row in csv.DictReader(f)]
    records.sort(key=lambda r: r["composite"], reverse=True)
    return records[:top_n]
