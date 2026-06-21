# jobs Layer + wealth-score Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `jobs` data layer (ingest/demand/gap-seeding) and a four-axis `wealth-score` pure function, exposing job-switch (`rank`) and side-hustle (`side-hustle`) analysis via `tutor jobs`.

**Architecture:** Two new modules mirroring the existing `srs.py` (pure) vs `memory.py` (I/O) split: `phantom_tutor/wealth.py` is a pure scorer; `phantom_tutor/jobs.py` is the data layer that reads/writes `data_root()` and reuses `memory.record_attempt`. Three derived signals share one `_coverage` helper — gap = demand×(1−coverage), side-hustle = demand×coverage, switch = wealth-score ranking. All real job data stays in `data_root()`; tests use synthetic PII-free fixtures.

**Tech Stack:** Python 3.11, stdlib only (json, argparse, collections, pathlib), pytest, ruff.

**Spec:** `docs/superpowers/specs/2026-06-21-jobs-layer-wealth-score-design.md`

---

## File Structure

| File | Responsibility | Action |
|---|---|---|
| `phantom_tutor/paths.py` | data-root path resolution | Modify: add `jobs_path()`, `operator_profile_path()` |
| `phantom_tutor/wealth.py` | pure four-axis scorer + rank | Create |
| `phantom_tutor/jobs.py` | data layer: ingest/demand/seed/side-hustle/profile | Create |
| `phantom_tutor/cli.py` | CLI `tutor jobs <action>` | Modify: add `jobs` subcommand |
| `tests/test_paths.py` | path resolution tests | Modify |
| `tests/test_wealth.py` | wealth_score axes + rank | Create |
| `tests/test_jobs.py` | ingest/demand/coverage/seed/side-hustle | Create |
| `tests/test_cli_jobs_e2e.py` | `cli.main(["jobs", ...])` e2e | Create |

All tests inherit the autouse `isolated_tutor_home` fixture from `tests/conftest.py` (tmp `PHANTOM_TUTOR_HOME` + stub LLM) — no extra setup needed for data-root isolation.

---

## Task 1: Data-root paths for jobs + operator profile

**Files:**
- Modify: `phantom_tutor/paths.py`
- Test: `tests/test_paths.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_paths.py`:

```python
def test_jobs_and_profile_paths_live_under_data_root(tmp_path, monkeypatch):
    monkeypatch.setenv("PHANTOM_TUTOR_HOME", str(tmp_path / "t"))
    assert paths.jobs_path() == tmp_path / "t" / "jobs.json"
    assert paths.operator_profile_path() == tmp_path / "t" / "operator_skills.json"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_paths.py::test_jobs_and_profile_paths_live_under_data_root -v`
Expected: FAIL with `AttributeError: module 'phantom_tutor.paths' has no attribute 'jobs_path'`

- [ ] **Step 3: Write minimal implementation**

In `phantom_tutor/paths.py`, after `attempts_path()`:

```python
def jobs_path() -> Path:
    return data_root() / "jobs.json"


def operator_profile_path() -> Path:
    return data_root() / "operator_skills.json"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_paths.py -v`
Expected: PASS (all paths tests)

- [ ] **Step 5: Commit**

```bash
git add phantom_tutor/paths.py tests/test_paths.py
git commit -m "feat(paths): add jobs_path + operator_profile_path under data_root"
```

---

## Task 2: wealth_score — four-axis pure scorer

**Files:**
- Create: `phantom_tutor/wealth.py`
- Test: `tests/test_wealth.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_wealth.py`:

