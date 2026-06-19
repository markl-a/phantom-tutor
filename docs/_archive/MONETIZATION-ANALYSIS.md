> ARCHIVED 2026-06-19 — 內容已併入 docs/phantom-tutor.md;此為歷史版本。

# phantom-tutor — 營利方向分析 / Monetization Analysis

> 日期:2026-06-19 · 市場資料於 2026-06-19 透過 WebSearch 調查(US-only)。
> 搭配 [`ROADMAP.md`](../ROADMAP.md)(狀態 SSOT)、[設計規格](2026-06-18-phantom-tutor-design.md)、
> [`OSS-LANDSCAPE-AND-DIRECTION.md`](OSS-LANDSCAPE-AND-DIRECTION.md)(含「人生財富最大化求職 copilot」方向)。
> 對齊 phantom-mesh 的 [`COMMERCIALIZATION-STRATEGY.md`](../../phantom-mesh-private/docs/COMMERCIALIZATION-STRATEGY.md)
> (Nabu-Casa 模式)。
>
> **本文件不含任何個人資料(PII)**:談的是產品/商業模式,不是 operator 的個人資料、求職切片或私有內容。
> 市場數字/星數凡未經本次直接抓取者標 `[unverified]`,且為 2026-06-19 的時間點快照,定價市場波動大。

---

## ① 一句話

**phantom-tutor 的 #1 目的永遠是「operator 自己天天用的個人學習/求職 copilot」;營利是**嚴格下游的副產品**——
若要營利,唯一對齊 apex 與 phantom-mesh Nabu-Casa 模式的路徑是:核心永久免費 AGPL、不另立 SaaS,
而是讓「需要雲端便利/長 session 的人」掛在 phantom-mesh 既有的那**一個**付費 zero-knowledge relay 之上,
搭配 Immich 式自願 supporter 授權;產品本身的設計**絕不可被營利反向塑造**。**並且明確不碰即時面試「外掛」這條倫理紅線。**

連結:能力與護城河見 [設計規格 §3/§6](2026-06-18-phantom-tutor-design.md);
階段路徑見 [ROADMAP「Planned-next」](../ROADMAP.md);求職 copilot 升級見
[OSS-LANDSCAPE §6–§11](OSS-LANDSCAPE-AND-DIRECTION.md)。

---

## ② 市場與玩家

> 兩個相鄰市場:**(A) 面試/求職準備**(合法、PREP-side)與 **(B) 即時面試 copilot**(倫理/ToS 紅線)。
> 定價皆為 2026-06-19 抓取的時間點快照。

| 玩家 | 定位 | 定價(2026 快照) | 模式 | 對 phantom-tutor 的啟示 |
|---|---|---|---|---|
| **LeetCode** | 題庫 + premium | ~$35/月 或 ~$159/年 | 訂閱(freemium) | 題庫廣度是別人的護城河;tutor 刻意**不**走題庫廣度,走 owned-memory 深度。 |
| **interviewing.io** | 真人模擬面試 + 免費 AI 面試官 | 真人 $100–225/場;AI 面試官免費 | 按場 + freemium AI | 「真人 marketplace」單人做不了;但「免費 AI 面試官」已是基準,**收費點不在這裡**。 |
| **Exponent**(併入 Pramp) | 課程 + 同儕模擬 + AI 回饋 | $79/月 或 年繳折 ~$12/月 `[unverified exact]` | 訂閱 | 內容/課程型,需持續產內容;單人難維持。 |
| **Interview Query** | 資料/ML 面試題 | 一次性 ~$230 `[unverified]` | 一次性/訂閱混合 | 利基題庫;與 tutor 的 AI-工程主題重疊但仍是題庫模式。 |
| **Hello Interview** | system-design AI 練習 | ~$30/月(亦有年繳/終身方案)`[unverified exact]` | 訂閱/終身混合 | 與 tutor 的 design 模式最相鄰;證明「單一垂直 + AI 回饋」有人付費,**但仍是 SaaS**。 |
| **Teal** | AI 履歷 + 投遞追蹤 | $13/週、$29/月、$79/季(無年繳) | freemium 訂閱 | 求職漏斗工具的訂閱定價帶;tutor 的求職 copilot **不**走 SaaS,走本地 + owned-memory。 |
| **Simplify** | 一鍵投遞 + 履歷 | freemium `[unverified pricing]` | freemium | 「自動填表投遞」便利層;tutor 對外動作一律治理 + 人控,不做盲投。 |
| **Google Interview Warmup** | 免費面試暖身 | **完全免費** | 免費(巨頭引流) | 免費基準的天花板;單人**無法**靠「免費面試練習」本身收費。 |
| **Final Round AI** | 即時面試 copilot(stealth) | ~$90–148/月 `[unverified exact]` | 訂閱(高價) | 🚩 **紅線區**:賣「對螢幕分享隱形的即時答案外掛」。 |
| **LockedIn AI** | 即時面試 copilot(stealth) | ~$55–120/月 `[unverified exact]` | 訂閱(高價) | 🚩 **紅線區**:同上,主打低延遲 + 隱形 overlay。 |
| **Cluely / Interview Coder 類** | 通用即時隱形 AI | 訂閱 `[unverified]` | 訂閱 | 🚩 **紅線區**:本質是「考試/面試時隱形作弊」;ToS + 信任地雷。 |

