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
