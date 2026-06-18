"""Knowledge mode: grade a free-text answer. Default = keyword overlap (Phase-1,
byte-unchanged). Phase-2 adds an OPTIONAL LLM grading path (use_llm=True) that
scores the free-text answer via llm.complete(...[[GRADE]]) + llm.parse_grade;
the record path is identical either way."""
from __future__ import annotations

from .. import content, llm, memory


def grade_knowledge(item: dict, answer: str) -> float:
    kws = [k.lower() for k in item.get("keywords", [])]
    if not kws:
        return 0.0
    hit = sum(1 for k in kws if k in answer.lower())
    return round(hit / len(kws), 4)


def grade_knowledge_llm(item: dict, answer: str) -> tuple[float, str]:
    """Grade a free-text answer with the LLM (stubbed in tests). Returns (score, feedback)."""
    prompt = (f"Grade this answer to a {item['dimension']} question.\n"
              f"Question: {item['question']}\n"
              f"Reference answer: {item.get('answer', '')}\n"
              f"Candidate answer: {answer}\n"
              f"Score 0-1.\n[[GRADE]]")
    raw = llm.complete(prompt, system="knowledge grader")
    return llm.parse_grade(raw)


def run_quiz(item_id: str, answer: str, now_iso: str, *, use_llm: bool = False) -> dict:
    item = content.get_item("knowledge", item_id)
    if use_llm:
        score, feedback = grade_knowledge_llm(item, answer)
    else:
        score, feedback = grade_knowledge(item, answer), None
    rec = memory.record_attempt(item["topic"], item["dimension"], score, now_iso, topic=item["topic"])
    return {"item": item, "score": score, "feedback": feedback, "record": rec}
