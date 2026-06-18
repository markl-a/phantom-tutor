"""Phase-2: assert the expanded seed banks load + every item has the required
fields, every topic is unique (the weak_spots store is keyed on topic), and every
coding problem's tests reference `from solution import ...` so the runner can grade them."""
from phantom_tutor import content


def test_knowledge_bank_has_genuine_breadth():
    items = content.load_bank("knowledge")
    assert len(items) >= 10  # >=8 new + the 2 Phase-1 seeds
    topics = [i["topic"] for i in items]
    assert len(topics) == len(set(topics)), "topics must be unique (store is keyed on topic)"
    for it in items:
        for field in ("id", "topic", "dimension", "question", "answer", "keywords"):
            assert field in it, f"knowledge item {it.get('id')} missing {field}"
        assert it["keywords"], f"knowledge item {it['id']} has empty keywords"
    # genuine AI-engineer coverage across ML/DL + LLM/RAG/eval/fine-tune dimensions
    dims = {i["dimension"] for i in items}
    assert {"ML", "LLM"} <= dims


def test_coding_bank_problems_are_runnable():
    items = content.load_bank("coding")
    assert len(items) >= 6  # >=4 new + the 2 Phase-1 seeds
    ids = [i["id"] for i in items]
    assert len(ids) == len(set(ids)), "ids must be unique"
    topics = [i["topic"] for i in items]
    assert len(topics) == len(set(topics)), "topics must be unique (store is keyed on topic)"
    for it in items:
        for field in ("id", "topic", "prompt", "tests"):
            assert field in it, f"coding item {it.get('id')} missing {field}"
        assert "from solution import" in it["tests"], \
            f"coding item {it['id']} tests must import from solution"
        assert "def test_" in it["tests"], f"coding item {it['id']} has no test_ functions"


def test_design_bank_has_rubrics():
    items = content.load_bank("design")
    assert len(items) >= 4  # >=3 new + the 1 Phase-1 seed
    topics = [i["topic"] for i in items]
    assert len(topics) == len(set(topics)), "topics must be unique (store is keyed on topic)"
    for it in items:
        for field in ("id", "topic", "dimension", "prompt", "rubric"):
            assert field in it, f"design item {it.get('id')} missing {field}"
        assert len(it["rubric"]) >= 3, f"design item {it['id']} rubric too thin"
