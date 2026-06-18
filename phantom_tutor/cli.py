"""tutor CLI. Drives the 4 modes + the weak-spots spine. now_iso defaults to today;
--now overrides for deterministic tests."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone

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

    c = sub.add_parser("code", help="coding problem graded by unit tests")
    c.add_argument("--id", required=True)
    c.add_argument("--solution", required=True)

    d = sub.add_parser("design", help="system-design answer graded by LLM rubric")
    d.add_argument("--id", required=True)
    d.add_argument("--answer", required=True)

    args = p.parse_args(argv)
    now = _now(args)

    if args.cmd == "quiz":
        res = knowledge.run_quiz(args.id, args.answer, now)
        print(f"[{res['item']['topic']}] score={res['score']:.2f}  "
              f"mastery={res['record']['mastery']:.2f}  next due {res['record']['due']}")
        return 0
    if args.cmd == "code":
        from .modes import coding
        res = coding.run_code_problem(args.id, args.solution, now)
        r = res["result"]
        print(f"[{res['item']['topic']}] passed={r['passed']}/{r['total']} "
              f"score={r['score']:.2f}  mastery={res['record']['mastery']:.2f}")
        return 0
    if args.cmd == "design":
        from .modes import design
        res = design.run_design(args.id, args.answer, now)
        print(f"[{res['item']['topic']}] score={res['score']:.2f}\nFEEDBACK: {res['feedback']}")
        return 0
    return 1