**市場主導定價模式:合法 PREP-side 玩家壓倒性是「月訂閱 freemium」**(LeetCode/Hello Interview/Teal/Exponent),
少數一次性(Interview Query)。即時 copilot 是**高價月訂閱**($55–148/月)且踩倫理紅線。
免費基準由巨頭(Google Interview Warmup)+ 開源本地工具壓到 $0。

---

## ③ 商業模式選項

| 模式 | 對 phantom-tutor 的契合 | 收入現實 | 風險 |
|---|---|---|---|
| **A. freemium 本地工具(核心免費,進階收費)** | 中:本地 + AGPL 友善,但「進階」很難不踩到 apex「核心能力不得 paywall」 | 低:本地工具的進階功能極難收費(Ollama/Jan 都免費) | 高:容易演變成「閹割核心」引發 OSS 反彈 |
| **B. SaaS 月訂閱題庫/AI 面試** | 低:**直接違反** apex(本地優先、owned-memory、無帳號雲端)與設計規格 §10 | 中:市場已驗證有人付費,但要持續產內容 + 雲端營運 | 高:單人難維持內容/營運;與本地優先衝突 |
| **C. 一次性 / 終身 supporter(Immich 式)** | **高**:零功能閘、純贊助,完全合 AGPL + apex;與 phantom-mesh Lever A 一致 | 低-中:贊助轉換率 <1%,但可前置現金流、零社群風險 | 低:幾乎無風險;天花板低 |
| **D. 開源 + 付費 hosted/relay(Nabu-Casa)** | **高(唯一主線)**:不為 tutor 另立 relay,而是**復用 phantom-mesh 那一個** zero-knowledge relay(長 session 跨裝置、手機核准 push、加密備份) | 中:綁在 mesh relay 的 12–24 個月路上;tutor 是其上的「應用情境之一」 | 中:取決於 mesh relay 本身是否起量;但無新增營運面 |
| **E. 作品 → 接案/顧問引流** | **高**:正是設計規格的「雙重目的(b)作品」;apex 允許 portfolio→接案(1+2 路線) | 中:非經常性、靠個人聲譽;但對單人最務實 | 低-中:時間換錢、不可規模化;但零產品風險 |
| **F. 內容/課程(賣攻略/教材)** | 低-中:`scenarios.md` 攻略可成內容,但會把產品拉向「內容生意」反塑產品 | 低-中:需持續產內容 | 中:內容生意的維護負擔 + 偏離工具本質 |
| **G. B2B(bootcamp/大學/企業)** | 低:需 sales motion + 多租戶,單人做不了;違反個人工具優先 | 中-高(若做成) | 高:需銷售組織;完全偏離 apex 的個人尺度 |
| **H. 「資料不出本機」premium** | 中:本地 + owned-memory 天生具此賣點,但「隱私本身收費」會破壞信任敘事(同 mesh §0) | 低 | 中:對隱私收費 = 砸自己招牌 |
| 🚩 **X. 即時面試 copilot(隱形外掛)** | **零(禁區)**:賣作弊 = 違反信任敘事、ToS、且與「真實能力複利」的產品目的對立 | 高(市場確實付高價) | **極高**:倫理 + ToS + 品牌自毀;**不可碰** |

**推薦排序(營利優先序,全部在「個人工具優先」前提下):**
**E(作品→接案)> C(終身 supporter)> D(綁 mesh relay)** ≫ A/F/H(邊際、條件式)≫ B/G(違 apex,不採)≫ **X(紅線,永不採)**。

---

## ④ 推薦路徑(階段式)

> 核心原則:**先做成 operator 自己天天用的工具**,其餘全是條件式下游。每階段「只在前一階段被真實使用證明後才推進」。

