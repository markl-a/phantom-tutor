"""Tests for the 104 matched_v2 CSV -> top200 source adapter. Synthetic, PII-free
fixtures (fake companies/skills), UTF-8 with BOM like the real export."""
import codecs
import csv

from phantom_tutor import sources_104

COLS = ["匹配分數", "命中明細", "職稱", "公司", "工作地點", "薪資", "經驗要求",
        "學歷要求", "公司產業", "需求技能", "工作摘要", "更新日期", "職缺網址",
        "公司網址", "薪資下限", "薪資上限", "職缺ID"]


def _row(**kw):
    base = {c: "" for c in COLS}
    base.update(kw)
    return base


def _write_csv(tmp_path, rows):
    p = tmp_path / "matched.csv"
    # UTF-8 with BOM, exactly like the real 104 export
    with open(p, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return str(p)


def _one(tmp_path, **kw):
    return sources_104.to_top200(_write_csv(tmp_path, [_row(職缺ID="1", **kw)]))[0]


def test_reads_utf8_bom_and_maps_basic_fields(tmp_path):
    rec = _one(tmp_path, 職稱="AI 應用開發工程師", 公司="南亞科技",
               工作地點="新北市", 公司產業="半導體", 匹配分數="84.5")
    assert rec["job_id"] == "104-1"
    assert rec["title"] == "AI 應用開發工程師"
    assert rec["company"] == "南亞科技"
    assert rec["match_score"] == 84.5


def test_salary_monthly_kept_annual_divided_sentinel_undisclosed(tmp_path):
    monthly = _one(tmp_path, 薪資下限="40000", 薪資上限="65000")
    assert monthly["salary_hi"] == 65000 and monthly["salary_disclosed"] is True
    annual = _one(tmp_path, 薪資下限="1500000", 薪資上限="2400000")
    assert annual["salary_hi"] == 200000          # 2.4M annual -> /12 monthly
    assert annual["salary_lo"] == 125000          # 1.5M annual -> /12
    sentinel = _one(tmp_path, 薪資下限="9999999", 薪資上限="9999999")
    assert sentinel["salary_hi"] == 0 and sentinel["salary_disclosed"] is False
    blank = _one(tmp_path, 薪資下限="", 薪資上限="")
    assert blank["salary_hi"] == 0 and blank["salary_disclosed"] is False


def test_skills_split_lower_dedup_multiple_separators(tmp_path):
    rec = _one(tmp_path, 需求技能="Python, PyTorch、LLM / Python; LLM")
    assert rec["skills_norm"] == ["python", "pytorch", "llm"]


def test_themes_hit_direction_keywords(tmp_path):
    rec = _one(tmp_path, 職稱="MLOps 平台架構師", 需求技能="Python, Kubernetes",
               命中明細="A_LLM: agent, rag", 公司產業="軟體")
    assert set(rec["themes"]) >= {"mlops", "平台", "架構師", "agent", "rag"}


def test_company_tier_four_way(tmp_path):
    assert _one(tmp_path, 公司="台積電")["company_tier"] == "big"
    assert _one(tmp_path, 公司="行動貝果")["company_tier"] == "mid"
    assert _one(tmp_path, 公司="睿富人力資源顧問")["company_tier"] == "agency"
    assert _one(tmp_path, 公司="某不知名新創")["company_tier"] == "small"


def test_agency_bait_detected_in_title(tmp_path):
    # 05 §2.1: proxy-recruiting bait (代招/代徵/獵才) is noise, not a target.
    # The marker is usually in the TITLE, not the company name.
    assert _one(tmp_path, 職稱="[代招] 資深 AI 機器學習工程師_KK",
                公司="某科技")["company_tier"] == "agency"
    assert _one(tmp_path, 職稱="AI 工程師(代徵)", 公司="X")["company_tier"] == "agency"
    assert _one(tmp_path, 公司="優秀獵才顧問")["company_tier"] == "agency"


def test_composite_ranks_and_truncates_top_n(tmp_path):
    rows = [
        _row(職缺ID="hi", 公司="台積電", 匹配分數="85", 薪資上限="3000000",
             職稱="AI Platform Architect", 需求技能="agent, mlops, rag, llm, platform",
             命中明細="agent llm rag"),
        _row(職缺ID="lo", 公司="某小店", 匹配分數="5", 薪資上限="",
             職稱="行政助理", 需求技能="excel"),
    ]
    ranked = sources_104.to_top200(_write_csv(tmp_path, rows))
    assert [r["job_id"] for r in ranked] == ["104-hi", "104-lo"]
    top1 = sources_104.to_top200(_write_csv(tmp_path, rows), top_n=1)
    assert [r["job_id"] for r in top1] == ["104-hi"]


def test_bom_present_in_fixture(tmp_path):
    # guard: the fixture really is BOM-prefixed (so we test the real read path)
    p = _write_csv(tmp_path, [_row(職缺ID="1")])
    with open(p, "rb") as f:
        assert f.read(3) == codecs.BOM_UTF8
