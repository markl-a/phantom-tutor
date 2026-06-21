# jobs 資料層 + wealth-score — 設計 spec

> 日期:2026-06-21 · 對應 master。本檔為**公開、零 PII** spec;真實求職資料(`top200.json`/來源 CSV)永遠落 `paths.data_root()`,不進 repo。
> 私人設計來源(gitignored,不 commit):`personalized/04-wealth-max-job-strategy.md` §2、`personalized/07-jobcopilot-tool-spec.md` §1–4。本檔只萃取**非 PII 的 schema 與評分量表**。

## 目標

把 phantom-tutor 從「靜態 4-mode 練習器」升級成「以真實目標職缺為地基的求職 copilot」的**最小子集**:

1. `jobs` 資料層:ingest 目標職缺 → 算 demand frequency → 用「demand − operator supply」播種既有 `weak_spots`,讓 `tutor today` 第一天就 grounded。
2. `wealth-score`:純評分函式,在既有 `match_score` 之上疊四軸人生財富目標函數,把目標排成「本週該主投 / 該跳槽去的前 N 個」(= **跳槽分析**)。
3. **副業分析**:從同一份職缺資料反推「能賣的技能」——demand × coverage,與 gap 播種對稱。

**範圍 = 07 SPEC 的 P1+P2 + wealth-score 函式 + 副業/跳槽訊號。** 刻意不做(階段後):mode 增強(`--job/--cluster`)、刷新管線、owned-memory 後端切換、LLM 細化四軸、跨槽時機評分(需現薪 PII,超出純職缺資料)。

### coverage 的三種對稱用途(同一個 helper)

operator 對每個技能的 coverage:`has_skills`→0.7、`weak_or_missing`→0.0、未知→0.4。三個衍生訊號共用:

| 訊號 | 公式 | 意義 | 落地 |
|---|---|---|---|
| **gap(要練的)** | demand × (1 − coverage) | 市場熱 × 你弱 | `seed_weak_spots` → `tutor today` |
| **副業(能賣的)** | demand × coverage | 市場熱 × 你強 | `tutor jobs side-hustle` |
| **跳槽(該換去哪)** | wealth-score 排序 | 高財富 × 拿得到 | `tutor jobs rank` |

## 架構

兩個新模組,沿用既有 `srs.py`(純)vs `memory.py`(I/O)的分層風格:

| 模組 | 角色 | I/O |
|---|---|---|
| `phantom_tutor/wealth.py` | 純評分:四軸 → wealth-score、rank | 無 I/O(純函式) |
| `phantom_tutor/jobs.py` | 資料層:ingest / demand / gap 播種 | 讀 top200 + 讀/寫 data_root + 呼叫 `memory.record_attempt` |

重用既有:`content.py` / `memory.py`(`record_attempt`)/ `srs.py` / `paths.py` / `cli.py`。不重寫 SRS、不重寫 mode。

### 資料邊界(硬規則)

- 所有 jobs/profile 資料落 `paths.data_root()`(`PHANTOM_TUTOR_HOME` > `PHANTOM_HOME/tutor` > `~/.phantom-mesh/tutor`),**絕不進 repo**。
- `paths.py` 新增 `jobs_path()`(`data_root()/jobs.json`)、`operator_profile_path()`(`data_root()/operator_skills.json`)。
- 來源 `top200.json` 含 PII(公司、JD、薪資),ingest 後本工具只在 data_root 存衍生資料;原始檔不 commit。
- 測試一律合成 fixture(假公司名/假技能),零 PII;沿用 `conftest.py` 的 tmp `PHANTOM_TUTOR_HOME` + stub LLM。

## 資料形狀(schema)

### jobs record(`jobs.json` 內一筆;非 PII 欄位定義)

```jsonc
{
  "job_id": "src-<id>",          // 去重 key
  "title": "...",
  "company": "...",
  "company_tier": "big",          // big | mid | small | agency(agency=雜訊,ingest 時濾掉)
  "salary_lo": 0, "salary_hi": 0, // 月薪 TWD;9999999 哨兵 → 0;0 = 未揭露
  "salary_disclosed": false,
  "skills_norm": ["python", "llm"],
  "themes": ["llm", "agent", "mlops"],
  "match_score": 84.5             // 既有關鍵字命中分(0–100)
}
```

> wealth-score 只讀:`title` / `skills_norm` / `themes` / `salary_hi` / `salary_disclosed` / `match_score` / `company_tier`。其餘欄位(loc/exp/edu/industry/cluster/rank…)ingest 時保留但本子集不消費。

### operator_profile(`operator_skills.json`;手動維護一次)

```jsonc
{
  "has_skills": ["python", "llm", "rag", "..."],
  "weak_or_missing": ["mlops", "k8s", "..."]
}
```

## wealth-score(`wealth.py`,純函式)

四軸 rubric,每軸 0–5;`wealth_score = 3·W1 + 2.5·W2 + 2·W3 + 2·W4`,滿分 **47.5**。
關鍵不對稱:W1×3、W2×2.5 **故意**壓過 W3 薪資——年資淺只能靠作品槓桿 + 耐久方向蓋過。

