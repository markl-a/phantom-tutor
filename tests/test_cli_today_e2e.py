from phantom_tutor.cli import main


def test_today_lists_due_weakest_first(capsys):
    # two weak spots due, one strong/not-due
    main(["--now", "2026-06-10", "quiz", "--id", "k-softmax", "--answer", "no idea"])   # weak
    main(["--now", "2026-06-10", "quiz", "--id", "k-rag", "--answer", "retrieval grounding hallucination context"])  # strong
    capsys.readouterr()  # drain prior output
    rc = main(["--now", "2026-06-12", "today"])
    assert rc == 0
    body = capsys.readouterr().out
    assert "softmax" in body          # weak one is due + surfaced
    assert "Due:" in body or "due" in body.lower()


def test_weak_spots_and_stats(capsys):
    main(["--now", "2026-06-10", "quiz", "--id", "k-softmax", "--answer", "no idea"])
    capsys.readouterr()
    assert main(["weak-spots"]) == 0
    assert "softmax" in capsys.readouterr().out
    assert main(["stats"]) == 0
    assert "attempts" in capsys.readouterr().out.lower()