1. **階段 0 — 個人工具優先(現在,唯一硬目標):**
   把 [ROADMAP Planned-next](../ROADMAP.md) 做透——`weak_spots` 接 phantom core 真 owned-memory、
   求職 copilot 的 wealth-score(見 OSS-LANDSCAPE §10)。**此階段零營利動作。**
   產品好不好用,才是後面一切的前提。**如果這步沒做到「自己天天用」,後面所有營利選項都不啟動。**

2. **階段 1 — 作品 → 接案/顧問引流(E,最務實、零產品風險):**
   把 phantom-tutor 當「我把自己的 AI mesh 編成 owned-memory 學習/求職教練」的**作品**展示
   (這正是設計規格 §1 的雙重目的(b))。引流到接案/顧問/職涯本身。
   **這不增加任何產品功能、不收使用者錢、不違反任何 apex 條款**——是單人最低風險的「營利」。

3. **階段 2 — 自願終身 supporter 授權(C,前置現金、零閘):**
   *若* phantom-tutor 對外發佈且有社群,掛 Immich 式自願 supporter(零功能差異、純贊助 + CHANGELOG 致謝)。
   與 phantom-mesh 的 Lever A($29/$99)同框,可由同一個 merchant-of-record 收。**零功能閘 = 零社群風險。**

4. **階段 3 — 綁 phantom-mesh relay(D,唯一「產品型」營利,且不新增 SaaS):**
   *若且唯若* phantom-mesh 的 zero-knowledge relay 已上線——把 tutor 的「長面試 session 跨裝置、
   手機核准、加密弱點備份」做成 relay 的**應用情境之一**。**phantom-tutor 不另立任何付費後端、不另開帳號系統**;
   它只是「mesh relay 之上的一個本地 app」。relay 只搬它讀不懂的密文(同 mesh §0 的 zero-knowledge 承諾)。
   核心(4 模式、SRS、owned-memory、CLI)**永久免費**,離線完全可用。

**最低風險營利路徑一句話:** 把它做成你自己天天用且能在面試現場展示的作品(E)→ 若公開則掛零閘 supporter(C)→
唯一的「服務型」收入是讓重度使用者掛在 phantom-mesh 既有的那一個 relay 上(D)。**永不為 tutor 單獨蓋 SaaS、帳號或付費閘。**

---

## ⑤ 與 apex 的對齊 + 誠實 GTM + 風險

### 與 apex 對齊
- **個人工具優先:** phantom-tutor 的 #1 目的是 operator 天天用;設計規格 §1 的雙重目的把「作品」也只當**展示**,不當產品形塑力。
- **副業是下游、不塑造產品:** 與 phantom-mesh `COMMERCIALIZATION-STRATEGY.md §0/§註` 一致——
  「Commercialization 是 building toward the Big Goal 的下游獎勵,**絕不可反向塑造 Phantom 是什麼**」。
  本文件所有營利選項(E/C/D)都**不新增任何使用者付費才能用的核心能力**;凡會 paywall 核心或加帳號的選項(A/B/G/H)一律否決。
- **AGPL + Nabu-Casa 一致:** 核心永久免費 AGPL;唯一服務型收入復用 mesh 那**一個** zero-knowledge relay,
  不為 tutor 另立 SaaS。完全落在 mesh 的 §1「免費開源核心 + 一個雲端便利層」框架內。

### 誠實 GTM
- **收入現實:** 對單人 AGPL 工具,**最務實的單一營利選項是「作品 → 接案/引流(E)」**——
  非經常性、靠聲譽,但零產品/營運風險、零 apex 衝突。
- supporter(C)轉換率現實 **<1%**`[unverified, 借 SaaS freemium 一般值]`,只能前置小額現金流、不可當主收入。
- relay(D)綁在 mesh 自己的 **12–24 個月** relay 路上(mesh §4 自承),tutor 不縮短這條路、只是其上情境。
- **不誇大:** 面試/求職工具市場確實有人月付 $30–148,但那是**雲端 SaaS / 即時 copilot** 的收入,
  與「本地優先、owned-memory、AGPL、單人」這四個約束**結構性不相容**;不要拿那組數字當 tutor 的營收期待。

### 風險(含倫理紅線)
- 🚩🚩 **倫理紅線 — 即時面試「外掛」(模式 X):phantom-tutor 不碰、永不碰。**
  Final Round AI / LockedIn AI / Cluely 一類賣的是「對螢幕分享隱形、面試當下餵答案」的工具
  (`[unverified exact pricing]`,但市場存在、確實高價)。2026 的事實:這類工具引發大規模面試誠信危機
  (有報告稱受測者出現作弊訊號的比例顯著上升 `[unverified exact figure]`),多數 FAANG/傳統雇主明文禁止、
  後果含取消資格/撤 offer/列黑名單;雖目前多非「違法」,但屬**誤導真實能力** + 踩平台 ToS + 未取得面試官同意錄取其問題。
  **這與 phantom-tutor 的產品目的(讓你**真的變強**、能力複利)正面對立。**
  → **裁決:phantom-tutor 永遠站在 PREP-side(賽前練到強)、絕不站在 cheating-side(賽中餵答案)。**
  4 模式、wealth-score、owned-memory 全是**賽前**準備;不做任何「面試進行中即時隱形提示」功能。
