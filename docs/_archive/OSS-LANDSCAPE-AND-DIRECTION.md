> ARCHIVED 2026-06-19 — 內容已併入 docs/phantom-tutor.md;此為歷史版本。

# 開源生態與方向 — phantom-tutor

> 日期：2026-06-19 · 搭配 [`ROADMAP.md`](../ROADMAP.md)（狀態 SSOT）與
> [設計規格](2026-06-18-phantom-tutor-design.md)。一份**輕量**掃描：策略方向
> 已經底定（見設計規格），因此本文件僅用於釘選幾個具體的
> **adopt / reference / build** 選擇，並標示過度建構與著作權陷阱。
> 每一項外部主張都以 URL 佐證；星數為時間點快照（於 2026-06-19
> 透過 GitHub API 驗證，除非標註 `[unverified]`）。

---

## 1. 現況（已佐證）

phantom-tutor 是一個尚屬早期但**真實**的 repo。Phase-1（骨架，`14c4cc0`）與 Phase-2
（疊加深化，`f990361`）皆已合併入 `master`；工作樹可端到端執行一個
真實的 `tutor` CLI，完全封閉自足（LLM 透過 `PHANTOM_TUTOR_STUB_LLM=1` 樁化，
暫時使用 tmp `PHANTOM_TUTOR_HOME`）。今天已存在的內容：

- **`weak_spots` 自有記憶骨幹**（`memory.py`）— `record_attempt` / `due_topics` /
  `list_weak`，建立於可抽換介面背後的**本地 JSON**後端之上。這就是
  apex-② 的護城河介面；將它重新接到 phantom core 的自有記憶**尚未完成**。
- **SRS 排程器**（`srs.py`）— **手刻的 SM-2-lite**：固定 ease `2.0`、首次
  間隔 `3` 天、通過門檻 `0.6`、失敗 → 1 天。無逐卡 ease 演化，無
  difficulty/stability/retrievability 建模。*（已建出，但演算法上簡單）*
- **4 種練習模式**，全部可由 CLI 觸及並寫入骨幹：`quiz`（關鍵字評分，
  `--llm` 選用）、`code`（沙箱子行程執行器，通過率）、`design`（LLM 對照評分量表評分）、
  `interview`（模擬面試官，`--turns N` 多輪）。多數**刻意做得單薄**——一個種子規模的
  內容庫 + 簡單評分。程式碼**執行器**與 SRS 是建得較完整的部分；
  knowledge/design/interview 的評分深度則延後處理。
- **每日循環** — `tutor today` / `weak-spots` / `stats`。
- **內容層** — 種子庫（knowledge 19、coding 6、design 4）+ `content/scenarios.md`，
  6 維度面試劇本（自行撰寫，內容護城河）。

**方向（僅為定調）：** 一個**AI 工程師面試準備**的個人家教；操作者
自身的使用情境瞄準 **Agentic-Systems / AI-Platform** 職位。此利基是一個**單人、本地優先、
以自有記憶為後盾、受治理、整合 phantom-mesh** 的練習循環——明確地**不是**
題庫式 SaaS。

---

## 2. 生態盤點

### 2a. 間隔重複／排程演算法

