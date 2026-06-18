# phantom-tutor — 設計 / Design Spec

> 日期:2026-06-18 · 狀態:設計(已與 operator brainstorm 定案,待 review)
> 一句話:一個跑在 **phantom-mesh core** 上的**個人學習助手(學習輔助)**——它教你、考你、盯你的弱點、隔天再考。**AI 工程師面試準備**是它的頭號 use case。同時是面試時能展示「我把自己的 AI mesh 編排成學習教練」的**作品**。

---

## 1. 願景 / 定位

- **是什麼**:一個學習助手領域 app,跟 `phantom-finance` / `phantom-quant` / `phantom-companion` 同位階——**直接長在 phantom-mesh core 上**,不掛載在其他衛星。
- **雙重目的**(operator 拍板「兩者都要」):(a) 一個我**真的天天用**來準備面試/持續學習的工具;(b) 一份面試現場拿得出手的**作品**(證明能組起 owned-memory + 多供應商 LLM + 治理的工程力)。
- **為什麼站在 core 上而非 compose ai-feed/training**:`ai-feed` 的本質是**定時資訊抓取/AI 新聞 digest**、`training` 的本質是**模型訓練全流程**(它的 judge 是評模型輸出)——兩者核心目的與「個人學習助手」距離遠,硬掛會打架。phantom-tutor 真正運用的是 **core 的三樣東西**(貼合、不牽強),自己擁有 SRS 與 code-runner 等小組件。

---

## 2. 架構

**一條 owned-memory 脊椎 + 4 個練習模式 + 1 個內容層**,全部寫進同一個 `weak_spots` 記憶;SRS 排程器把該複習/最弱的點端回來考。

```
        ┌──────── 4 模式(都寫弱點、都被 SRS 排程)────────┐
 knowledge(SRS) │ coding(judge) │ system-design(rubric) │ interview(mock)
        │             │                │                    │
        └─────────────┴──── weak_spots 記憶(脊椎)──────────┘
                              │
                     SRS 排程器:依「間隔重複 + 弱點優先」端回來考
                              │
              ┌───────────────┴───────────────┐
        phantom core(genuine tie-in)     content/ 內容層
   LLM(exec/12+ providers) · owned-memory · governor    題庫 + scenarios.md 攻略
```

### phantom-tutor 需要什麼、來自哪(關鍵:站在 core 上、自擁小組件)

| 需要的 | 來源 | 說明 |
|---|---|---|
| **弱點記憶**(跨 session 記你哪裡弱) | **core owned-memory(Hermes/FTS5)** | **最強、最不牽強的 tie-in**:學習弱點存進**你自己的加密 owned-memory**,每次 session recall 回來、廠商看不到 = apex ②護城河落在學習上。Phase 1 先用本地 `weak_spots.json`,Phase 2 接 phantom core 真記憶。 |
| **LLM**(面試官、批改 system-design、出題) | **core 多供應商 LLM**(`phantom exec`/`chat`) | 自動繼承 12+ 供應商 / BYOM;**測試一律 stub**(env flag,像 ai-feed 的 `PHANTOM_FLOW_STUB_LLM`)保持 hermetic。 |
| **長練習跑安全**(可選) | **core governor / mesh** | 長面試 session 可被你的硬煞車管;重批改可派到有 GPU 的節點。Phase 2+。 |
| **SRS 間隔重複** | **自己的**(first-class) | 學習工具的核心,自己擁有。可把成熟演算法(SM-2 類)**抄一份**當起點,**不依賴** ai-feed。 |
| **Coding 批改**(跑解答 vs 單元測試,沙箱) | **自己的**小 code-runner | ~100 行自己的;借 training judge 的**寫法**(subprocess + timeout + pass-rate),**不耦合** training repo。 |

---

## 3. 核心脊椎 — owned-memory 弱點迴圈(護城河 + 作品亮點)

4 個模式每次練習都往 `weak_spots` 寫一筆:`{topic, dimension, outcome(對/錯/分數), confidence, ts}`。SRS 排程器依「間隔重複 + 弱點優先」決定下次端哪些回來考。**= apex ②「越用越懂你」直接落在學習上**:你越用,它越知道你哪裡弱,越針對性地練你。

- **資料模型**:`weak_spots`(每個 topic 的 mastery/last_seen/due/streak)+ `attempts`(每次練習的原始紀錄,可回溯)。
- **SRS**:`due_today(now)` + `record_attempt(topic, outcome)` → 更新 interval/due。Phase 1 純本地 JSON;Phase 2 鏡射進 phantom owned-memory(`phantom event capture` / Hermes),跨裝置 + 加密 + 廠商看不到。

---

## 4. 四個練習模式(spec 全含;實作分階段)

每個模式都必須 **CLI 可達 + 真入口 e2e**(anti-fake-green),寫回 `weak_spots`,被 SRS 排程。

