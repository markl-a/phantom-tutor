"""e2e: tutor jobs import-104 reads a synthetic 104 CSV, ingests top200, writes an
operator_skills template. Synthetic PII-free fixture, UTF-8 BOM like the real export."""
import csv
import json

from phantom_tutor import cli, jobs, paths

COLS = ["匹配分數", "命中明細", "職稱", "公司", "工作地點", "薪資", "經驗要求",
        "學歷要求", "公司產業", "需求技能", "工作摘要", "更新日期", "職缺網址",
        "公司網址", "薪資下限", "薪資上限", "職缺ID"]


def _write_104_csv(tmp_path):
    rows = [
        {**{c: "" for c in COLS}, "職缺ID": "1", "職稱": "AI Platform Architect",
         "公司": "台積電", "匹配分數": "80", "薪資下限": "1500000", "薪資上限": "2400000",
         "需求技能": "Python, MLOps", "命中明細": "agent llm", "公司產業": "半導體"},
        {**{c: "" for c in COLS}, "職缺ID": "2", "職稱": "資深 AI 人才",
         "公司": "睿富人力資源顧問", "匹配分數": "28", "薪資上限": "3000000",
         "需求技能": "AI", "命中明細": ""},
    ]
    p = tmp_path / "matched.csv"
    with open(p, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    return str(p)


def test_import_104_ingests_and_writes_profile_template(tmp_path, capsys):
    src = _write_104_csv(tmp_path)
    assert cli.main(["jobs", "import-104", "--src", src]) == 0
    out = capsys.readouterr().out
    assert "1" in out                                   # 1 ingested (agency dropped)

    ingested = jobs.load_jobs()
    ids = [j["job_id"] for j in ingested]
    assert ids == ["104-1"]                             # agency 104-2 filtered out
    assert ingested[0]["salary_hi"] == 200000           # 2.4M annual -> monthly

    # operator_skills template written when absent
    prof = json.loads(paths.operator_profile_path().read_text(encoding="utf-8"))
    assert prof == {"has_skills": [], "weak_or_missing": []}

    # downstream commands run on the real-schema data
    assert cli.main(["jobs", "rank"]) == 0
    assert "AI Platform Architect" in capsys.readouterr().out


def test_import_104_keeps_existing_profile(tmp_path):
    paths.operator_profile_path().write_text(
        json.dumps({"has_skills": ["python"], "weak_or_missing": []}), encoding="utf-8")
    cli.main(["jobs", "import-104", "--src", _write_104_csv(tmp_path)])
    prof = json.loads(paths.operator_profile_path().read_text(encoding="utf-8"))
    assert prof["has_skills"] == ["python"]             # not clobbered
