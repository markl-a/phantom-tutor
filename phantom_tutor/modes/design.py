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
