from phantom_tutor import runner

SOLUTION_OK = "def add(a, b):\n    return a + b\n"
SOLUTION_BAD = "def add(a, b):\n    return a - b\n"
TESTS = (
    "from solution import add\n"
    "def test_pos():\n    assert add(2, 3) == 5\n"
    "def test_big():\n    assert add(10, 5) == 15\n"
)
PARTIAL_TESTS = (
    "from solution import add\n"
    "def test_pos():\n    assert add(2, 3) == 5\n"
    "def test_negative():\n    assert add(2, -3) == -1\n"
)


def test_runner_scores_correct_solution_full():
    r = runner.run_code(SOLUTION_OK, TESTS)
    assert r["passed"] == 2 and r["total"] == 2 and r["score"] == 1.0


def test_runner_scores_wrong_solution_low():
    r = runner.run_code(SOLUTION_BAD, TESTS)
    assert r["passed"] == 0 and r["score"] == 0.0


def test_runner_scores_partial_pass_rate():
    r = runner.run_code("def add(a, b):\n    return a + b if b > 0 else 0\n", PARTIAL_TESTS)
    assert r["passed"] == 1 and r["total"] == 2 and r["score"] == 0.5


def test_runner_scores_zero_when_no_tests_collected():
    r = runner.run_code(SOLUTION_OK, "from solution import add\n")
    assert r["passed"] == 0 and r["total"] == 0 and r["score"] == 0.0


def test_runner_times_out_gracefully():
    r = runner.run_code("import time\ntime.sleep(30)\n", "from solution import x\n", timeout=2)
    assert r["score"] == 0.0  # timeout -> 0, no hang
