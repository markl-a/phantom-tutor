> ARCHIVED 2026-06-19 — frozen historical snapshot; current status lives in [/ROADMAP.md](../../ROADMAP.md)
>
> This Phase-1 plan has fully shipped (merged `14c4cc0`). It is kept for provenance only.

# phantom-tutor Phase-1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Phase-1 MVP of phantom-tutor — a personal study assistant whose 4 practice modes all write to an owned-memory weak-spots spine that an SRS scheduler resurfaces, all reachable from a real `tutor` CLI and proven hermetically.

**Architecture:** A small Python package `phantom_tutor/` standing on phantom-mesh core. A `weak_spots` JSON store (interface kept swappable for Phase-2 phantom owned-memory) is the spine; `srs.py` schedules; `llm.py` wraps the core LLM with a deterministic stub for tests; `runner.py` is a sandboxed code-grader; 4 thin `modes/` each grade an attempt and record it; `cli.py` exposes `tutor <today|quiz|code|design|interview|weak-spots|stats>`. Every mode is CLI-reachable and proven by an e2e that drives `main([...])`. All tests hermetic (stub LLM, tmp HOME, never the real `~/.phantom-mesh`).

**Tech Stack:** Python 3.11+, stdlib only (json, subprocess, argparse, datetime, statistics) + pytest + ruff. No numpy/LLM SDK deps in Phase-1.

**Spec:** `docs/2026-06-18-phantom-tutor-design.md`. **Content playbook:** `content/scenarios.md` (already present).

**Anti-fake-green rule (gate enforces):** every mode must be reachable via the real `tutor` CLI and proven by an e2e through `cli.main([...])` (not a library fn in isolation). LLM stubbed via `PHANTOM_TUTOR_STUB_LLM=1`. Tests set `PHANTOM_TUTOR_HOME` to a tmp dir — NEVER touch real `~/.phantom-mesh`.

---

## File Structure

```
phantom_tutor/
  __init__.py          # version
  paths.py             # data_root() — honors PHANTOM_TUTOR_HOME / PHANTOM_HOME, tmp-able
  srs.py               # pure scheduling: next_interval_days(), is_due()
  memory.py            # weak_spots store + record_attempt() + due_topics() + list_weak() (calls srs)
  llm.py               # complete(prompt, system) + deterministic stub via PHANTOM_TUTOR_STUB_LLM
  runner.py            # run_code(solution, tests, timeout) -> {passed,total,score} (sandboxed subprocess)
  content.py           # load_bank(kind) — reads content/<kind>/*.json
  modes/
    __init__.py
    knowledge.py       # grade_knowledge(item, answer) + run via memory
    coding.py          # grade_coding(item, solution) via runner
    design.py          # grade_design(item, answer) via llm
    interview.py       # interview_turn(focus, answer) via llm + weak_spots
  cli.py               # main(argv) — tutor today/quiz/code/design/interview/weak-spots/stats
content/
  knowledge/seed.json  # [{id,topic,dimension,question,answer,keywords}]
  coding/seed.json     # [{id,topic,prompt,tests}]
  design/seed.json     # [{id,topic,prompt,rubric}]
  scenarios.md         # (exists)
tests/
  conftest.py          # autouse tmp PHANTOM_TUTOR_HOME + PHANTOM_TUTOR_STUB_LLM
  test_paths.py  test_srs.py  test_memory.py  test_llm.py  test_runner.py
  test_content.py  test_mode_knowledge_e2e.py  test_mode_coding_e2e.py
  test_mode_design_e2e.py  test_mode_interview_e2e.py  test_cli_today_e2e.py
pyproject.toml
```

---

## Task 1: Package scaffold + paths + conftest

**Files:**
- Create: `pyproject.toml`, `phantom_tutor/__init__.py`, `phantom_tutor/paths.py`, `tests/conftest.py`, `tests/test_paths.py`

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "phantom-tutor"
version = "0.1.0"
description = "Personal study assistant on phantom-mesh core"
requires-python = ">=3.11"

