from phantom_tutor.cli import main
from phantom_tutor import memory


def test_quiz_grades_keyword_answer_and_records_weakspot(capsys):
    # answer containing a keyword scores a pass; recorded to weak_spots
    rc = main(["quiz", "--id", "k-softmax", "--answer", "subtract the max for numerical stability"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "softmax" in out.lower()
    store = memory.load_store()
    assert "softmax" in store and store["softmax"]["attempts"] == 1
    assert store["softmax"]["mastery"] > 0  # keyword hit -> positive score


def test_quiz_wrong_answer_records_low(capsys):
    rc = main(["quiz", "--id", "k-softmax", "--answer", "no idea"])
    assert rc == 0
    store = memory.load_store()
    assert store["softmax"]["mastery"] == 0.0  # no keyword -> 0