```python
from phantom_tutor import wealth


def _job(**kw):
    base = {"title": "", "skills_norm": [], "themes": [],
            "salary_hi": 0, "salary_disclosed": False,
            "match_score": 0.0, "company_tier": "small"}
    base.update(kw)
    return base


def test_platform_governance_job_maxes_w1_w2():
    s = wealth.wealth_score(_job(themes=["agent", "platform", "governance"],
                                 salary_hi=120000, salary_disclosed=True,
                                 match_score=80, company_tier="big"))
    assert s["w1"] == 5   # agent/platform/governance
    assert s["w2"] == 5   # platform/governance
    assert s["w3"] == 5   # 120k*14 = 1.68M annual >= 1.6M
    assert s["w4"] == 5   # match>=60 and big


def test_rag_app_job_scores_mid_w1_w2():
    s = wealth.wealth_score(_job(themes=["rag", "application"], match_score=40))
    assert s["w1"] == 3   # rag
    assert s["w2"] == 3   # application


def test_traditional_job_scores_low():
    s = wealth.wealth_score(_job(themes=["cv"], match_score=10))
    assert s["w1"] == 1
    assert s["w2"] == 1
    assert s["w3"] == 1   # undisclosed salary
    assert s["w4"] == 1


def test_salary_bands():
    def w3(hi):
        return wealth.wealth_score(_job(salary_hi=hi, salary_disclosed=True))["w3"]
    assert w3(120000) == 5   # 1.68M >= 1.6M
    assert w3(80000) == 4    # 1.12M in [1.0M,1.6M)
    assert w3(60000) == 2    # 0.84M in [0.8M,1.0M)
    assert w3(40000) == 1    # 0.56M < 0.8M
    assert wealth.wealth_score(_job(salary_hi=999999999))["w3"] == 1  # undisclosed default


def test_weighted_score_formula():
    s = wealth.wealth_score(_job(themes=["agent"], salary_hi=120000,
                                 salary_disclosed=True, match_score=80,
                                 company_tier="big"))
    # 3*5 + 2.5*5 + 2*5 + 2*5 = 47.5
    assert s["score"] == 47.5
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_wealth.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'phantom_tutor.wealth'`

- [ ] **Step 3: Write minimal implementation**

Create `phantom_tutor/wealth.py`:

```python
"""wealth-score — pure four-axis life-wealth objective on top of match_score.
No I/O. score = 3*W1 + 2.5*W2 + 2*W3 + 2*W4 (max 47.5). W1/W2 weighted to
deliberately outweigh raw salary (portfolio leverage + durability beat pay)."""
from __future__ import annotations

W1_HIGH = {"agent", "runtime", "platform", "governance", "mlops", "infra"}
W1_MID = {"llm", "rag"}
W2_HIGH = {"platform", "infra", "system-design", "governance", "architect", "mlops"}
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_wealth.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add phantom_tutor/wealth.py tests/test_wealth.py
git commit -m "feat(wealth): four-axis wealth_score pure function"
```

---

## Task 3: wealth.rank — switch-target ranking

**Files:**
- Modify: `phantom_tutor/wealth.py`
- Test: `tests/test_wealth.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_wealth.py`:

```python
def test_rank_puts_platform_above_pure_high_salary_app():
    platform = _job(title="platform", themes=["platform", "governance"],
                    salary_hi=90000, salary_disclosed=True, match_score=70,
                    company_tier="big")
    pay_app = _job(title="app", themes=["rag", "application"],
                   salary_hi=200000, salary_disclosed=True, match_score=70,
                   company_tier="big")
    ranked = wealth.rank([pay_app, platform])
    assert ranked[0]["title"] == "platform"           # W1/W2 asymmetry wins
    assert ranked[0]["wealth"]["score"] >= ranked[1]["wealth"]["score"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_wealth.py::test_rank_puts_platform_above_pure_high_salary_app -v`
Expected: FAIL with `AttributeError: module 'phantom_tutor.wealth' has no attribute 'rank'`

- [ ] **Step 3: Write minimal implementation**

Append to `phantom_tutor/wealth.py`:

```python
def rank(jobs: list[dict]) -> list[dict]:
    """Each job gets a 'wealth' sub-dict; sorted by wealth score descending.
    This is the job-switch target list ('which job to move to')."""
    scored = [{**j, "wealth": wealth_score(j)} for j in jobs]
    return sorted(scored, key=lambda j: j["wealth"]["score"], reverse=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_wealth.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add phantom_tutor/wealth.py tests/test_wealth.py
git commit -m "feat(wealth): rank() switch-target ranking by wealth-score"
```

---

## Task 4: jobs.ingest + load_jobs

**Files:**
- Create: `phantom_tutor/jobs.py`
- Test: `tests/test_jobs.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_jobs.py`:

```python
import json

from phantom_tutor import jobs, paths


def _write_src(tmp_path, records):
    p = tmp_path / "top200.json"
    p.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    return p


def test_ingest_dedups_by_job_id_and_filters_agency(tmp_path):
    src = _write_src(tmp_path, [
        {"job_id": "a", "title": "A", "company_tier": "big"},
        {"job_id": "a", "title": "A-dup", "company_tier": "big"},   # dup -> dropped
        {"job_id": "b", "title": "B", "company_tier": "agency"},    # agency -> dropped
        {"job_id": "c", "title": "C", "company_tier": "mid"},
    ])
    out = jobs.ingest(str(src))
    ids = sorted(j["job_id"] for j in out)
    assert ids == ["a", "c"]
    # persisted to data_root
    assert paths.jobs_path().exists()
    assert sorted(j["job_id"] for j in jobs.load_jobs()) == ["a", "c"]


def test_load_jobs_missing_returns_empty():
    assert jobs.load_jobs() == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_jobs.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'phantom_tutor.jobs'`

- [ ] **Step 3: Write minimal implementation**

Create `phantom_tutor/jobs.py`:

```python
"""jobs data layer: ingest target postings, compute skill demand, seed weak_spots
from demand-supply gaps, and surface side-hustle (sellable) skills. All data lives
under paths.data_root() and never enters the repo."""
from __future__ import annotations

import json

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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_jobs.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add phantom_tutor/jobs.py tests/test_jobs.py
git commit -m "feat(jobs): ingest (dedup + agency filter) + load_jobs"
```

---

## Task 5: jobs.demand — skill frequency

**Files:**
- Modify: `phantom_tutor/jobs.py`
- Test: `tests/test_jobs.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_jobs.py`:

```python
def test_demand_counts_skills_and_themes_descending():
    js = [
        {"job_id": "1", "skills_norm": ["python", "llm"], "themes": ["agent"]},
        {"job_id": "2", "skills_norm": ["python"], "themes": ["agent", "mlops"]},
        {"job_id": "3", "skills_norm": ["llm"], "themes": []},
    ]
    d = jobs.demand(js)
    assert d["python"] == 2
    assert d["agent"] == 2
    assert d["llm"] == 2
    assert d["mlops"] == 1
    # descending by count
    assert list(d.values()) == sorted(d.values(), reverse=True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_jobs.py::test_demand_counts_skills_and_themes_descending -v`
Expected: FAIL with `AttributeError: module 'phantom_tutor.jobs' has no attribute 'demand'`

- [ ] **Step 3: Write minimal implementation**

Add `from collections import Counter` to the imports of `phantom_tutor/jobs.py`, then append:

```python
def demand(jobs: list[dict]) -> dict[str, int]:
    """Frequency of each skill/theme across all jobs, descending by count."""
    c: Counter[str] = Counter()
    for j in jobs:
        c.update(j.get("skills_norm", []))
        c.update(j.get("themes", []))
    return dict(c.most_common())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_jobs.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add phantom_tutor/jobs.py tests/test_jobs.py
git commit -m "feat(jobs): demand() skill/theme frequency"
```

---

## Task 6: jobs._coverage + load_profile + seed_weak_spots (gap)

**Files:**
- Modify: `phantom_tutor/jobs.py`
- Test: `tests/test_jobs.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_jobs.py`:

```python
from phantom_tutor import memory


def test_coverage_three_branches():
    profile = {"has_skills": ["python"], "weak_or_missing": ["mlops"]}
    assert jobs._coverage("python", profile) == 0.7
    assert jobs._coverage("mlops", profile) == 0.0
    assert jobs._coverage("unknown", profile) == 0.4


def test_seed_weak_spots_seeds_highest_gap_first_into_memory():
    js = [
        {"job_id": "1", "skills_norm": [], "themes": ["mlops", "mlops", "python"]},
        {"job_id": "2", "skills_norm": [], "themes": ["mlops", "python"]},
    ]
    profile = {"has_skills": ["python"], "weak_or_missing": ["mlops"]}
    seeded = jobs.seed_weak_spots(js, profile, "2026-06-21", top_n=5)
    # mlops: demand 3, coverage 0 -> priority 3 ; python: demand 2, cov .7 -> .6
    assert seeded[0]["topic"] == "mlops"
    # written to the weak_spots spine, due today (score 1-coverage=1.0 -> passes,
    # but first interval seeds FIRST_INTERVAL days out; mlops score=1.0)
    keys = [w["key"] for w in memory.list_weak()]
    assert "mlops" in keys and "python" in keys
    # dimension tag
    assert all(s["dimension"] == "job-gap" for s in seeded)


def test_load_profile_missing_returns_empty_lists():
    p = jobs.load_profile()
    assert p == {"has_skills": [], "weak_or_missing": []}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_jobs.py::test_coverage_three_branches -v`
Expected: FAIL with `AttributeError: module 'phantom_tutor.jobs' has no attribute '_coverage'`

- [ ] **Step 3: Write minimal implementation**

Add `from . import memory, paths` (extend the existing paths import) to `phantom_tutor/jobs.py`, then append:

```python
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
    Top-N gaps get a record_attempt(score=1-coverage) so `tutor today` surfaces
    the most worth-training skills weakest-first. Returns the seeded records."""
    d = demand(jobs)
    scored = sorted(
        ((skill, freq, _coverage(skill, profile)) for skill, freq in d.items()),
        key=lambda t: t[1] * (1 - t[2]), reverse=True,
    )
    seeded: list[dict] = []
    for skill, _freq, cov in scored[:top_n]:
        rec = memory.record_attempt(skill, "job-gap", round(1 - cov, 4), now_iso,
                                    topic=skill)
        seeded.append(rec)
    return seeded
```

> Replace the existing `from . import paths` line with `from . import memory, paths`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_jobs.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add phantom_tutor/jobs.py tests/test_jobs.py
git commit -m "feat(jobs): _coverage + load_profile + seed_weak_spots (gap seeding)"
```

---

## Task 7: jobs.side_hustle — sellable skills (demand × coverage)

**Files:**
- Modify: `phantom_tutor/jobs.py`
- Test: `tests/test_jobs.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_jobs.py`:

```python
def test_side_hustle_ranks_strong_in_demand_skills_excludes_real_gaps():
    js = [
        {"job_id": "1", "skills_norm": ["python", "python"], "themes": ["mlops"]},
        {"job_id": "2", "skills_norm": ["python"], "themes": ["mlops"]},
    ]
    profile = {"has_skills": ["python"], "weak_or_missing": ["mlops"]}
    out = jobs.side_hustle(js, profile, top_n=5)
    skills = [r["skill"] for r in out]
    # python: demand 3, coverage .7 -> 2.1 (sellable, top) ; mlops: cov 0 -> 0
    assert skills[0] == "python"
    assert "mlops" not in skills            # real gap -> can't sell -> excluded
    assert out[0]["score"] == round(3 * 0.7, 4)