1. **knowledge(知識問答 + SRS)** — AI/ML 題庫(概念題:transformer/RAG/embedding/eval/fine-tune/agent/prompt)。`tutor quiz` 端出到期/弱的題 → 你答 → 判定(自評或對照答案/關鍵詞)→ 更新 SRS + weak_spots。Phase 1:seed 題庫 + 自評/對照。Phase 2:LLM 評分自由作答、題庫擴充。
2. **coding(自動批改)** — DSA + ML-coding 題庫,各帶參考單元測試。`tutor code <problem>` → 你交解答檔 → **自己的 code-runner** 在沙箱 subprocess 跑單元測試 → pass-rate 分數 → weak_spots。Phase 1:幾題 + runner + 計時。Phase 2:大題庫 + 提示分級 + 複雜度回饋。
3. **system-design** — 設計題 + rubric。`tutor design <prompt>` → 你寫答案 → **core LLM** 依 rubric 評分 + 給回饋(requirements/data/model/serving/scale/monitor 各面向)→ weak_spots。Phase 1:幾題 + rubric + LLM 評分(stub 測)。Phase 2:參考架構庫 + 追問。
4. **interview(行為題 / 模擬面試官)** — `tutor interview [--focus <dim>]` → **core LLM 當面試官**,逐輪追問,**讀你的 weak_spots + 你的作品(phantom-mesh)** 來出題與防守練習 → 評分 + weak_spots。Phase 1:單輪→多輪、讀 weak_spots。Phase 2:更深追問、防守作品決策、語氣/節奏。

---

## 5. 每日迴圈(data flow)

`tutor today` → 看今天該做什麼(SRS 到期 + 最弱主題,跨 4 模式)→ 選模式練 → 自動評分/追問 → 寫回 weak_spots → 排下次。一個 loop 收掉「讀 → 考 → 記弱點 → 再考」。`tutor weak-spots` 看弱點排行;`tutor stats` 看進度。

---

## 6. core 整合(怎麼「運用 phantom-mesh」,乾淨版)

- **LLM**:封一層 `llm.py`,預設呼叫 `phantom exec`(或 provider API);`PHANTOM_TUTOR_STUB_LLM=1` 時回確定性 stub → 所有測試 hermetic、不需網路/金鑰。
- **owned-memory**:封一層 `memory.py`;Phase 1 後端 = 本地 JSON,Phase 2 後端 = phantom owned-memory(同介面,換實作)。**絕不寫真 `~/.phantom-mesh`**;測試用 tmp。
- **governor/mesh**:Phase 2+ 可把長 session 包進 `phantom govern`、把重批改 `phantom dispatch` 到 GPU 節點。
- **作品故事**:「phantom-tutor 是長在我自己 phantom-mesh core 上的學習助手——弱點存進**我自己的加密 owned-memory**(每次都記得、跨裝置、廠商拿不走),用**多供應商 LLM mesh** 當面試官與批改器,長 session 跑在**我的 governor** 底下。」

---

## 7. 內容層 + 「面試情境 → 解法」攻略

`content/` 下:題庫(`knowledge/`、`coding/`、`design/`,各為結構化檔)+ **`scenarios.md`**。後者 = operator 要的「**情境 → 在考什麼 → 怎麼答 → 哪個模式練**」全攻略,**同時**是工具題庫/rubric 來源 + 可單獨讀的攻略。完整內容見下節(由 6 個維度 agent 寫成)。

> The full 6-dimension scenario playbook lives in [`content/scenarios.md`](../content/scenarios.md); not duplicated here.

---

## 8. 測試 / 品質(沿用 anti-fake-green)

- 每個模式 **CLI 可達 + 真入口 e2e**:例 `tutor code` 真的把解答丟 runner 跑出 pass-rate、`tutor quiz` 真的更新 SRS+weak_spots、`tutor interview` 真的多輪且讀 weak_spots。NOT library-only。
- LLM 全程 stub(`PHANTOM_TUTOR_STUB_LLM=1`)→ hermetic、CI 可跑、零網路/金鑰。
- **絕不碰真 `~/.phantom-mesh`**;tmp HOME。lint(ruff)clean。

---

## 9. 分階段(operator 選「先搭骨架再深化」)

- **Phase 1(骨架打通)**:repo + 套件骨架 + `weak_spots` 脊椎 + SRS + 4 模式薄版(各能端到端跑一條)+ `tutor today` loop + seed 內容 + `scenarios.md` 攻略 v1 + 每模式一條 e2e。**能真的跑一輪。**
- **Phase 2+(逐個做透)**:題庫擴充、LLM 評分品質、面試官追問深度、weak_spots 接 phantom core 真記憶、governor/mesh、進度視覺化。

---

## 10. 明確排除 / 邊界

- ❌ 不 compose ai-feed/training(平行衛星,只共用 core)。❌ 不改 phantom core/apex(這是 downstream 作品,apex 規定 downstream 永不塑造產品)。
- ❌ Phase 1 不接真 owned-memory(先本地 JSON,介面預留)。❌ 不做帳號/雲端同步/付費。❌ 不爬題庫網站(seed + 自建,避版權)。❌ 不在測試碰真 LLM/真 mesh/真 ~/.phantom-mesh。

---

## 11. Repo 結構(初版)

```
phantom-tutor/
  README.md
  pyproject.toml
  phantom_tutor/
    __init__.py
    cli.py            # tutor <today|quiz|code|design|interview|weak-spots|stats>
    memory.py         # weak_spots 介面(本地 JSON → Phase2 phantom owned-memory)
    srs.py            # 間隔重複排程
    llm.py            # core LLM 封裝 + stub
    runner.py         # coding 沙箱 code-runner(subprocess+timeout+pass-rate)
    modes/
      knowledge.py  coding.py  design.py  interview.py
  content/
    scenarios.md      # 面試情境→解法 攻略
    knowledge/  coding/  design/   # 題庫
  tests/              # 每模式 e2e + 單元;全 hermetic(stub LLM, tmp HOME)
  docs/2026-06-18-phantom-tutor-design.md
```