| 專案 | URL | 星數 | 授權 | 成熟度 | 契合度／落差 |
|---|---|---:|---|---|---|
| **FSRS**（演算法 + 參考實作） | [open-spaced-repetition/free-spaced-repetition-scheduler](https://github.com/open-spaced-repetition/free-spaced-repetition-scheduler) | 672 | MIT | 成熟、有學術根據（DSR/DHP 模型：difficulty/stability/retrievability） | ⭐ **最佳 adopt。** 現代版 SM-2 後繼者；寬鬆的 MIT；可直接替換我們手刻的 SM-2-lite。 |
| **py-fsrs**（Python 實作） | [open-spaced-repetition/py-fsrs](https://github.com/open-spaced-repetition/py-fsrs) | 438 | MIT | 持續維護（2026-03 推送） | ⭐ **Python repo 的具體 adopt 對象**——一個持續維護的 MIT 套件，純排程器，無 Anki 耦合。 |
| **fsrs-rs**（Rust 實作 + 最佳化器） | [open-spaced-repetition/fsrs-rs](https://github.com/open-spaced-repetition/fsrs-rs) | 386 | BSD-3-Clause | 活躍（2026-06 推送） | 僅供參考——phantom-tutor 是 Python；若哪天有 Rust core 想要 FSRS 才相關。 |
| **anki-sm-2**（Anki 的 SM-2，封裝版） | [open-spaced-repetition/anki-sm-2](https://github.com/open-spaced-repetition/anki-sm-2) | 7 | **AGPL-3.0** | 低關注度 | ⚠️ AGPL——授權不相容的地雷；**跳過**，py-fsrs 才是 MIT 的路線。 |
| **Anki**（完整應用程式） | [ankitects/anki](https://github.com/ankitects/anki) | 28.6k | AGPL-3.0（桌面版） | 非常成熟 | **僅供參考** SRS UX／排程構想；切勿 vendor 其程式碼（AGPL）——adopt 的是 FSRS 這個演算法，不是 Anki 這個應用程式。 |

### 2b. 面試準備內容與學習計畫

| 專案 | URL | 星數 | 授權 | 成熟度 | 契合度／落差 |
|---|---|---:|---|---|---|
| **system-design-primer** | [donnemartin/system-design-primer](https://github.com/donnemartin/system-design-primer) | 353k | CC BY 4.0（API 上為 `NOASSERTION`） | 非常成熟 | ⭐ **Reference** `design` 模式評分量表結構與主題涵蓋面。CC-BY = 須署名，不可整批複製進出貨內容庫。 |
| **coding-interview-university** | [jwasham/coding-interview-university](https://github.com/jwasham/coding-interview-university) | 353k | **CC-BY-SA-4.0** | 非常成熟（DSA 學習計畫） | **Reference** 編碼主題分類法。⚠️ **CC-BY-SA 是 share-alike（具傳染性）**——汲取*結構／構想*，切勿把文字貼進我們的內容樹。 |
| **interactive-coding-challenges** | [donnemartin/interactive-coding-challenges](https://github.com/donnemartin/interactive-coding-challenges) | 31.5k | CC BY 4.0（`NOASSERTION`） | 成熟但停滯（2024） | Reference 自行撰寫 DSA 題目*形態*與測試模式。並非可倚賴的即時題庫。 |

### 2c. AI 家教／模擬面試／LLM 評估代理

| 專案 | URL | 星數 | 授權 | 成熟度 | 契合度／落差 |
|---|---|---:|---|---|---|
| **Interviewer**（AI 模擬面試官，可本地運行） | [IliaLarchenko/Interviewer](https://github.com/IliaLarchenko/Interviewer) | 114 | Apache-2.0 | 規模小、停滯（2025-03） | **Reference** 模擬面試 UX（LLM+STT+TTS，自帶／本地模型）。架構上相鄰但呈應用程式形態，不是可包裹的函式庫。 |
| **RAGAS**（LLM-as-judge 評估指標） | [explodinggradients/ragas](https://github.com/explodinggradients/ragas) | ~4k `[unverified exact]` | Apache-2.0 | 活躍、YC 投資 | **Reference** 評分量表（faithfulness／answer-relevance／position-bias 緩解）。我們的 `scenarios.md §C-4` 已反映此思路；借用模式，勿引入相依。 |

> 已掃描但**刻意略過**作為直接選擇的對象：完整的閃卡應用程式
>（Anki/Mochi/RemNote——應用程式而非函式庫；AGPL 或閉源）、LeetCode 爬蟲類 repo
>（著作權／ToS 風險），以及重量級評估平台（對單人家教而言過度建構）。

---

## 3. 建議方向（adopt / wrap / reference / build）

| 決策 | 內容 | 理由 |
|---|---|---|
| ⭐ **ADOPT** | **py-fsrs (MIT)** 取代 `srs.py` 中手刻的 SM-2-lite | FSRS 是現代、有學術根據的 SM-2 後繼者；MIT 授權乾淨；替換動作藏在既有的 `next_interval_days`／`is_due` 接縫背後，因此低風險且為疊加式。讓「越用越懂你」的護城河更鋒利（更精準校準的再現）。 |
| **WRAP（稍後）** | 在既有 `memory.py` 介面背後接上 phantom **core 自有記憶**；以 phantom **governor/mesh** 環繞長時間工作階段 | apex-② 護城河與 ④-受治理的差異化點。同一個可抽換接縫已就位——這是後端重新接線，不是重寫。 |
| **REFERENCE** | system-design-primer（design 評分量表／主題）、interactive-coding-challenges（DSA 題目形態）、RAGAS（judge-bias 評分量表）、Interviewer（模擬 UX） | 汲取*構想與結構*以撰寫我們**自己的**內容／評分量表；須署名，切勿 vendor。 |
| **BUILD（持續擁有）** | `runner.py`（沙箱程式碼評審）、`content/scenarios.md`（6 維度劇本）、`weak_spots` 資料模型、模式黏合層 | 這些是產品的識別與內容護城河——自行撰寫，無外部耦合（依設計規格 §2/§10）。 |
| **NEVER** | 爬取 LeetCode/HackerRank 等題庫；把 AGPL 或 CC-BY-SA *文字* vendor 進出貨內容 | 著作權／ToS／share-alike 污染。種子 + 自行撰寫是已鎖定的政策（設計規格 §10、ROADMAP「不在範圍內」）。 |

---

## 4. 分階段路徑（輕量）

1. **快速高價值（現在）：** 把 SM-2-lite → **py-fsrs** 替換到 `srs.py` 接縫背後（便宜、
   收斂、磨利再現護城河）。內容庫維持自行撰寫，僅就*結構*參考
   CC 授權的學習 repo。
2. **護城河（Phase-3 旗艦）：** 把 `memory.py` 重新接到 phantom core 自有記憶
   （加密、跨裝置、供應商不可見）——頭條的 apex-② 工作。
3. **受治理差異化點：** 以 `phantom govern` 包裹長時間的面試／評分工作階段；
   把繁重評分派發到 GPU mesh 節點。
4. **深度，唯有在真實使用證明落差後才做：** 深化評分（RAGAS 風格的 judge 評分量表）、
   編碼提示分層、design 參考架構庫、更深的面試追問鏈。

---

## 5. 過度建構與著作權警示

- 🚩 **在真實每日使用證明落差之前，別深化模式評分。** 這些模式*刻意*單薄；
  FSRS + 真正的自有記憶後端，今天比更豐富的評分量表更具價值。
- 🚩 **別爬取題庫網站**（LeetCode/HackerRank 等）——著作權 + ToS。種子 +
  僅自行撰寫（已鎖定的政策）。
- 🚩 **授權衛生：** Anki 桌面版與 anki-sm-2 是 **AGPL**；coding-interview-university 是
  **CC-BY-SA（具傳染性的 share-alike）**。參考構想；切勿把它們的文字／程式碼貼進
  出貨樹。優先採用 **MIT/BSD/Apache** 的選擇（py-fsrs、fsrs-rs、RAGAS、Interviewer）。
- 🚩 **別為單人家教引入重量級評估平台相依**（RAGAS 作為函式庫、langchain 等）
  ——借用*評分量表模式*，讓執行期保持小巧且封閉自足。
- 🚩 **別朝題庫 SaaS／帳號／雲端同步分岔**——依設計規格不在範圍內；
  此利基是自有記憶 + 受治理 + 整合 mesh 的*個人*循環。

---

## 方向升級:phantom-tutor 作為「人生財富最大化求職 copilot」

> 本節是對前述方向的一次**升級**(append-only,前面的學習/SRS 盤點不變)。
> 前面把 phantom-tutor 定位成「AI 工程師**面試準備**家教」;這一節把它的 **#1 目的**
> 升級成「**全程求職 copilot**」——在 operator 求職期間,端到端陪他找到並**拿下**
> 那份「人生財富最大化」的工作。星數/授權為 2026-06-19 透過 GitHub API 驗證的時間點快照,
> 標 `[unverified]` 者除外。所有外部主張附 URL。

### 6. 為什麼升級:從「面試準備工具」→「全程求職 copilot」

「面試準備」只是求職漏斗的**最後一段**。一個真正的求職 copilot 應該覆蓋整條漏斗,
而且每一步都對齊**同一個目標函數**——不是「下一份薪水最大」,而是**人生財富最大化**:

```
方向定位 → 目標職缺評分 → 作品/proof-of-work 塑形 → 履歷客製 →
投遞追蹤 → 面試準備(沿用現有 4 模式) → offer/談薪
   ╲___________________ 全部最佳化同一個目標函數 ___________________╱
```

**人生財富目標函數(取代「薪資單軸」)**——求職決策同時看四個軸,而非只看薪資:

| 軸 | 問的問題 | 為什麼進目標函數 |
|---|---|---|
| **薪資天花板** | 這條路 3–5 年後的 band 能到哪? | 短期現金流,但**不是唯一**。 |
| **耐久性 / 抗 AI 取代** | 這份工作的核心技能會被 agent 自動化嗎? | 越靠平台/治理/系統設計越耐久;越是「再寫一個 RAG demo」越快被取代。 |
| **既有資產槓桿** | 我手上的作品(如自有的 agent runtime)能不能直接當這份工作的 proof-of-work? | 槓桿讓「年資淺」的弱項被作品蓋過——這是 copilot 最該放大的維度。 |
| **契合 / 黏著** | 我會不會真心投入、能不能長期複利? | 黏著 = 能待得久 = 複利;凍市場下「待得久」本身就是財富。 |

這個四軸目標函數正是**現有 104 求職資料所缺的那一層**:operator 既有的 `match_jobs.py`
打的是**關鍵字命中分**(LLM 技能 30 / ML 25 / 工程 10 / domain 10 / 經驗 / 學歷 / 地點 / 薪資 +5),
能告訴你「JD 對不對得上」,**卻不會告訴你「這份工作對你的人生財富好不好」**。
copilot 的真正增量 = 在既有命中分**之上**疊一層 wealth-score。

### 7. 它如何站在 operator 既有資產 + phantom-mesh 生態上(無 PII)

copilot **不是重起爐灶**,而是把 operator 已驗證的求職管線**模式**(scraper → clean → score → match,
已實跑數週、日更)接到 phantom-mesh 的能力上:

| 既有/生態能力 | 在 copilot 裡的角色 |
|---|---|
| **求職管線模式**(scraper → clean → score → match,既有) | 漏斗的「取得 + 初篩」段;copilot 在其輸出上疊 wealth-score,而非重寫爬蟲。 |
| **ai-feed**(產業/角色情報) | 餵「目標角色的市場訊號」——哪類平台/治理職缺在長、JD 關鍵字在變什麼。 |
| **companion**(jobseek-aging follow-up) | 投遞後的**時效追蹤**:哪家投了 N 天沒回、該 follow-up、面試後 thank-you。 |
| **weak_spots 自有記憶脊椎**(本工具核心) | 把「目標角色要求 vs 我的技能」的**落差**當 weak_spot 追蹤;SRS 回沖最該補的缺口。 |
| **governor + 手機核准**(apex-④) | 任何**對外動作**(送出申請、寄信、貼文)走 PreToolUse gate → 手機核准才執行。這是把「自動投遞」做得**合規**的唯一正確方式。 |

護城河 = **本地優先 + 你自己這場求職的 owned-memory + 沒有任何 SaaS 在做的 wealth-objective 評分**。
JobScan / LinkedIn 之流握的是「別人的資料 + 雲端」;copilot 握的是「**你的**漏斗 + 你的弱點 + 你的目標函數」,加密、廠商看不到。

### 8. 求職-copilot 開源生態盤點

#### 8a. 職缺爬取 / 聚合

| 專案 | URL | 星數 | 授權 | 成熟度 | 契合度／落差 |
|---|---|---:|---|---|---|
| **JobSpy** | [speedyapply/JobSpy](https://github.com/speedyapply/JobSpy) | 3.7k | MIT | 活躍(2026-02 推送) | ⭐ **最佳 wrap 對象**(海外板)。一個 lib 併爬 LinkedIn/Indeed/Glassdoor/Google/ZipRecruiter;MIT 乾淨。**但** LinkedIn 約第 10 頁就 rate-limit,且爬取本身有 ToS 風險——**必須包在 governor 後、限速、僅供個人**。台灣 104 不在其覆蓋內,operator 既有的 104 管線仍是本地主力。 |
| **JobFunnel** | [PaulMcInnis/JobFunnel](https://github.com/PaulMcInnis/JobFunnel) | 2.2k | MIT | ⚠️ **已 archived**(2025-12) | **僅供參考**「多板 → 去重 → 單一表格」的資料模型。作者明說現代求職板的反爬已讓純 HTML 爬法失效——**別 fork,別當即時來源**;借其 schema 概念即可。 |
| **py-linkedin-jobs-scraper** | [spinlud/py-linkedin-jobs-scraper](https://github.com/spinlud/py-linkedin-jobs-scraper) | 484 | MIT | 中等(2025-03) | 參考級。單板(LinkedIn)、瀏覽器自動化、脆弱且 ToS 風險高。JobSpy 已涵蓋且更廣,**不需要**它。 |

#### 8b. 履歷 / CV 最佳化 + ATS 匹配

| 專案 | URL | 星數 | 授權 | 成熟度 | 契合度／落差 |
|---|---|---:|---|---|---|
| **Resume-Matcher** | [srbhr/Resume-Matcher](https://github.com/srbhr/Resume-Matcher) | 27.4k | Apache-2.0 | 非常活躍(2026-06 推送) | ⭐ **最佳 reference**(履歷 × JD 對標)。本地、開源、把履歷對 JD 解析 + 給關鍵字/ATS 洞見。Apache-2.0 友善。借其**評分量表/關鍵字 gap 思路**接到 copilot 的 wealth-score,**不必整包 vendor**(它是 Next.js+FastAPI 全棧 app,對單人 CLI 過重)。 |
| **Reactive-Resume** | [AmruthPillai/Reactive-Resume](https://github.com/AmruthPillai/Reactive-Resume) | 38.7k | MIT | 非常成熟、活躍(2026-06) | **Reference/可選自架**。MIT 的履歷建置器;若要「多版本履歷對多目標叢集」的**渲染/版本管理**,自架它比自己寫好。copilot 不該重造履歷編輯器——**reference 它,必要時自架,別內嵌**。 |
| **OpenResume** | [xitanggg/open-resume](https://github.com/xitanggg/open-resume) | 8.7k | **AGPL-3.0** | 停滯(2024-10) | ⚠️ **AGPL = 授權地雷** + 已停滯。其 ATS-readability parser 構想可參考,但**切勿 vendor 程式碼**。要 ATS 對標走 Apache 的 Resume-Matcher。 |

#### 8c. LLM 職缺匹配 / 排序 / 自動投遞 copilot

| 專案 | URL | 星數 | 授權 | 成熟度 | 契合度／落差 |
|---|---|---:|---|---|---|
| **AIHawk / Auto_Jobs_Applier** | [feder-cr/Auto_Jobs_Applier_AIHawk](https://github.com/feder-cr/Auto_Jobs_Applier_AIHawk)(已更名/轉址至 `feder-cr/Jobs_Applier_AI_Agent_AIHawk`) | 29.9k | **AGPL-3.0** | ⚠️ **已 archived**(2026-05);原作者轉商業化 AIHawk,OSS 由社群接手、fork 林立 | 🚩 **DON'T adopt(盲目自動投遞)**。它示範了「LLM 客製 + 自動點擊投遞」,但**自動大量投遞踩 LinkedIn ToS、傷招募方信任、品質低**;且 **AGPL = 授權地雷**。可**reference** 其「LLM 依 JD 客製履歷段落」的局部**構想**(勿 vendor 程式碼),但 copilot 的對外投遞**一律經 governor + 手機核准、人類最後按鍵**,絕不無人值守大量送。 |

#### 8d. 薪資 / comp 情報

| 來源 | URL | 性質 | 契合度／落差 |
|---|---|---|---|
| **levels.fyi**(資料平台,非 OSS) | [levels.fyi](https://www.levels.fyi/) | 閉源、tech comp 為主、北美偏重 | 僅供**人工參考**薪資 band 校準 wealth-score 的「薪資天花板」軸。**無開源資料集授權**;勿爬。台灣本地 band 仍以 104/實際 offer 為準。 |
| 開源 salary-data repo(零散) | [github topics: salary-data](https://github.com/topics/salary-data) `[unverified quality]` | 零散、品質參差、多為北美 | 對台灣求職幾乎無用;**不採用**。wealth-score 的薪資軸用 operator 既有的高薪/dream 切片即可。 |

#### 8e. 面試準備平台

> 已在本文件 §2b/§2c 盤點(system-design-primer、interactive-coding-challenges、Interviewer、RAGAS)。
> 升級觀點:這些仍是 copilot 漏斗**最後一段**的 reference 來源——**不變**。copilot 只是把它們
> 從「孤立的面試練習」接進「對齊 top-scored 目標角色」的端到端流程裡(見 §10)。

### 9. adopt / wrap / reference / build 裁決(求職-copilot 增量)

| 決策 | 內容 | 理由 |
|---|---|---|
| **WRAP(限速 + 治理)** | **JobSpy (MIT)** 作為**海外板**爬取後端,**包在 governor 後**、限速、僅個人用 | 省掉重寫多板爬蟲;但爬取有 ToS 風險,必須治理化、低頻、人控。台灣 104 維持 operator 既有本地管線。 |
| **REFERENCE** | **Resume-Matcher (Apache-2.0)** 的 ATS/關鍵字 gap 評分量表;**Reactive-Resume (MIT)** 的多版本履歷渲染(必要時自架);AIHawk 的「LLM 依 JD 客製履歷段落」局部能力 | 借**構想/評分量表**,不整包 vendor(全棧 app 對單人 CLI 過重)。 |
| **BUILD(持續擁有 = 護城河)** | **wealth-score**(四軸目標函數,疊在既有命中分上)、**漏斗追蹤的 owned-memory**(投遞→面試→offer 狀態 + 技能 gap 當 weak_spot)、**對齊 top-scored 角色的面試 loop** | 沒有任何 SaaS 在做「你的漏斗 × 你的弱點 × wealth-objective」;這是本地優先 + owned-memory 才做得出的差異化。 |
| 🚩 **NEVER** | 盲目自動大量投遞(AIHawk 式);爬取題庫/履歷網站超量;把 AGPL(OpenResume)程式碼 vendor 進出貨樹;重造一個求職板或履歷編輯器 | ToS / 倫理 / 授權污染 / 過度建構。對外動作一律人控 + 治理。 |

### 10. 分階段建置路徑(便宜高價值先做)

1. **`wealth-score`(現在,最便宜最高價值):** 在 operator 既有 scored-jobs CSV(命中分)**之上**,
   疊一層四軸(薪資天花板 × 耐久性 × 既有槓桿 × 契合)的 wealth-score。純讀既有 CSV + 一個評分函式,
   零爬取、零對外動作、零 ToS 風險,**立刻**把「872 個目標」排成「對人生財富最該投的前 N 個」。
2. **履歷-match 弱點回饋:** 把「top-scored 角色要求 vs 我的技能」的落差(reference Resume-Matcher 的 gap 思路)
   寫進 `weak_spots`;SRS 回沖**最該補**的缺口。把求職準備變成「會複利的 daily loop」。
3. **面試準備 loop 綁定 top 角色:** 沿用既有 4 模式(quiz/code/design/interview),但出題**對齊**
   wealth-score 排出的前幾個目標角色叢集(見 §8e)。
4. **(可選、最後)治理化的取得 + 對外:** JobSpy 海外板限速爬取 + companion 的投遞時效追蹤,
   **全部**經 governor + 手機核准。**先把前三步用熟、確認落差再做這步**——不要一開始就衝爬取/自動化。

### 11. 過度建構與倫理警示(求職-copilot 增量)

- 🚩 **別做盲目自動投遞。** AIHawk 式大量自動送踩 LinkedIn ToS、品質低、傷招募方信任。對外動作**一律人控 + governor 核准**。
- 🚩 **爬取要克制。** JobSpy 海外板 rate-limit 真實存在;低頻、個人用、治理化。**別**把 copilot 變成爬蟲農場。
- 🚩 **別重造求職板/履歷編輯器。** Resume-Matcher/Reactive-Resume 已成熟;reference 或自架,別內嵌重寫。
- 🚩 **授權衛生:** OpenResume = **AGPL**(地雷);AIHawk fork 授權雜亂(含 Commons-Clause)。優先 MIT/Apache(JobSpy、Resume-Matcher、Reactive-Resume)。
- 🚩 **wealth-score 別過度工程。** 第一版就是「既有命中分 + 四軸加權」的薄評分函式;先用真實求職證明它有用,再談 LLM 細化。
- 🚩 **薪資資料勿爬。** levels.fyi 無開源授權;台灣 band 用既有 104 切片人工校準即可。

---

## Sources

- [open-spaced-repetition/free-spaced-repetition-scheduler](https://github.com/open-spaced-repetition/free-spaced-repetition-scheduler)
- [open-spaced-repetition/py-fsrs](https://github.com/open-spaced-repetition/py-fsrs)
- [open-spaced-repetition/fsrs-rs](https://github.com/open-spaced-repetition/fsrs-rs)
- [open-spaced-repetition/anki-sm-2](https://github.com/open-spaced-repetition/anki-sm-2)
- [ankitects/anki](https://github.com/ankitects/anki)
- [donnemartin/system-design-primer](https://github.com/donnemartin/system-design-primer)
- [jwasham/coding-interview-university](https://github.com/jwasham/coding-interview-university)
- [donnemartin/interactive-coding-challenges](https://github.com/donnemartin/interactive-coding-challenges)
- [IliaLarchenko/Interviewer](https://github.com/IliaLarchenko/Interviewer)
- [explodinggradients/ragas](https://github.com/explodinggradients/ragas)
- [speedyapply/JobSpy](https://github.com/speedyapply/JobSpy)
- [PaulMcInnis/JobFunnel](https://github.com/PaulMcInnis/JobFunnel)
- [spinlud/py-linkedin-jobs-scraper](https://github.com/spinlud/py-linkedin-jobs-scraper)
- [srbhr/Resume-Matcher](https://github.com/srbhr/Resume-Matcher)
- [AmruthPillai/Reactive-Resume](https://github.com/AmruthPillai/Reactive-Resume)
- [xitanggg/open-resume](https://github.com/xitanggg/open-resume)
- [feder-cr/Auto_Jobs_Applier_AIHawk](https://github.com/feder-cr/Auto_Jobs_Applier_AIHawk)(更名 `feder-cr/Jobs_Applier_AI_Agent_AIHawk`,AGPL-3.0,archived)
- [levels.fyi](https://www.levels.fyi/)
