from phantom_tutor import wealth


def _job(**kw):
    base = {"title": "", "skills_norm": [], "themes": [],
            "salary_hi": 0, "salary_disclosed": False,
            "match_score": 0.0, "company_tier": "small"}
    base.update(kw)
    return base


def test_platform_governance_job_maxes_w1_w2():
    s = wealth.wealth_score(_job(themes=["agent", "platform", "governance"],
                                 salary_hi=120000, salary_disclosed=True,
                                 match_score=80, company_tier="big"))
    assert s["w1"] == 5   # agent/platform/governance
    assert s["w2"] == 5   # platform/governance
    assert s["w3"] == 5   # 120k*14 = 1.68M annual >= 1.6M
    assert s["w4"] == 5   # match>=60 and big


def test_rag_app_job_scores_mid_w1_w2():
    s = wealth.wealth_score(_job(themes=["rag", "application"], match_score=40))
    assert s["w1"] == 3   # rag
    assert s["w2"] == 3   # application


def test_traditional_job_scores_low():
    s = wealth.wealth_score(_job(themes=["cv"], match_score=10))
    assert s["w1"] == 1
    assert s["w2"] == 1
    assert s["w3"] == 1   # undisclosed salary
    assert s["w4"] == 1


def test_salary_bands():
    def w3(hi):
        return wealth.wealth_score(_job(salary_hi=hi, salary_disclosed=True))["w3"]
    assert w3(120000) == 5   # 1.68M >= 1.6M
    assert w3(80000) == 4    # 1.12M in [1.0M,1.6M)
    assert w3(60000) == 2    # 0.84M in [0.8M,1.0M)
    assert w3(40000) == 1    # 0.56M < 0.8M
    assert wealth.wealth_score(_job(salary_hi=999999999))["w3"] == 1  # undisclosed default


def test_weighted_score_formula():
    # agent -> W1 leverage; platform -> W2 durability (axes stay distinct)
    s = wealth.wealth_score(_job(themes=["agent", "platform"], salary_hi=120000,
                                 salary_disclosed=True, match_score=80,
                                 company_tier="big"))
    # 3*5 + 2.5*5 + 2*5 + 2*5 = 47.5
    assert s["score"] == 47.5


def test_axes_stay_distinct_agent_is_w1_not_w2():
    # 'agent' is leverage (W1), not durability (W2): a pure agent-app theme must
    # not auto-max W2 — keeps the durability axis discriminating.
    s = wealth.wealth_score(_job(themes=["agent"]))
    assert s["w1"] == 5
    assert s["w2"] == 1


def test_rank_puts_platform_above_pure_high_salary_app():
    platform = _job(title="platform", themes=["platform", "governance"],
                    salary_hi=90000, salary_disclosed=True, match_score=70,
                    company_tier="big")
    pay_app = _job(title="app", themes=["rag", "application"],
                   salary_hi=200000, salary_disclosed=True, match_score=70,
                   company_tier="big")
    ranked = wealth.rank([pay_app, platform])
    assert ranked[0]["title"] == "platform"           # W1/W2 asymmetry wins
    assert ranked[0]["wealth"]["score"] >= ranked[1]["wealth"]["score"]
