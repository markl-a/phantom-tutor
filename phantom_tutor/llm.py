"""LLM access via phantom-mesh core. In tests / PHANTOM_TUTOR_STUB_LLM=1 a
deterministic stub is used so everything is hermetic. Prod calls `phantom exec`."""
from __future__ import annotations

import os
import re
import subprocess


def complete(prompt: str, system: str | None = None) -> str:
    if os.environ.get("PHANTOM_TUTOR_STUB_LLM"):
        return _stub(prompt, system)
    cmd = ["phantom", "exec", prompt]
    if system:
        cmd += ["--system", system]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
    return out.stdout.strip()


def _stub(prompt: str, system: str | None) -> str:
    """Deterministic, marker-driven so tests are stable. A grading prompt
    (contains [[GRADE]]) returns a SCORE/FEEDBACK block; [[ASK]] returns a question."""
    if "[[GRADE]]" in prompt:
        # crude deterministic score: longer answers score higher, capped
        ans_len = len(prompt)
        score = min(1.0, round(0.3 + ans_len / 2000.0, 2))
        return f"SCORE: {score}\nFEEDBACK: stub feedback (len={ans_len})."
    if "[[ASK]]" in prompt:
        return "Explain how retrieval-augmented generation grounds an LLM answer."
    return "stub-response"


def parse_grade(text: str) -> tuple[float, str]:
    """Parse a 'SCORE: x\\nFEEDBACK: ...' block. Defaults to (0.0, raw) if malformed."""
    m = re.search(r"SCORE:\s*([0-9]*\.?[0-9]+)", text)
    score = float(m.group(1)) if m else 0.0
    score = max(0.0, min(1.0, score))
    fb = re.search(r"FEEDBACK:\s*(.+)", text, re.S)
    return score, (fb.group(1).strip() if fb else text.strip())
