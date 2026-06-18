from phantom_tutor.cli import main
from phantom_tutor import memory

GOOD = "def add(a, b):\n    return a + b\n"
BAD = "def add(a, b):\n    return a - b\n"


def test_code_grades_solution_file_through_runner(tmp_path, capsys):
    sol = tmp_path / "sol.py"
    sol.write_text(GOOD, encoding="utf-8")
    rc = main(["code", "--id", "c-add", "--solution", str(sol)])
    assert rc == 0
    assert "score=1.00" in capsys.readouterr().out
    assert memory.load_store()["basics"]["mastery"] > 0


def test_code_wrong_solution_low(tmp_path):
    sol = tmp_path / "sol.py"
    sol.write_text(BAD, encoding="utf-8")
    rc = main(["code", "--id", "c-add", "--solution", str(sol)])
    assert rc == 0
    assert memory.load_store()["basics"]["mastery"] == 0.0
