import json

from phantom_tutor import jobs, paths


def _write_src(tmp_path, records):
    p = tmp_path / "top200.json"
    p.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    return p


def test_ingest_dedups_by_job_id_and_filters_agency(tmp_path):
    src = _write_src(tmp_path, [
        {"job_id": "a", "title": "A", "company_tier": "big"},
        {"job_id": "a", "title": "A-dup", "company_tier": "big"},   # dup -> dropped
        {"job_id": "b", "title": "B", "company_tier": "agency"},    # agency -> dropped
        {"job_id": "c", "title": "C", "company_tier": "mid"},
    ])
    out = jobs.ingest(str(src))
    ids = sorted(j["job_id"] for j in out)
    assert ids == ["a", "c"]
    assert paths.jobs_path().exists()
    assert sorted(j["job_id"] for j in jobs.load_jobs()) == ["a", "c"]


def test_load_jobs_missing_returns_empty():
    assert jobs.load_jobs() == []
