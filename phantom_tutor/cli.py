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
    q.add_argument("--llm", action="store_true",
                   help="grade the free-text answer via the LLM instead of keyword overlap")

    c = sub.add_parser("code", help="coding problem graded by unit tests")
    c.add_argument("--id", required=True)
    c.add_argument("--solution", required=True)

    d = sub.add_parser("design", help="system-design answer graded by LLM rubric")
    d.add_argument("--id", required=True)
    d.add_argument("--answer", required=True)

    iv = sub.add_parser("interview", help="LLM mock interviewer (reads your weak spots)")
    iv.add_argument("--focus", default="general")
    iv.add_argument("--answer", required=True)
    iv.add_argument("--turns", type=int, default=1,
                    help="run an N-turn mock interview (>1 = multi-turn follow-ups)")

    sub.add_parser("today", help="what to review now (SRS due, weakest first)")
    wk = sub.add_parser("weak-spots", help="weakest topics")
    wk.add_argument("--n", type=int, default=10)
    sub.add_parser("stats", help="progress summary")

    args = p.parse_args(argv)
    now = _now(args)

    if args.cmd == "quiz":
        res = knowledge.run_quiz(args.id, args.answer, now, use_llm=args.llm)
        print(f"[{res['item']['topic']}] score={res['score']:.2f}  "
              f"mastery={res['record']['mastery']:.2f}  next due {res['record']['due']}")
        if args.llm and res.get("feedback"):
            print(f"FEEDBACK: {res['feedback']}")
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
    if args.cmd == "interview":
        from .modes import interview
        if args.turns <= 1:
            res = interview.run_interview(args.focus, args.answer, now)
            print(f"Q: {res['question']}\nscore={res['score']:.2f}  FEEDBACK: {res['feedback']}")
            return 0
        res = interview.run_interview_session(args.focus, args.answer, now, turns=args.turns)
        for r in res["rounds"]:
            print(f"Q{r['turn']}: {r['question']}")
        print(f"session score={res['score']:.2f}  FEEDBACK: {res['feedback']}")
        return 0
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
    return 1