| 軸 | 權重 | 自動化來源 | 啟發式打分 |
|---|---:|---|---|
| **W1 既有槓桿** | ×3 | `skills_norm` + `themes` + `title` | 命中 {agent, runtime, platform, governance, mlops, infra} 任一 → 5;命中 {llm, rag} → 3;否則 → 1 |
| **W2 抗 AI 取代** | ×2.5 | `title` + `themes` | 命中 {platform, infra, system-design, governance, architect, mlops} → 5;命中 {rag, app, application} → 3;否則 → 1 |
| **W3 薪資天花板** | ×2 | `salary_hi`(月薪 → 年薪 ×14 估算) | 年薪 ≥160萬 → 5;100–150萬 → 4;80–100萬 → 2;<80萬 或未揭露 → 1 |
| **W4 契合/命中** | ×2 | `match_score` + `company_tier` | match≥60 且 tier=big → 5;match≥60 或 tier∈{big,mid} → 3;否則 → 1 |

> **W4 是近似**:04 §2.2 原始 W4 含「我真心想做 + 大廠能待久」的主觀判斷,無法自動;此處用 `company_tier` + `match_score` 近似,operator 可在 offer 階段手動覆寫。關鍵字集合定義為模組常數,易調。

API:
- `wealth_score(job: dict) -> dict` → `{"w1": int, "w2": int, "w3": int, "w4": int, "score": float}`(score round 到 2 位)
- `rank(jobs: list[dict]) -> list[dict]` → 每筆附 `wealth` 子物件,依 `score` 由高到低排序

## jobs 資料層(`jobs.py`)

- `ingest(top200_path, *, path=None) -> list[dict]`:讀 top200.json → 去重 by `job_id` → 濾 `company_tier=="agency"` → 寫 `jobs.json`(`json.dumps` indent=2, ensure_ascii=False,沿用 `memory.save_store` 風格)。回傳寫入的 records。
- `load_jobs(*, path=None) -> list[dict]`:讀 `jobs.json`(不存在 → `[]`)。
- `demand(jobs: list[dict]) -> dict[str, int]`:對所有 `skills_norm` + `themes` 做 frequency,回 `{skill: 命中筆數}`,降冪。
- `_coverage(skill, profile) -> float`(共用 helper):`has_skills`→0.7、`weak_or_missing`→0.0、未知→0.4。
- `seed_weak_spots(jobs, profile, now_iso, *, top_n=10, path=None) -> list[dict]`:
  ```
  for skill, freq in demand(jobs).items():
      coverage = _coverage(skill, profile)
      priority = freq * (1 - coverage)          # gap = 市場熱 × 你弱
  # 取 priority top_n → memory.record_attempt(key=skill, dimension="job-gap",
  #                       score=1-coverage, now_iso, topic=skill)
  ```
  讓 `tutor today` 第一天 weakest-first 排出最該補的 gap。回傳播種的 records。
- `side_hustle(jobs, profile, *, top_n=10) -> list[dict]`(副業分析,純函式不寫 weak_spots):
  ```
  for skill, freq in demand(jobs).items():
      coverage = _coverage(skill, profile)
      monetizable = freq * coverage             # 副業 = 市場熱 × 你強
  # 回 top_n: {"skill", "demand", "coverage", "score"},score 降冪
  ```
  與 gap 對稱:gap 找「該練的」,side_hustle 找「該接案賣的」。

## CLI(掛在 `tutor jobs` 子命令族,沿用 `cli.py` 既有 `sub.add_parser` 模式)

| 命令 | 行為 |
|---|---|
| `tutor jobs ingest --src <path>` | ingest top200.json → jobs.json;印寫入筆數 |
| `tutor jobs list [--tier big]` | 列出 jobs(可依 tier 過濾) |
| `tutor jobs demand [--n N]` | 印 demand frequency top-N |
| `tutor jobs gap [--n N]` | 跑 seed_weak_spots,印播種的 gap(該練的) |
| `tutor jobs rank [--n N]` | **跳槽分析**:wealth.rank(jobs),印前 N「該主投/該跳槽去」(title / wealth-score / 四軸) |
| `tutor jobs side-hustle [--n N]` | **副業分析**:印前 N「能賣的技能」(skill / demand / coverage / score) |

## 測試(TDD,全 hermetic)

- `tests/test_wealth.py`:純函式四軸邊界(每軸高/中/低)、加權公式、未揭露薪資、rank 排序穩定性。
- `tests/test_jobs.py`:ingest 去重 + 濾 agency、demand frequency、`_coverage` 三分支、gap 播種 priority 排序 + 寫進 weak_spots(查 `memory.due_topics`)、side_hustle 排序(has-skill 高分、missing-skill 出局)+ 與 gap 的對稱性。
- `tests/test_cli_jobs_e2e.py`:`cli.main(["jobs", "ingest", ...])` 等子命令 e2e,合成 fixture。
- `tests/test_paths.py`:新增 `jobs_path` / `operator_profile_path` 解析。

## 驗收

- `tutor jobs ingest --src <合成fixture>` → 寫出 jobs.json、濾掉 agency。
- `tutor jobs gap` → `tutor today` 隔天排出最高 priority 的 gap(weakest-first)。
- `tutor jobs rank` → 平台/治理職(W1/W2 高)排在純高薪應用職之上(驗證 04 §2.2 的關鍵不對稱);這就是跳槽目標清單。
- `tutor jobs side-hustle` → 你已強且市場熱的技能排前面,真缺口(coverage=0)不出現。
- ruff clean、既有 29 測試 + 新測試全綠。
