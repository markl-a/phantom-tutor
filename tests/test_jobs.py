import json

from phantom_tutor import jobs, memory, paths


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


def test_demand_counts_skills_and_themes_descending():
    js = [
        {"job_id": "1", "skills_norm": ["python", "llm"], "themes": ["agent"]},
        {"job_id": "2", "skills_norm": ["python"], "themes": ["agent", "mlops"]},
        {"job_id": "3", "skills_norm": ["llm"], "themes": []},
    ]
    d = jobs.demand(js)
    assert d["python"] == 2
    assert d["agent"] == 2
    assert d["llm"] == 2
    assert d["mlops"] == 1
    assert list(d.values()) == sorted(d.values(), reverse=True)


def test_coverage_three_branches():
    profile = {"has_skills": ["python"], "weak_or_missing": ["mlops"]}
    assert jobs._coverage("python", profile) == 0.7
    assert jobs._coverage("mlops", profile) == 0.0
    assert jobs._coverage("unknown", profile) == 0.4


def test_seed_weak_spots_seeds_highest_gap_first_into_memory():
    js = [
        {"job_id": "1", "skills_norm": [], "themes": ["mlops", "mlops", "python"]},
        {"job_id": "2", "skills_norm": [], "themes": ["mlops", "python"]},
    ]
    profile = {"has_skills": ["python"], "weak_or_missing": ["mlops"]}
    seeded = jobs.seed_weak_spots(js, profile, "2026-06-21", top_n=5)
    assert seeded[0]["topic"] == "mlops"
    keys = [w["key"] for w in memory.list_weak()]
    assert "mlops" in keys and "python" in keys
    assert all(s["dimension"] == "job-gap" for s in seeded)


def test_load_profile_missing_returns_empty_lists():
    p = jobs.load_profile()
    assert p == {"has_skills": [], "weak_or_missing": []}


def test_side_hustle_ranks_strong_in_demand_skills_excludes_real_gaps():
    js = [
        {"job_id": "1", "skills_norm": ["python", "python"], "themes": ["mlops"]},
        {"job_id": "2", "skills_norm": ["python"], "themes": ["mlops"]},
    ]
    profile = {"has_skills": ["python"], "weak_or_missing": ["mlops"]}
    out = jobs.side_hustle(js, profile, top_n=5)
    skills = [r["skill"] for r in out]
    assert skills[0] == "python"
    assert "mlops" not in skills            # real gap -> can't sell -> excluded
    assert out[0]["score"] == round(3 * 0.7, 4)


def test_side_hustle_and_gap_are_symmetric():
    js = [{"job_id": "1", "skills_norm": ["python", "mlops"], "themes": []}]
    profile = {"has_skills": ["python"], "weak_or_missing": ["mlops"]}
    sell = {r["skill"] for r in jobs.side_hustle(js, profile)}
    seeded = jobs.seed_weak_spots(js, profile, "2026-06-21")
    gaps = {s["topic"] for s in seeded}
    assert "python" in sell and "mlops" in gaps