def test_side_hustle_and_gap_are_symmetric():
    js = [{"job_id": "1", "skills_norm": ["python", "mlops"], "themes": []}]
    profile = {"has_skills": ["python"], "weak_or_missing": ["mlops"]}
    sell = {r["skill"] for r in jobs.side_hustle(js, profile)}
    seeded = jobs.seed_weak_spots(js, profile, "2026-06-21")
    gaps = {s["topic"] for s in seeded}
    assert "python" in sell and "mlops" in gaps    # strong->sell, weak->train
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_jobs.py::test_side_hustle_ranks_strong_in_demand_skills_excludes_real_gaps -v`
Expected: FAIL with `AttributeError: module 'phantom_tutor.jobs' has no attribute 'side_hustle'`

- [ ] **Step 3: Write minimal implementation**

Append to `phantom_tutor/jobs.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_jobs.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add phantom_tutor/jobs.py tests/test_jobs.py
git commit -m "feat(jobs): side_hustle() sellable-skills analysis (demand x coverage)"
```

---

## Task 8: CLI `tutor jobs <action>`

**Files:**
- Modify: `phantom_tutor/cli.py`
- Test: `tests/test_cli_jobs_e2e.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_cli_jobs_e2e.py`:

```python
import json

from phantom_tutor import cli, paths


def _seed_data(tmp_path):
    src = tmp_path / "top200.json"
    src.write_text(json.dumps([
        {"job_id": "p", "title": "platform", "company_tier": "big",
         "skills_norm": ["python"], "themes": ["platform", "governance"],
         "salary_hi": 90000, "salary_disclosed": True, "match_score": 70},
        {"job_id": "x", "title": "agency-noise", "company_tier": "agency",
         "skills_norm": [], "themes": [], "match_score": 0},
    ], ensure_ascii=False), encoding="utf-8")
    paths.operator_profile_path().write_text(
        json.dumps({"has_skills": ["python"], "weak_or_missing": ["mlops"]}),
        encoding="utf-8")
    return src


def test_jobs_ingest_then_rank_and_side_hustle(tmp_path, capsys):
    src = _seed_data(tmp_path)
    assert cli.main(["jobs", "ingest", "--src", str(src)]) == 0
    out = capsys.readouterr().out
    assert "1" in out                      # 1 ingested (agency dropped)

    assert cli.main(["jobs", "rank"]) == 0
    assert "platform" in capsys.readouterr().out

    assert cli.main(["jobs", "side-hustle"]) == 0
    assert "python" in capsys.readouterr().out


def test_jobs_gap_seeds_today(tmp_path, capsys):
    src = _seed_data(tmp_path)
    cli.main(["jobs", "ingest", "--src", str(src)])
    capsys.readouterr()
    assert cli.main(["--now", "2026-06-21", "jobs", "gap"]) == 0
    assert cli.main(["--now", "2026-06-21", "today"]) == 0
    assert "platform" in capsys.readouterr().out or "python" in capsys.readouterr().out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cli_jobs_e2e.py -v`
Expected: FAIL — argparse exits non-zero / SystemExit because `jobs` is not a known subcommand.

- [ ] **Step 3: Write minimal implementation**

In `phantom_tutor/cli.py`, after the `stats` parser line (`sub.add_parser("stats", ...)`), add the `jobs` parser:

```python
    jb = sub.add_parser("jobs", help="job-funnel: ingest/demand/gap/rank/side-hustle")
    jb.add_argument("action",
                    choices=["ingest", "list", "demand", "gap", "rank", "side-hustle"])
    jb.add_argument("--src", help="path to top200-style JSON (for ingest)")
    jb.add_argument("--tier", default=None, help="filter list by company_tier")
    jb.add_argument("--n", type=int, default=10)
