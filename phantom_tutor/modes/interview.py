"""Interview mode: LLM acts as a mock interviewer, focused on the user's weakest
topics, grades the answer, records to weak_spots. Phase-1 = single-turn; Phase-2
adds a multi-turn loop (run_interview_session) where the LLM asks a follow-up each
round reading weak_spots, then grades the whole session as one weak_spots record.
Single-turn (turns=1) is byte-unchanged from Phase-1."""
from __future__ import annotations

from .. import llm, memory


def _weak_context() -> str:
    weak = [w["topic"] for w in memory.list_weak(n=3)]
    return f"Candidate's weak topics: {', '.join(weak) or 'none yet'}."


def run_interview(focus: str, answer: str, now_iso: str) -> dict:
    ctx = _weak_context()
    question = llm.complete(f"{ctx}\nAsk one {focus} interview question.\n[[ASK]]",
                            system="interviewer")
    grade_raw = llm.complete(f"Question: {question}\nAnswer: {answer}\n"
                             f"Grade the answer 0-1.\n[[GRADE]]", system="interviewer")
    score, feedback = llm.parse_grade(grade_raw)
    key = f"interview:{focus}"
    rec = memory.record_attempt(key, focus, score, now_iso, topic=key)
    return {"question": question, "score": score, "feedback": feedback, "record": rec}


def run_interview_session(focus: str, answer: str, now_iso: str, turns: int = 1) -> dict:
    """Run an N-turn mock interview. Each round the (stubbed) LLM reads the
    candidate's weak_spots and asks a follow-up; the candidate answers (the same
    non-interactive --answer is reused/echoed across turns in Phase-2). After N
    rounds the whole session is graded and recorded as ONE weak_spots attempt.

    turns<=1 delegates to run_interview so single-turn stays byte-identical to
    Phase-1; this function's result then re-exposes that as a 1-round session."""
    turns = max(1, turns)
    if turns == 1:
        single = run_interview(focus, answer, now_iso)
        return {"focus": focus, "turns": 1, "rounds": [single],
                "score": single["score"], "feedback": single["feedback"],
                "record": single["record"]}

    rounds: list[dict] = []
    for i in range(turns):
        ctx = _weak_context()  # re-read weak_spots each round (follow-up is weak-aware)
        prior = "" if i == 0 else f"Prior answer: {rounds[-1]['answer']}\n"
        question = llm.complete(
            f"{ctx}\n{prior}Round {i + 1}: ask a follow-up {focus} interview "
            f"question that probes the candidate's weak spots.\n[[ASK]]",
            system="interviewer")
        rounds.append({"turn": i + 1, "question": question, "answer": answer})

    transcript = "\n".join(
        f"Q{r['turn']}: {r['question']}\nA{r['turn']}: {r['answer']}" for r in rounds)
    grade_raw = llm.complete(
        f"Grade this {turns}-round {focus} interview as a whole, 0-1.\n"
        f"{transcript}\n[[GRADE]]", system="interviewer")
    score, feedback = llm.parse_grade(grade_raw)
    key = f"interview:{focus}"
    rec = memory.record_attempt(key, focus, score, now_iso, topic=key)
    return {"focus": focus, "turns": turns, "rounds": rounds,
            "score": score, "feedback": feedback, "record": rec}
