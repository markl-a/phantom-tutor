# 104 source importer (R0: real data → top200 → ingest) — design spec

> 日期:2026-06-21 · 分支 `feat/import-104`。公開、零 PII。
> 私人來源(gitignored,不 commit):`personalized/05-top200-analysis.md`(composite rubric / big_company 名表 / direction 關鍵字 / 9999999 哨兵 / 雜訊)、`personalized/07-jobcopilot-tool-spec.md` §1.1(top200 schema)。本檔只萃取非 PII 的 schema 與規則。

## 目標(R0)

把工具從「合成 fixture」接上**真實求職資料**,落實 apex 階段 0「個人工具優先」。新增一個來源適配器:讀 operator 的 `104_ai_jobs_matched_v2_<date>.csv`(2,996 筆/日),依 05 §1 composite rubric 選 top-200,轉成既有 `jobs.ingest` 吃得下的 schema,一鍵把真實資料接進 `data_root()`。

**範圍**:CSV → top200 → ingest + 寫 operator_skills 空範本。**不做**:對外爬取、每日刷新管線(R0 之後)、wealth 四軸 LLM 細化(R2)。

## 來源 CSV(真實 schema,UTF-8 with BOM,17 欄)

`匹配分數`(0–85) · `命中明細`(A_LLM/B_ML/C_ENG 桶文字) · `職稱` · `公司` · `工作地點` · `薪資`(人讀文字) · `經驗要求` · `學歷要求` · `公司產業` · `需求技能`(分隔字串) · `工作摘要` · `更新日期` · `職缺網址`(PII) · `公司網址` · `薪資下限` · `薪資上限` · `職缺ID`

## 架構

- **新模組** `phantom_tutor/sources_104.py`:`to_top200(csv_path, *, top_n=200) -> list[dict]`。純讀 CSV(`utf-8-sig`)、逐列轉換、算 composite、排序取 top_n。**不寫檔**。
- **CLI** `tutor jobs import-104 --src <csv> [--n 200]`:`to_top200` → 既有 `jobs.ingest`(寫 `jobs.json`、去重、濾 `agency`)。若 `operator_skills.json` 不存在,寫一份空範本 `{"has_skills": [], "weak_or_missing": []}` 並提示填寫。
- 重用 `jobs.ingest` / `wealth` / `paths`。產出的 record 直接餵 `rank`/`gap`/`side-hustle`。

### 邊界(硬規則)

- `--src` 可為任意路徑(operator 的 Downloads CSV);**只寫 `data_root()`**,永不寫 repo。
- 原始 CSV 含 PII(公司/JD/薪資/網址)——只存衍生的 top200 + 統計,原始 CSV 不 commit。
- 測試一律合成 UTF-8-BOM CSV fixture(假公司/假技能),零 PII;沿用 conftest tmp HOME。

## 逐列轉換(to_top200)

每列 → record:
- `job_id` = `f"104-{職缺ID}"`(去重 key)
- `title`=職稱、`company`=公司、`loc`=工作地點、`industry`=公司產業
- **薪資正規化成月薪 TWD**:`lo/hi` = int(薪資下限/上限);`9999999` 或 ≤0 → 0;**揭露且值 ≥ 300_000 視為年薪 → `//12`**(否則當月薪);`salary_disclosed` = 正規化後 hi>0
- `match_score` = float(匹配分數)
- `skills_norm` = 切分 `需求技能`(分隔:`,`、`、`、`/`、`;`、空白)→ strip → lower → 去重、去空
- `themes` = 在 `職稱 + 需求技能 + 命中明細 + 公司產業` 文字中命中 `DIRECTION_KEYWORDS` 的 token 集(這些 theme 餵 wealth W1/W2)
- `company_tier`(四分法,名單驅動,因來源無員工數欄):
  1. 公司含 `AGENCY_KEYWORDS`(人力/仲介/獵頭/派遣/顧問派遣/補習/人資)→ `agency`(ingest 會濾掉)
  2. 公司 ∈ `BIG_COMPANIES`(05 名表)→ `big`
  3. 公司 ∈ `MID_COMPANIES`(策展起始名單,operator 可擴)→ `mid`
  4. 其餘 → `small`
