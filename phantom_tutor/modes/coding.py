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
