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
