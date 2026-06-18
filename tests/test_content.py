from phantom_tutor import content


def test_load_bank_reads_seed():
    items = content.load_bank("knowledge")
    assert any(i["id"] == "k-softmax" for i in items)
    cod = content.load_bank("coding")
    assert any("tests" in i for i in cod)


def test_get_item_by_id():
    item = content.get_item("coding", "c-add")
    assert item["prompt"].startswith("Implement add")
