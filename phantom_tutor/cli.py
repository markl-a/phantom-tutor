"""tutor CLI. Drives the 4 modes + the weak-spots spine. now_iso defaults to today;
--now overrides for deterministic tests."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

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

    demo = sub.add_parser(
        "demo-loop",
        help="write a deterministic synthetic career-learning artifact bundle",
    )
    demo.add_argument("--out", type=Path, required=True)
    demo.add_argument("--now", default=None, help="ISO date override for the bundle")

    plan_demo = sub.add_parser(
        "learning-plan-demo",
        help="derive a deterministic synthetic learning-plan/evidence bundle",
    )
    plan_demo.add_argument("--source", type=Path, required=True)
    plan_demo.add_argument("--out", type=Path, required=True)
    plan_demo.add_argument("--horizon-days", type=int, default=14)

    practice_scenario = sub.add_parser(
        "practice-scenario",
        help="write a deterministic weak-spot to practice evidence bundle",
    )
    practice_scenario.add_argument("--source", type=Path, required=True)
    practice_scenario.add_argument("--out", type=Path, required=True)

    jb = sub.add_parser("jobs",
                        help="job-funnel: import-104/ingest/demand/gap/rank/side-hustle")
    jb.add_argument("action",
                    choices=["import-104", "ingest", "list", "demand", "gap",
                             "rank", "side-hustle"])
    jb.add_argument("--src", help="path to source CSV (import-104) or top200 JSON (ingest)")
    jb.add_argument("--tier", default=None, help="filter list by company_tier")
    jb.add_argument("--n", type=int, default=10)
    jb.add_argument("--top", type=int, default=200, help="top-N to keep (import-104)")

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
    if args.cmd == "demo-loop":
        from .demo_loop import write_synthetic_demo_loop

        path = write_synthetic_demo_loop(out_root=args.out, now=now)
        print(str(path))
        return 0
    if args.cmd == "learning-plan-demo":
        from .learning_plan import write_learning_plan_bundle

        try:
            path = write_learning_plan_bundle(
                source_bundle=args.source,
                out_root=args.out,
                horizon_days=args.horizon_days,
            )
        except (RuntimeError, ValueError) as exc:
            print(f"tutor: {exc}", file=sys.stderr)
            return 1
        print(str(path))
        return 0
    if args.cmd == "practice-scenario":
        from .practice_scenario import write_practice_scenario_bundle

        try:
            path = write_practice_scenario_bundle(
                source_bundle=args.source,
                out_root=args.out,
            )
        except (RuntimeError, ValueError) as exc:
            print(f"tutor: {exc}", file=sys.stderr)
            return 1
        print(str(path))
        return 0
    if args.cmd == "jobs":
        import json

        from . import jobs, paths, sources_104, wealth
        if args.action == "import-104":
            top = sources_104.to_top200(args.src, top_n=args.top)
            out = jobs.ingest_records(top)
            print(f"ingested {len(out)} job(s) from 104 CSV -> {paths.jobs_path()}")
            prof = paths.operator_profile_path()
            if not prof.exists():
                prof.write_text(json.dumps({"has_skills": [], "weak_or_missing": []},
                                           indent=2, ensure_ascii=False), encoding="utf-8")
                print(f"wrote profile template -> {prof} (fill in your skills)")
            return 0
        if args.action == "ingest":
            out = jobs.ingest(args.src)
            print(f"ingested {len(out)} job(s) -> {paths.jobs_path()}")
            return 0
        data = jobs.load_jobs()
        if args.action not in ("ingest", "list") and not data:
            print("No jobs ingested yet — run `tutor jobs ingest --src <file>`.")
            return 0
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


if __name__ == "__main__":
    raise SystemExit(main())
