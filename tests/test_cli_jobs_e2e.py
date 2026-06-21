import json

from phantom_tutor import cli, paths


def _seed_data(tmp_path):
    src = tmp_path / "top200.json"
    src.write_text(json.dumps([
        {"job_id": "p", "title": "platform", "company_tier": "big",
         "skills_norm": ["python"], "themes": ["platform", "governance"],
         "salary_hi": 90000, "salary_disclosed": True, "match_score": 70},
        {"job_id": "x", "title": "agency-noise", "company_tier": "agency",
         "skills_norm": [], "themes": [], "match_score": 0},
    ], ensure_ascii=False), encoding="utf-8")
    paths.operator_profile_path().write_text(
        json.dumps({"has_skills": ["python"], "weak_or_missing": ["mlops"]}),
        encoding="utf-8")
    return src


def test_jobs_ingest_then_rank_and_side_hustle(tmp_path, capsys):
    src = _seed_data(tmp_path)
    assert cli.main(["jobs", "ingest", "--src", str(src)]) == 0
    out = capsys.readouterr().out
    assert "1" in out                      # 1 ingested (agency dropped)

    assert cli.main(["jobs", "rank"]) == 0
    assert "platform" in capsys.readouterr().out

    assert cli.main(["jobs", "side-hustle"]) == 0
    assert "python" in capsys.readouterr().out


def test_jobs_gap_seeds_today(tmp_path, capsys):
    src = _seed_data(tmp_path)
    cli.main(["jobs", "ingest", "--src", str(src)])
    capsys.readouterr()
    assert cli.main(["--now", "2026-06-21", "jobs", "gap"]) == 0
    assert cli.main(["--now", "2026-06-21", "today"]) == 0
    assert "platform" in capsys.readouterr().out or "python" in capsys.readouterr().out