- 🚩 **爬取/自動投遞風險**(求職 copilot 增量):見 OSS-LANDSCAPE §11——對外動作一律 governor + 手機核准、限速、人控;不做盲投。
- 🚩 **核心 paywall 風險:** 任何「進階功能收費」都可能滑向閹割核心 → OSS 反彈(同 mesh §2 的 Plex/Emby 教訓)。本文件以「零功能閘」鎖死此風險。
- 🚩 **隱私收費悖論:** 「資料不出本機」是賣點不是收費點;對隱私本身收費會砸信任招牌(同 mesh §0/§8)。
- 🚩 **bus-factor / 內容維護:** 單人 + 內容型模式(B/F)維護負擔高;這也是不走 SaaS/課程主線的原因之一。

---

## ⑥ 與生態整合的營利角度

- **作品 → 接案引流(主力,E):**
  phantom-tutor 是 phantom-mesh 生態最好的「會走路的 demo」之一——它在**單一垂直(AI 工程求職)**上
  把 owned-memory(apex-②)、多供應商 LLM mesh、governor(apex-④ 手機核准)全部用上。
  作為作品,它證明 operator 能把整個 mesh 編排成解決真實問題的 app;這比抽象架構圖更能引流到接案/職涯。
  **這條引流路徑零產品風險、零 apex 衝突,是單人最務實的營利。**

- **phantom-mesh relay 綁定(條件式服務型收入,D):**
  tutor 的「長 session 跨裝置、手機核准對外動作、加密弱點/漏斗備份」天生需要 NAT 穿透 + push + 加密備份——
  **正是 phantom-mesh relay($6/月 zero-knowledge)解決的那一類雜務**(mesh §1)。
  因此 tutor **不需要、也不應該**有自己的付費後端;它直接成為「為什麼值得訂 relay」的**使用情境之一**,
  幫 mesh relay 累積轉換,而 tutor 核心保持永久免費、離線可用。relay 只搬密文、讀不懂內容。

- **與其他衛星的引流綜效(非營利但放大作品):**
  設計規格 §10 明訂 tutor **不** compose ai-feed/training(平行衛星、只共用 core),維持邊界清晰;
  但作為「同一個 owned-memory + governor 生態下的一員」,它與 companion/finance 等一起,
  讓整個 phantom-mesh 的「越用越懂你 + 安全自動化」敘事更具體可信——這放大的是 mesh 的作品價值,
  間接回饋到 E(接案引流)與 D(relay 轉換)。

---

## Sources(2026-06-19 抓取;定價為時間點快照,市場波動大)

- LeetCode pricing — https://www.saasworthy.com/product/leetcode-interview/pricing
- interviewing.io pricing/alternatives — https://igotanoffer.com/blogs/tech/interviewingio-alternatives · https://www.lodely.com/blog/interviewing-io-pricing
- Exponent / Pramp / Hello Interview / Interview Query — https://leetcopilot.dev/blog/best-mock-interview-platforms-2026 · https://www.teamblind.com/post/leetcode-and-interview-query-subscription-i2nkixat
- Teal pricing — https://ophyai.com/blog/resume-writing/teal-ai-resume-builder-review · https://aichief.com/ai-resume-builder/teal-ai/
- Google Interview Warmup(free) — https://interviewsidekick.com/blog/interview-warmup · https://learningdaily.dev/is-google-interview-warmup-free-b98f4862e7c4
- Final Round AI / LockedIn AI pricing — https://www.finalroundai.com/blog/ai-tools-live-interview-support · https://www.lockedinai.com/compare/lockedinai-vs-final-round-ai · https://ophyai.com/blog/career-advice/best-ai-interview-copilot-tools-2026
- AI interview cheating ethics/ToS — https://fabrichq.ai/blogs/state-of-ai-interview-cheating-in-2026-insights-from-19-368-interviews · https://www.aceround.app/blog/is-using-ai-in-interviews-cheating/ · https://builtin.com/articles/ai-job-interview-cheating-debate · https://incruiter.com/blog/how-companies-detect-ai-assisted-interview-cheating/
- phantom-mesh commercialization model — `../../phantom-mesh-private/docs/COMMERCIALIZATION-STRATEGY.md`
