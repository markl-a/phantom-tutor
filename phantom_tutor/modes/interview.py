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