```

Then, before the final `return 1` in `main`, add the dispatch block:

```python
    if args.cmd == "jobs":
        from . import jobs, paths, wealth
        if args.action == "ingest":
            out = jobs.ingest(args.src)
            print(f"ingested {len(out)} job(s) -> {paths.jobs_path()}")
            return 0
        data = jobs.load_jobs()
        if args.action == "list":
            for j in data:
                if args.tier and j.get("company_tier") != args.tier:
                    continue
                print(f"  {j.get('job_id',''):12s} [{j.get('company_tier','')}] "
                      f"{j.get('title','')}")
            return 0
        if args.action == "demand":
            for skill, freq in list(jobs.demand(data).items())[:args.n]:
                print(f"  {skill:24s} {freq}")
            return 0
        if args.action == "gap":
            profile = jobs.load_profile()
            for s in jobs.seed_weak_spots(data, profile, now, top_n=args.n):
                print(f"  {s['topic']:24s} mastery={s['mastery']:.2f} (due {s['due']})")
            return 0
        if args.action == "rank":
            for j in wealth.rank(data)[:args.n]:
                w = j["wealth"]
                print(f"  {w['score']:5.1f}  {j.get('title','')}  "
                      f"(W1={w['w1']} W2={w['w2']} W3={w['w3']} W4={w['w4']})")
            return 0
        if args.action == "side-hustle":
            profile = jobs.load_profile()
            for r in jobs.side_hustle(data, profile, top_n=args.n):
                print(f"  {r['skill']:24s} demand={r['demand']} "
                      f"coverage={r['coverage']} score={r['score']}")
            return 0
    return 1
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_cli_jobs_e2e.py -v`
Expected: PASS

- [ ] **Step 5: Run full suite + ruff**

Run: `python -m pytest -q && python -m ruff check .`
Expected: all pass (existing 30 + new tests), ruff clean.

- [ ] **Step 6: Commit**

```bash
git add phantom_tutor/cli.py tests/test_cli_jobs_e2e.py
git commit -m "feat(cli): tutor jobs ingest/list/demand/gap/rank/side-hustle"
```

---

## Task 9: Docs — wire into public doc roadmap

**Files:**
- Modify: `docs/phantom-tutor.md`

- [ ] **Step 1: Update the shipped/roadmap section**

In `docs/phantom-tutor.md`, move wealth-score + `tutor jobs` from "階段一 / 明確尚未建置" into the shipped table (✅), noting: jobs ingest/demand/gap-seeding + four-axis wealth-score (`rank`) + side-hustle analysis (`side-hustle`), all hermetic, data in `data_root()`. Keep py-fsrs / owned-memory backend / governed scraping as still-planned. Update the test count to the new total.

- [ ] **Step 2: Commit**

```bash
git add docs/phantom-tutor.md
git commit -m "docs: mark jobs layer + wealth-score + side-hustle/switch as shipped"
```

---

## Self-Review

**Spec coverage:**
- jobs.py ingest/demand/gap-seeding → Tasks 4, 5, 6 ✓
- wealth.py four-axis + rank (switch) → Tasks 2, 3 ✓
- side-hustle (demand×coverage) → Task 7 ✓
- shared `_coverage` helper → Task 6 ✓
- paths jobs_path/operator_profile_path → Task 1 ✓
- CLI ingest/list/demand/gap/rank/side-hustle → Task 8 ✓
- operator_profile loading → Task 6 (`load_profile`) ✓
- data-root-only persistence, PII-free synthetic fixtures → all tasks use tmp HOME fixture ✓
- acceptance: platform-above-pay (Task 3), side-hustle excludes gaps (Task 7), gap→today (Task 8) ✓

**Type consistency:** `wealth_score` returns `{w1,w2,w3,w4,score}` (Tasks 2,3,8 agree). `side_hustle` returns `{skill,demand,coverage,score}` (Tasks 7,8 agree). `seed_weak_spots` returns memory records with `topic/dimension/mastery/due` (Tasks 6,8 agree). `_coverage(skill, profile)` signature consistent (Tasks 6,7). `demand` returns `dict[str,int]` (Tasks 5,6,7,8).

**Placeholder scan:** No TBD/TODO; every code step has full, self-consistent code.