- `composite`(05 §1,選樣依據):
  ```
  composite = 0.30 * min(salary_hi_raw, 3_000_000)/3_000_000   # 未揭露=0;用原始上限(未月薪正規化前)
            + 0.30 * match_score/85
            + 0.20 * (1 if tier=="big" else 0)
            + 0.20 * min(direction_hits, 15)/15                  # themes 命中數 cap 15
  ```
  > 註:composite 的 salary 用「原始薪資上限」(05 原文如此,不做月薪正規化),與 record 的 `salary_hi`(月薪正規化)是兩個不同用途的數字。

排序:`composite` 降冪,取前 `top_n`(預設 200)。

## 模組常數(易調)

- `BIG_COMPANIES`:05 §1 名表(台積/鴻海/聯發科/南亞科/美光/廣達/緯創/和碩/華碩/宏碁/技嘉/研華/台達/聯詠/瑞昱/日月光/群聯/世界先進/力積電 + 國泰/富邦/中信/玉山/台新/永豐 + 工研院/資策會 + 趨勢/LINE/Appier/iKala/Garmin + 外商 Google/MSFT/NVIDIA/Intel/AWS/Qualcomm/Synopsys/Cadence)。子字串比對(公司名含其一即命中)。
- `MID_COMPANIES`:策展起始(行動貝果/神基/緯穎/國泰人壽 等非頂大廠但可信中型;operator 擴充)。
- `AGENCY_KEYWORDS`:{人力, 仲介, 獵頭, 派遣, 顧問派遣, 補習, 人資}。
- `DIRECTION_KEYWORDS`:05 §1(agent, llm, rag, mlops, platform, infra, serving, vllm, triton, langchain, k8s, vector, embedding, 推論, 平台, 框架, 架構師, pytorch, tensorflow, fine-tune, huggingface, transformer, distributed)。

## CLI

| 命令 | 行為 |
|---|---|
| `tutor jobs import-104 --src <csv> [--n N]` | to_top200 → ingest;若無 operator_skills.json 寫空範本;印「ingested N / 寫了範本請填」 |

(既有 `tutor jobs list/demand/gap/rank/side-hustle` 不變,直接在真實資料上跑。)

## 測試(TDD,hermetic)

- `tests/test_sources_104.py`:
  - 薪資正規化:月薪原樣、年薪(≥300k)→/12、9999999→未揭露、空→未揭露
  - skills_norm 切分/小寫/去重(多分隔符)
  - themes 命中 DIRECTION_KEYWORDS
  - company_tier 四分支(big/mid/small/agency)
  - composite 排序 + top_n 截斷
  - UTF-8-BOM 讀取正確
- `tests/test_cli_import_104_e2e.py`:`cli.main(["jobs","import-104","--src",<合成csv>])` → jobs.json 寫出、agency 濾掉、operator_skills.json 空範本生成;接著 `rank` 在真實 schema 上有輸出。

## 驗收

- 合成 CSV(含 1 筆年薪、1 筆月薪、1 筆面議、1 筆 agency)→ `import-104` 寫出正確 jobs.json,薪資正規化正確,agency 不在內。
- `operator_skills.json` 不存在時被寫成空範本。
- ruff clean、既有 48 測試 + 新測試全綠。
- **(operator 手動驗收)**:對真實 `104_ai_jobs_matched_v2_20260618.csv` 跑 import-104 + 填 profile → `tutor today` 排出真實 gap、`rank` top-N 符合直覺(交叉比對 05 §2.3 的 top5:南亞科/工研院/鴻海/華碩在前段)。
