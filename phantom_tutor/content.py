"""Load the seed question/problem/design banks from content/<kind>/*.json."""
from __future__ import annotations

import json
from pathlib import Path

_CONTENT = Path(__file__).resolve().parent.parent / "content"


def load_bank(kind: str) -> list[dict]:
    items: list[dict] = []
    for f in sorted((_CONTENT / kind).glob("*.json")):
        items.extend(json.loads(f.read_text(encoding="utf-8")))
    return items


def get_item(kind: str, item_id: str) -> dict:
    for it in load_bank(kind):
        if it["id"] == item_id:
            return it
    raise KeyError(f"no {kind} item {item_id!r}")