[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
include = ["phantom_tutor*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Write `phantom_tutor/__init__.py`**

```python
__version__ = "0.1.0"
```

- [ ] **Step 3: Write the failing test `tests/test_paths.py`**

```python
import os
from pathlib import Path
from phantom_tutor import paths


def test_data_root_honors_tutor_home(tmp_path, monkeypatch):
    monkeypatch.setenv("PHANTOM_TUTOR_HOME", str(tmp_path / "t"))
    root = paths.data_root()
    assert root == tmp_path / "t"
    assert root.is_dir()  # created


def test_data_root_falls_back_to_phantom_home(tmp_path, monkeypatch):
    monkeypatch.delenv("PHANTOM_TUTOR_HOME", raising=False)
    monkeypatch.setenv("PHANTOM_HOME", str(tmp_path / "ph"))
    assert paths.data_root() == tmp_path / "ph" / "tutor"
```

- [ ] **Step 4: Run it to verify it fails**

Run: `python -m pytest tests/test_paths.py -q`
Expected: FAIL (ModuleNotFoundError: phantom_tutor.paths)

- [ ] **Step 5: Write `phantom_tutor/paths.py`**

```python
"""Data-root resolution. NEVER hardcode ~/.phantom-mesh in callers — go through here."""
from __future__ import annotations

import os
from pathlib import Path


def data_root() -> Path:
    """The tutor data dir. Honors PHANTOM_TUTOR_HOME, else PHANTOM_HOME/tutor,
    else ~/.phantom-mesh/tutor. Created if absent."""
    if os.environ.get("PHANTOM_TUTOR_HOME"):
        p = Path(os.environ["PHANTOM_TUTOR_HOME"])
    elif os.environ.get("PHANTOM_HOME"):
        p = Path(os.environ["PHANTOM_HOME"]) / "tutor"
    else:
        p = Path.home() / ".phantom-mesh" / "tutor"
    p.mkdir(parents=True, exist_ok=True)
    return p


def weak_spots_path() -> Path:
    return data_root() / "weak_spots.json"


def attempts_path() -> Path:
    return data_root() / "attempts.jsonl"
```

- [ ] **Step 6: Write `tests/conftest.py` (autouse isolation — CRITICAL, never touch real HOME)**

```python
import pytest


@pytest.fixture(autouse=True)
def isolated_tutor_home(tmp_path, monkeypatch):
    """Every test gets its own tutor home + stubbed LLM — never the real ~/.phantom-mesh."""
    monkeypatch.setenv("PHANTOM_TUTOR_HOME", str(tmp_path / "tutor"))
    monkeypatch.delenv("PHANTOM_HOME", raising=False)
    monkeypatch.setenv("PHANTOM_TUTOR_STUB_LLM", "1")
    return tmp_path
```

- [ ] **Step 7: Run tests + commit**

Run: `python -m pytest tests/test_paths.py -q` → Expected: PASS (note: the second test sets PHANTOM_TUTOR_HOME via its own monkeypatch overriding the autouse fixture's — verify it deletes PHANTOM_TUTOR_HOME first; if the autouse fixture's env leaks, the test should `monkeypatch.delenv("PHANTOM_TUTOR_HOME", raising=False)` before setting PHANTOM_HOME — add that line to test 2).

```bash
git add pyproject.toml phantom_tutor/__init__.py phantom_tutor/paths.py tests/conftest.py tests/test_paths.py
git commit -m "feat(paths): data-root resolution + autouse test isolation"
```

---

## Task 2: SRS scheduler (pure)

**Files:**
- Create: `phantom_tutor/srs.py`, `tests/test_srs.py`

- [ ] **Step 1: Write the failing test `tests/test_srs.py`**

```python
from phantom_tutor import srs


def test_next_interval_grows_on_pass_and_resets_on_fail():
    # score >= 0.6 grows the interval; below resets to 1 day
    assert srs.next_interval_days(prev_interval=1, score=1.0) > 1
    assert srs.next_interval_days(prev_interval=10, score=0.9) > 10
    assert srs.next_interval_days(prev_interval=10, score=0.3) == 1
    assert srs.next_interval_days(prev_interval=0, score=1.0) >= 1


def test_is_due():
    assert srs.is_due("2026-06-10", "2026-06-12") is True   # past due
    assert srs.is_due("2026-06-12", "2026-06-12") is True   # due today
    assert srs.is_due("2026-06-20", "2026-06-12") is False  # future
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest tests/test_srs.py -q` → Expected: FAIL (no module srs)

- [ ] **Step 3: Write `phantom_tutor/srs.py`**

```python
"""Pure spaced-repetition scheduling (SM-2-lite). No I/O."""
from __future__ import annotations

from datetime import date

PASS_THRESHOLD = 0.6
EASE = 2.0


def next_interval_days(prev_interval: int, score: float) -> int:
    """New review interval in days. Pass (score>=0.6) multiplies the interval
    (min 1 day); fail resets to 1 day."""
    if score < PASS_THRESHOLD:
        return 1
    base = max(prev_interval, 1)
    return max(1, round(base * EASE))


def is_due(due_iso: str, now_iso: str) -> bool:
    """True if due_iso (YYYY-MM-DD) is on or before now_iso."""
    return date.fromisoformat(due_iso) <= date.fromisoformat(now_iso)
```

- [ ] **Step 4: Run + commit**

Run: `python -m pytest tests/test_srs.py -q` → Expected: PASS

```bash
git add phantom_tutor/srs.py tests/test_srs.py
git commit -m "feat(srs): SM-2-lite interval + is_due"
```

---

## Task 3: weak_spots memory store (the spine)

**Files:**
- Create: `phantom_tutor/memory.py`, `tests/test_memory.py`

- [ ] **Step 1: Write the failing test `tests/test_memory.py`**

```python
from phantom_tutor import memory


def test_record_attempt_persists_and_updates_mastery_and_due():
    rec = memory.record_attempt("transformer", "ML", score=0.4, now_iso="2026-06-12")
    assert rec["topic"] == "transformer"
    assert rec["dimension"] == "ML"
    assert rec["attempts"] == 1
    assert rec["due"] == "2026-06-13"   # fail -> 1 day later
    # a pass grows the interval and raises mastery
    rec2 = memory.record_attempt("transformer", "ML", score=1.0, now_iso="2026-06-13")
    assert rec2["attempts"] == 2
    assert rec2["mastery"] > rec["mastery"]
    assert rec2["due"] > "2026-06-14"   # interval grew


def test_due_topics_and_list_weak():
    memory.record_attempt("a", "ML", score=0.2, now_iso="2026-06-10")   # weak, due 06-11
    memory.record_attempt("b", "ML", score=1.0, now_iso="2026-06-10")   # strong, due later
    due = memory.due_topics(now_iso="2026-06-12")
    assert "a" in [d["key"] for d in due]
    assert "b" not in [d["key"] for d in due]   # not yet due
    weak = memory.list_weak(n=1)
    assert weak[0]["key"] == "a"   # weakest first
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest tests/test_memory.py -q` → Expected: FAIL

- [ ] **Step 3: Write `phantom_tutor/memory.py`**

```python
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
    return {"key": key, **rec}


def due_topics(now_iso: str, path: Path | None = None) -> list[dict]:
    """Records due on/before now_iso, weakest (lowest mastery) first."""
    store = load_store(path)
    due = [{"key": k, **v} for k, v in store.items() if srs.is_due(v["due"], now_iso)]
    return sorted(due, key=lambda r: r["mastery"])


def list_weak(n: int | None = None, path: Path | None = None) -> list[dict]:
    store = load_store(path)
    items = sorted(({"key": k, **v} for k, v in store.items()), key=lambda r: r["mastery"])
    return items[:n] if n else items
```

- [ ] **Step 4: Run + commit**

Run: `python -m pytest tests/test_memory.py -q` → Expected: PASS

```bash
git add phantom_tutor/memory.py tests/test_memory.py
git commit -m "feat(memory): weak_spots spine — record_attempt/due_topics/list_weak"
```

---

## Task 4: LLM wrapper + deterministic stub

**Files:**
- Create: `phantom_tutor/llm.py`, `tests/test_llm.py`

- [ ] **Step 1: Write the failing test `tests/test_llm.py`** (the autouse fixture sets PHANTOM_TUTOR_STUB_LLM=1)

```python
from phantom_tutor import llm


def test_stub_is_deterministic_and_parseable():
    # In stub mode the grader prompt yields a deterministic SCORE/FEEDBACK block.
    out = llm.complete("Grade this answer.\n[[GRADE]]", system="grader")
    assert "SCORE:" in out
    score, feedback = llm.parse_grade(out)
    assert 0.0 <= score <= 1.0
    assert isinstance(feedback, str) and feedback


def test_stub_interview_question_marker():
    out = llm.complete("Ask an interview question about RAG.\n[[ASK]]")
    assert out.strip()  # non-empty deterministic question
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest tests/test_llm.py -q` → Expected: FAIL

- [ ] **Step 3: Write `phantom_tutor/llm.py`**

```python
"""LLM access via phantom-mesh core. In tests / PHANTOM_TUTOR_STUB_LLM=1 a
deterministic stub is used so everything is hermetic. Prod calls `phantom exec`."""
from __future__ import annotations

import os
import re
import subprocess


def complete(prompt: str, system: str | None = None) -> str:
    if os.environ.get("PHANTOM_TUTOR_STUB_LLM"):
        return _stub(prompt, system)
    cmd = ["phantom", "exec", prompt]
    if system:
        cmd += ["--system", system]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
    return out.stdout.strip()


def _stub(prompt: str, system: str | None) -> str:
    """Deterministic, marker-driven so tests are stable. A grading prompt
    (contains [[GRADE]]) returns a SCORE/FEEDBACK block; [[ASK]] returns a question."""
    if "[[GRADE]]" in prompt:
        # crude deterministic score: longer answers score higher, capped
        ans_len = len(prompt)
        score = min(1.0, round(0.3 + ans_len / 2000.0, 2))
        return f"SCORE: {score}\nFEEDBACK: stub feedback (len={ans_len})."
    if "[[ASK]]" in prompt:
        return "Explain how retrieval-augmented generation grounds an LLM answer."
    return "stub-response"


def parse_grade(text: str) -> tuple[float, str]:
    """Parse a 'SCORE: x\\nFEEDBACK: ...' block. Defaults to (0.0, raw) if malformed."""
    m = re.search(r"SCORE:\s*([0-9]*\.?[0-9]+)", text)
    score = float(m.group(1)) if m else 0.0
    score = max(0.0, min(1.0, score))
    fb = re.search(r"FEEDBACK:\s*(.+)", text, re.S)
    return score, (fb.group(1).strip() if fb else text.strip())
```

- [ ] **Step 4: Run + commit**

Run: `python -m pytest tests/test_llm.py -q` → Expected: PASS

```bash
git add phantom_tutor/llm.py tests/test_llm.py
git commit -m "feat(llm): core LLM wrapper + deterministic stub + parse_grade"
```

---

## Task 5: Sandboxed code-runner

**Files:**
- Create: `phantom_tutor/runner.py`, `tests/test_runner.py`

- [ ] **Step 1: Write the failing test `tests/test_runner.py`**

```python
from phantom_tutor import runner

SOLUTION_OK = "def add(a, b):\n    return a + b\n"
SOLUTION_BAD = "def add(a, b):\n    return a - b\n"
TESTS = (
    "from solution import add\n"
    "def test_pos():\n    assert add(2, 3) == 5\n"
    "def test_zero():\n    assert add(0, 0) == 0\n"
)


def test_runner_scores_correct_solution_full():
    r = runner.run_code(SOLUTION_OK, TESTS)
    assert r["passed"] == 2 and r["total"] == 2 and r["score"] == 1.0


def test_runner_scores_wrong_solution_low():
    r = runner.run_code(SOLUTION_BAD, TESTS)
    assert r["passed"] == 0 and r["score"] == 0.0


def test_runner_times_out_gracefully():
    r = runner.run_code("import time\ntime.sleep(30)\n", "from solution import x\n", timeout=2)
    assert r["score"] == 0.0  # timeout -> 0, no hang
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest tests/test_runner.py -q` → Expected: FAIL

- [ ] **Step 3: Write `phantom_tutor/runner.py`** (mirror the proven sandbox pattern: tmp dir + subprocess + timeout)

```python
"""Sandboxed code grader: run a candidate solution against pytest-free unit tests
in a subprocess; score = pass-rate. No in-process exec of candidate code."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

_RUNNER = textwrap.dedent("""
    import json
    passed = 0
    total = 0
    try:
        import _tests
        tests = [obj for name, obj in sorted(vars(_tests).items())
                 if name.startswith("test_") and callable(obj)]
        total = len(tests)
        for t in tests:
            try:
                t()
            except Exception:
                pass
            else:
                passed += 1
    except Exception:
        passed = 0
    print(json.dumps({"passed": passed, "total": total}))
""").strip()


def run_code(solution: str, tests: str, timeout: float = 10.0) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "solution.py").write_text(solution, encoding="utf-8")
        (d / "_tests.py").write_text(tests, encoding="utf-8")
        (d / "_runner.py").write_text(_RUNNER, encoding="utf-8")
        try:
            cp = subprocess.run([sys.executable, "_runner.py"], cwd=d,
                                capture_output=True, text=True, timeout=timeout, check=False)
            data = json.loads(cp.stdout.strip().splitlines()[-1])
            passed, total = int(data["passed"]), int(data["total"])
        except (subprocess.TimeoutExpired, OSError, ValueError, json.JSONDecodeError, IndexError):
            passed, total = 0, 0
    score = round(passed / total, 4) if total else 0.0
    return {"passed": passed, "total": total, "score": score}
```

- [ ] **Step 4: Run + commit**

Run: `python -m pytest tests/test_runner.py -q` → Expected: PASS

```bash
git add phantom_tutor/runner.py tests/test_runner.py
git commit -m "feat(runner): sandboxed subprocess code grader (pass-rate)"
```

---

## Task 6: Content banks + loader

**Files:**
- Create: `content/knowledge/seed.json`, `content/coding/seed.json`, `content/design/seed.json`, `phantom_tutor/content.py`, `tests/test_content.py`

- [ ] **Step 1: Write the 3 seed banks**

`content/knowledge/seed.json`:
```json
[
  {"id": "k-softmax", "topic": "softmax", "dimension": "ML", "question": "Why subtract max(x) before exp in softmax?", "answer": "numerical stability", "keywords": ["stability", "overflow", "max"]},
  {"id": "k-rag", "topic": "rag", "dimension": "LLM", "question": "What problem does RAG address?", "answer": "grounding/hallucination via retrieval", "keywords": ["retrieval", "grounding", "hallucination", "context"]}
]
```

`content/coding/seed.json`:
```json
[
  {"id": "c-add", "topic": "basics", "prompt": "Implement add(a, b) returning a+b.", "tests": "from solution import add\ndef test_a():\n    assert add(2,3)==5\ndef test_b():\n    assert add(-1,1)==0\n"},
  {"id": "c-softmax", "topic": "softmax", "prompt": "Implement softmax(xs) (list of floats) -> list summing to 1.", "tests": "from solution import softmax\ndef test_sum():\n    assert abs(sum(softmax([1.0,2.0,3.0]))-1.0)<1e-6\n"}
]
```

`content/design/seed.json`:
```json
[
  {"id": "d-rag", "topic": "rag-system", "dimension": "system-design", "prompt": "Design a RAG assistant over a company wiki.", "rubric": ["data/ingestion+chunking", "embeddings+retrieval+rerank", "serving/latency", "eval+monitoring"]}
]
```

- [ ] **Step 2: Write the failing test `tests/test_content.py`**

```python
from phantom_tutor import content


def test_load_bank_reads_seed():
    items = content.load_bank("knowledge")
    assert any(i["id"] == "k-softmax" for i in items)
    cod = content.load_bank("coding")
    assert any("tests" in i for i in cod)


def test_get_item_by_id():
    item = content.get_item("coding", "c-add")
    assert item["prompt"].startswith("Implement add")
```

- [ ] **Step 3: Run to verify fail**

Run: `python -m pytest tests/test_content.py -q` → Expected: FAIL

- [ ] **Step 4: Write `phantom_tutor/content.py`**

```python
"""Load the seed question/problem/design banks from content/<kind>/*.json."""
from __future__ import annotations

import json
from pathlib import Path

_CONTENT = Path(__file__).resolve().parent.parent / "content"


def load_bank(kind: str) -> list[dict]:
    items: list[dict] = []
    for f in sorted((_CONTENT / kind).glob("*.json")):
        items.extend(json.loads(f.read_text(encoding="utf-8")))
    return items


def get_item(kind: str, item_id: str) -> dict:
    for it in load_bank(kind):
        if it["id"] == item_id:
            return it
    raise KeyError(f"no {kind} item {item_id!r}")
```

- [ ] **Step 5: Run + commit**

Run: `python -m pytest tests/test_content.py -q` → Expected: PASS

```bash
git add content/ phantom_tutor/content.py tests/test_content.py
git commit -m "feat(content): seed banks + loader"
```

---

## Task 7: knowledge mode + e2e through CLI

> NOTE: cli.py is introduced here (minimal) and extended in later tasks. Build it incrementally.

**Files:**
- Create: `phantom_tutor/modes/__init__.py`, `phantom_tutor/modes/knowledge.py`, `phantom_tutor/cli.py`, `tests/test_mode_knowledge_e2e.py`

- [ ] **Step 1: Write `phantom_tutor/modes/__init__.py`** (empty) and the failing e2e `tests/test_mode_knowledge_e2e.py`

```python
from phantom_tutor.cli import main
from phantom_tutor import memory


def test_quiz_grades_keyword_answer_and_records_weakspot(capsys):
    # answer containing a keyword scores a pass; recorded to weak_spots
    rc = main(["quiz", "--id", "k-softmax", "--answer", "subtract the max for numerical stability"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "softmax" in out.lower()
    store = memory.load_store()
    assert "softmax" in store and store["softmax"]["attempts"] == 1
    assert store["softmax"]["mastery"] > 0  # keyword hit -> positive score


def test_quiz_wrong_answer_records_low(capsys):
    rc = main(["quiz", "--id", "k-softmax", "--answer", "no idea"])
    assert rc == 0
    store = memory.load_store()
    assert store["softmax"]["mastery"] == 0.0  # no keyword -> 0
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest tests/test_mode_knowledge_e2e.py -q` → Expected: FAIL (no cli)

- [ ] **Step 3: Write `phantom_tutor/modes/knowledge.py`**

```python
"""Knowledge mode: grade a free-text answer by keyword overlap (Phase-1).
Phase-2 swaps in llm grading; the record path is identical."""
from __future__ import annotations

from .. import content, memory


def grade_knowledge(item: dict, answer: str) -> float:
    kws = [k.lower() for k in item.get("keywords", [])]
    if not kws:
        return 0.0
    hit = sum(1 for k in kws if k in answer.lower())
    return round(hit / len(kws), 4)


def run_quiz(item_id: str, answer: str, now_iso: str) -> dict:
    item = content.get_item("knowledge", item_id)
    score = grade_knowledge(item, answer)
    rec = memory.record_attempt(item["topic"], item["dimension"], score, now_iso, topic=item["topic"])
    return {"item": item, "score": score, "record": rec}
```

- [ ] **Step 4: Write minimal `phantom_tutor/cli.py` with the `quiz` subcommand**

```python
"""tutor CLI. Drives the 4 modes + the weak-spots spine. now_iso defaults to today;
--now overrides for deterministic tests."""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone

from . import memory
from .modes import knowledge


def _now(args) -> str:
    return args.now or datetime.now(timezone.utc).date().isoformat()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="tutor")
    p.add_argument("--now", default=None, help="ISO date override (tests)")
    sub = p.add_subparsers(dest="cmd", required=True)

    q = sub.add_parser("quiz", help="knowledge SRS quiz")
    q.add_argument("--id", required=True)
    q.add_argument("--answer", required=True)

    args = p.parse_args(argv)
    now = _now(args)

    if args.cmd == "quiz":
        res = knowledge.run_quiz(args.id, args.answer, now)
        print(f"[{res['item']['topic']}] score={res['score']:.2f}  "
              f"mastery={res['record']['mastery']:.2f}  next due {res['record']['due']}")
        return 0
    return 1
```

- [ ] **Step 5: Run + commit**

Run: `python -m pytest tests/test_mode_knowledge_e2e.py -q` → Expected: PASS

```bash
git add phantom_tutor/modes/__init__.py phantom_tutor/modes/knowledge.py phantom_tutor/cli.py tests/test_mode_knowledge_e2e.py
git commit -m "feat(knowledge): quiz mode + tutor quiz CLI + e2e"
```

---

## Task 8: coding mode + e2e

**Files:**
- Create: `phantom_tutor/modes/coding.py`, `tests/test_mode_coding_e2e.py`; Modify: `phantom_tutor/cli.py`

- [ ] **Step 1: Write the failing e2e `tests/test_mode_coding_e2e.py`**

```python
from phantom_tutor.cli import main
from phantom_tutor import memory

GOOD = "def add(a, b):\n    return a + b\n"
BAD = "def add(a, b):\n    return a - b\n"


def test_code_grades_solution_file_through_runner(tmp_path, capsys):
    sol = tmp_path / "sol.py"
    sol.write_text(GOOD, encoding="utf-8")
    rc = main(["code", "--id", "c-add", "--solution", str(sol)])
    assert rc == 0
    assert "score=1.00" in capsys.readouterr().out
    assert memory.load_store()["basics"]["mastery"] > 0


def test_code_wrong_solution_low(tmp_path):
    sol = tmp_path / "sol.py"
    sol.write_text(BAD, encoding="utf-8")
    rc = main(["code", "--id", "c-add", "--solution", str(sol)])
    assert rc == 0
    assert memory.load_store()["basics"]["mastery"] == 0.0
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest tests/test_mode_coding_e2e.py -q` → Expected: FAIL

- [ ] **Step 3: Write `phantom_tutor/modes/coding.py`**

```python
"""Coding mode: grade a solution file against the problem's unit tests via the sandbox runner."""
from __future__ import annotations

from pathlib import Path

from .. import content, memory, runner


def run_code_problem(item_id: str, solution_path: str, now_iso: str) -> dict:
    item = content.get_item("coding", item_id)
    solution = Path(solution_path).read_text(encoding="utf-8")
    result = runner.run_code(solution, item["tests"])
    rec = memory.record_attempt(item["topic"], item.get("dimension", "coding"),
                                result["score"], now_iso, topic=item["topic"])
    return {"item": item, "result": result, "record": rec}
```

- [ ] **Step 4: Add the `code` subcommand to `phantom_tutor/cli.py`** (inside main, after the quiz block; and add the parser)

```python
    c = sub.add_parser("code", help="coding problem graded by unit tests")
    c.add_argument("--id", required=True)
    c.add_argument("--solution", required=True)
```
```python
    if args.cmd == "code":
        from .modes import coding
        res = coding.run_code_problem(args.id, args.solution, now)
        r = res["result"]
        print(f"[{res['item']['topic']}] passed={r['passed']}/{r['total']} "
              f"score={r['score']:.2f}  mastery={res['record']['mastery']:.2f}")
        return 0
```

- [ ] **Step 5: Run + commit**

Run: `python -m pytest tests/test_mode_coding_e2e.py -q` → Expected: PASS

```bash
git add phantom_tutor/modes/coding.py phantom_tutor/cli.py tests/test_mode_coding_e2e.py
git commit -m "feat(coding): code mode via sandbox runner + tutor code CLI + e2e"
```

---

## Task 9: design mode + e2e (LLM-graded, stubbed)

**Files:**
- Create: `phantom_tutor/modes/design.py`, `tests/test_mode_design_e2e.py`; Modify: `phantom_tutor/cli.py`

- [ ] **Step 1: Write the failing e2e `tests/test_mode_design_e2e.py`**

```python
from phantom_tutor.cli import main
from phantom_tutor import memory


def test_design_grades_answer_via_stub_llm_and_records(tmp_path, capsys):
    ans = tmp_path / "ans.txt"
    ans.write_text("ingestion + chunking, embeddings + retrieval + rerank, serving latency, eval", encoding="utf-8")
    rc = main(["design", "--id", "d-rag", "--answer", str(ans)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "score=" in out and "FEEDBACK" in out.upper()
    assert "rag-system" in memory.load_store()
```

- [ ] **Step 2: Run to verify fail** → FAIL

- [ ] **Step 3: Write `phantom_tutor/modes/design.py`**

```python
"""System-design mode: LLM grades the answer against the problem rubric (stubbed in tests)."""
from __future__ import annotations

from pathlib import Path

from .. import content, llm, memory


def run_design(item_id: str, answer_path: str, now_iso: str) -> dict:
    item = content.get_item("design", item_id)
    answer = Path(answer_path).read_text(encoding="utf-8")
    rubric = "; ".join(item.get("rubric", []))
    prompt = (f"Grade this system-design answer against the rubric [{rubric}].\n"
              f"Answer:\n{answer}\n[[GRADE]]")
    raw = llm.complete(prompt, system="system-design grader")
    score, feedback = llm.parse_grade(raw)
    rec = memory.record_attempt(item["topic"], item.get("dimension", "system-design"),
                                score, now_iso, topic=item["topic"])
    return {"item": item, "score": score, "feedback": feedback, "record": rec}
```

- [ ] **Step 4: Add the `design` subcommand to `cli.py`**

```python
    d = sub.add_parser("design", help="system-design answer graded by LLM rubric")
    d.add_argument("--id", required=True)
    d.add_argument("--answer", required=True)
```
```python
    if args.cmd == "design":
        from .modes import design
        res = design.run_design(args.id, args.answer, now)
        print(f"[{res['item']['topic']}] score={res['score']:.2f}\nFEEDBACK: {res['feedback']}")
        return 0
```

- [ ] **Step 5: Run + commit** → PASS

```bash
git add phantom_tutor/modes/design.py phantom_tutor/cli.py tests/test_mode_design_e2e.py
git commit -m "feat(design): system-design mode (LLM-graded) + tutor design CLI + e2e"
```

---

## Task 10: interview mode + e2e (LLM interviewer reads weak_spots)

**Files:**
- Create: `phantom_tutor/modes/interview.py`, `tests/test_mode_interview_e2e.py`; Modify: `phantom_tutor/cli.py`

- [ ] **Step 1: Write the failing e2e `tests/test_mode_interview_e2e.py`**

```python
from phantom_tutor.cli import main
from phantom_tutor import memory


def test_interview_asks_grades_and_records(capsys):
    # seed a weak spot so the interviewer has context to focus on
    memory.record_attempt("rag", "LLM", score=0.2, now_iso="2026-06-10", topic="rag")
    rc = main(["interview", "--focus", "LLM", "--answer", "RAG retrieves docs and grounds the answer"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Q:" in out and "score=" in out      # asked a question + graded the answer
    assert memory.load_store()["interview:LLM"]["attempts"] >= 1
```

- [ ] **Step 2: Run to verify fail** → FAIL

- [ ] **Step 3: Write `phantom_tutor/modes/interview.py`**

```python
"""Interview mode: LLM asks a question (focused on the user's weakest topics),
grades the answer, records to weak_spots. Single-turn in Phase-1 (multi-turn = Phase-2)."""
from __future__ import annotations

from .. import llm, memory


def run_interview(focus: str, answer: str, now_iso: str) -> dict:
    weak = [w["topic"] for w in memory.list_weak(n=3)]
    ctx = f"Candidate's weak topics: {', '.join(weak) or 'none yet'}."
    question = llm.complete(f"{ctx}\nAsk one {focus} interview question.\n[[ASK]]",
                            system="interviewer")
    grade_raw = llm.complete(f"Question: {question}\nAnswer: {answer}\n"
                             f"Grade the answer 0-1.\n[[GRADE]]", system="interviewer")
    score, feedback = llm.parse_grade(grade_raw)
    key = f"interview:{focus}"
    rec = memory.record_attempt(key, focus, score, now_iso, topic=key)
    return {"question": question, "score": score, "feedback": feedback, "record": rec}
```

- [ ] **Step 4: Add the `interview` subcommand to `cli.py`**

```python
    iv = sub.add_parser("interview", help="LLM mock interviewer (reads your weak spots)")
    iv.add_argument("--focus", default="general")
    iv.add_argument("--answer", required=True)
```
```python
    if args.cmd == "interview":
        from .modes import interview
        res = interview.run_interview(args.focus, args.answer, now)
        print(f"Q: {res['question']}\nscore={res['score']:.2f}  FEEDBACK: {res['feedback']}")
        return 0
```

- [ ] **Step 5: Run + commit** → PASS

```bash
git add phantom_tutor/modes/interview.py phantom_tutor/cli.py tests/test_mode_interview_e2e.py
git commit -m "feat(interview): mock interviewer reads weak_spots + tutor interview CLI + e2e"
```

---

## Task 11: `tutor today` + `weak-spots` + `stats` + the daily loop e2e

**Files:**
- Modify: `phantom_tutor/cli.py`; Create: `tests/test_cli_today_e2e.py`

- [ ] **Step 1: Write the failing e2e `tests/test_cli_today_e2e.py`**

```python
from phantom_tutor.cli import main


def test_today_lists_due_weakest_first(capsys):
    # two weak spots due, one strong/not-due
    main(["--now", "2026-06-10", "quiz", "--id", "k-softmax", "--answer", "no idea"])   # weak
    main(["--now", "2026-06-10", "quiz", "--id", "k-rag", "--answer", "retrieval grounding hallucination context"])  # strong
    out = capsys.readouterr().out  # drain
    rc = main(["--now", "2026-06-12", "today"])
    assert rc == 0
    body = capsys.readouterr().out
    assert "softmax" in body          # weak one is due + surfaced
    assert "Due:" in body or "due" in body.lower()


def test_weak_spots_and_stats(capsys):
    main(["--now", "2026-06-10", "quiz", "--id", "k-softmax", "--answer", "no idea"])
    capsys.readouterr()
    assert main(["weak-spots"]) == 0
    assert "softmax" in capsys.readouterr().out
    assert main(["stats"]) == 0
    assert "attempts" in capsys.readouterr().out.lower()
```

- [ ] **Step 2: Run to verify fail** → FAIL

- [ ] **Step 3: Add `today`, `weak-spots`, `stats` subcommands to `cli.py`**

```python
    sub.add_parser("today", help="what to review now (SRS due, weakest first)")
    wk = sub.add_parser("weak-spots", help="weakest topics")
    wk.add_argument("--n", type=int, default=10)
    sub.add_parser("stats", help="progress summary")
```
```python
    if args.cmd == "today":
        due = memory.due_topics(now)
        if not due:
            print("Nothing due — you're caught up. Try `tutor quiz` or `tutor interview`.")
            return 0
        print(f"Due: {len(due)} topic(s), weakest first:")
        for d in due:
            print(f"  - {d['topic']} [{d['dimension']}] mastery={d['mastery']:.2f} (due {d['due']})")
        return 0
    if args.cmd == "weak-spots":
        for w in memory.list_weak(n=args.n):
            print(f"  {w['topic']:24s} mastery={w['mastery']:.2f} attempts={w['attempts']}")
        return 0
    if args.cmd == "stats":
        store = memory.load_store()
        total = sum(r["attempts"] for r in store.values())
        avg = round(sum(r["mastery"] for r in store.values()) / len(store), 3) if store else 0.0
        print(f"topics={len(store)}  attempts={total}  avg_mastery={avg}")
        return 0
```

- [ ] **Step 4: Run the FULL suite + commit**

Run: `python -m pytest -q` → Expected: all PASS
Run: `ruff check .` → Expected: clean

```bash
git add phantom_tutor/cli.py tests/test_cli_today_e2e.py
git commit -m "feat(cli): tutor today/weak-spots/stats + daily-loop e2e"
```

---

## Task 12: README + ship-check

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update `README.md`** with Phase-1 usage

```markdown
## Phase-1 usage (hermetic, LLM-stubbed by default in dev)

    tutor quiz --id k-softmax --answer "subtract max for numerical stability"
    tutor code --id c-add --solution my_add.py
    tutor design --id d-rag --answer my_answer.txt
    tutor interview --focus LLM --answer "RAG retrieves and grounds the answer"
    tutor today          # SRS-due topics, weakest first
    tutor weak-spots     # your weakest topics
    tutor stats          # progress

Modes write to the weak_spots spine (`$PHANTOM_TUTOR_HOME/weak_spots.json`); SRS resurfaces
the weak/due ones via `tutor today`. LLM goes through `phantom exec` (set
`PHANTOM_TUTOR_STUB_LLM=1` for offline/dev). Phase-2: real owned-memory backend, deeper
modes, multi-turn interview, governor/mesh. See `docs/2026-06-18-phantom-tutor-design.md`.
```

- [ ] **Step 2: Final full-suite + lint + commit**

Run: `python -m pytest -q` (all green) ; `ruff check .` (clean)

```bash
git add README.md
git commit -m "docs(readme): Phase-1 usage"
```

---

## Self-Review checklist (done)

- **Spec coverage:** ② weak_spots spine (Task 3) + SRS (Task 2); ④-style hermetic gate (every mode e2e); 4 modes (Tasks 7-10); `tutor today` daily loop (Task 11); content layer (Task 6 + existing scenarios.md); core LLM via stub/`phantom exec` (Task 4); sandbox runner (Task 5). Phase-2 items (real owned-memory, governor, multi-turn, deeper banks) explicitly deferred.
- **Type consistency:** `memory.record_attempt(key, dimension, score, now_iso, *, topic=, path=)` used consistently in all modes; `llm.complete()/parse_grade()` consistent; `runner.run_code()->{passed,total,score}` consistent; `content.get_item(kind,id)` consistent.
- **No placeholders:** every step has real code + exact commands.
- **Anti-fake-green:** each mode proven by an e2e through `cli.main([...])` writing to the real weak_spots store; LLM stubbed; tmp HOME (autouse conftest) — never real `~/.phantom-mesh`.
