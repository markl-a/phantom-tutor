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

> **完整攻略見 [`content/scenarios.md`](../content/scenarios.md);以下為同一份內容內嵌。**


## A. Coding(DSA + ML 手刻)

這個 dimension 是 AI 工程師面試裡最「可被準備到」、也最容易因為小失誤被刷掉的一關。它通常分成兩種血型:**傳統 DSA**(跟一般 SWE 一樣)與 **ML-flavoured coding**(從零手刻 attention / softmax / kNN / k-means / Dataset+DataLoader / gradient descent / batchnorm)。很多 AI 候選人 LeetCode 練得不錯,卻在「手刻一個 numerically-stable softmax」或「自己寫 DataLoader 的 collate」上翻車,反之亦然。這一節把兩條線都拆到「情境 → 在考什麼 → 怎麼答 → 紅旗 → 怎麼用 phantom-tutor 練」。

---

### 1. 常見情境 / 題型(archetypes)

#### A. 傳統 DSA(45 分鐘、1~2 題)
依資料結構 / 技巧分,AI 職缺最常出的子集:

- **Arrays / Strings / Hashing**:Two Sum 變體、最長無重複子字串(sliding window)、anagram 分群、subarray sum = k(prefix sum + hashmap)、字串編碼/解碼。
- **Two pointers / Sliding window**:container with most water、3-sum、minimum window substring、移除重複、合併排序陣列。
- **Stack / Queue / Monotonic**:valid parentheses、daily temperatures(monotonic stack)、滑動視窗最大值(monotonic deque)、min stack。
- **Trees / BST**:DFS/BFS、最近共同祖先(LCA)、序列化/反序列化、validate BST、level-order、diameter、path sum。
- **Graphs**:number of islands(grid DFS/BFS/union-find)、course schedule(拓撲排序 + 偵測環)、Dijkstra / BFS 最短路、clone graph、word ladder。
- **DP**:climbing stairs、house robber、coin change(完全背包)、LIS、edit distance、0/1 knapsack、最大子陣列(Kadane)、unique paths。
- **Heap / Top-K**:top K frequent、merge K sorted lists、kth largest、median from data stream(雙 heap)。
- **Binary search**:旋轉陣列搜尋、find peak、search in 2D matrix、koko eating bananas(對「答案」二分)。

> AI 面試的 DSA 通常**難度落在 Easy~Medium**(尤其是 ML/Research 偏研究的職缺),但 infra / platform / MLE production 的職缺會出到 Medium~Hard,且更看重 production-quality(邊界、可讀性、測試)。

#### B. ML-flavoured「從零手刻」(這是 AI 職缺的鑑別題)
這類題目用 numpy 或 torch(禁止呼叫現成 high-level API,例如不准用 `torch.softmax`、`nn.MultiheadAttention`、`sklearn.KMeans`)。最高頻的幾顆:

1. **Numerically-stable softmax**(幾乎必考的暖身):`softmax(x) = exp(x - max(x)) / sum(...)`,要會解釋為什麼減 max。延伸:log-softmax、cross-entropy(combine log-sum-exp)、temperature。
2. **Scaled dot-product attention / self-attention**:`softmax(QKᵀ/√d_k + mask) V`。延伸:causal mask、multi-head 的 reshape、batched 版本、為何除以 √d_k。
3. **kNN classifier**:算 pairwise distance(向量化,避免 Python loop)、取 top-k、多數投票;延伸:加權投票、breaking ties、用 `argpartition` 而非 full sort。
4. **k-means**:init → assign(最近 centroid)→ update(重算 centroid)→ 收斂判斷;延伸:k-means++ init、處理空 cluster、向量化距離矩陣。
5. **Dataset + DataLoader(PyTorch)**:`__len__` / `__getitem__`、自訂 `collate_fn`(padding 變長序列)、shuffle / batch、train/val split。
6. **Gradient descent(手算梯度)**:linear regression / logistic regression 的 forward + 解析梯度 + 更新;延伸:mini-batch、learning rate、加 L2、用有限差分驗證梯度(gradient check)。
7. **BatchNorm / LayerNorm**:forward(減 mean / 除 std + γ、β)、train vs eval(running stats)、為什麼 eps;進階會問 backward。
8. **其他高頻**:sigmoid / ReLU / cross-entropy loss、cosine similarity、layer 的 forward/backward(一層 MLP 的反傳)、positional encoding、NMS(物件偵測常見)、IoU、tokenizer(BPE 簡化版)、beam search、computing perplexity。

#### C. 「實作 + 用一下」的混合題
近年很常見:**先手刻、再小規模跑起來**。例如「手刻 self-attention,然後在一個 toy tensor 上跑出 shape 對的 output」、或「實作一個 mini training loop:Dataset→DataLoader→model→loss→backward→step,跑 2 個 epoch 證明 loss 下降」。考的是你能不能把零件接成會動的東西。

#### D. Debug / 補完既有 code
給一段有 bug 的 attention 或 training loop(常見植入 bug:忘了 `model.eval()`、忘了 `optimizer.zero_grad()`、softmax 沒減 max、mask 加錯維度、broadcast 形狀錯、in-place 改壞 autograd),要你找出並修。考 production sense 與對框架的真實理解。

---

### 2. 在考什麼(各題型背後的訊號)

| 題型 | 真正評估的能力 |
|---|---|
| DSA Easy/Medium | 能否把模糊問題形式化、選對資料結構、寫出 bug-free 的乾淨 code、講對複雜度 |
| Top-K / Heap / Binary search | 是否知道「不用全排序」「對答案二分」這種 production 直覺(ML 資料量大,O(n log n) vs O(n log k) 有感) |
| softmax / cross-entropy | **數值穩定性**意識(overflow/underflow、log(0))——這是 ML 工程的基本素養 |
| attention | 對 Transformer 內部的真實理解(不是背公式):形狀、mask、√d_k、batching;能不能 from-scratch 重建 |
| kNN / k-means | **向量化**能力(會不會寫雙 for-loop)、broadcasting、複雜度意識、邊界(空 cluster、tie) |
| Dataset/DataLoader | 是否真的寫過 PyTorch 訓練 pipeline(collate/padding/shuffle 是試金石) |
| gradient descent | 數學(會不會自己推梯度)+ 能不能用 gradient check 驗證自己 |
| BatchNorm | train/eval 行為差異的理解(這題能立刻分出「只調過 API」vs「懂內部」) |
| Debug 題 | production 經驗、對 autograd / 框架陷阱的肌肉記憶 |

一句話:DSA 考「會不會寫程式」,ML-coding 考「你是不是真的懂你天天 import 的東西」。後者是 AI 職缺刷人的關鍵,因為它無法靠純背 LeetCode 過關。

---

### 3. 解法 / 答題策略(framework + worked examples)

#### 3.1 萬用流程:CEACCT(每題都照這個跑)
這是 live-coding etiquette 的骨幹,面試官明確會評分:

1. **Clarify(澄清)**:輸入範圍 / 型別 / 是否排序 / 是否有重複 / 空輸入 / 負數 / 是否 in-place / 要回傳什麼 / 規模多大(影響複雜度目標)。ML 題要問:輸入 shape?batched 與否?要不要 mask?用 numpy 還是 torch?能不能用內建 X?
2. **Examples(舉例)**:自己給 1 個正常例 + 1 個邊界例,確認你跟面試官對齊「正確答案長什麼樣」。
3. **Approach(講思路)**:**先說做法再寫**。講你想到的暴力解 → 優化解 → 為什麼。讓面試官有機會在你寫之前就糾正方向(超重要,省下整段寫錯)。
4. **Complexity(複雜度)**:在動手前說出目標 time/space,寫完再確認實際達成。
5. **Code(寫)**:邊寫邊講(think aloud)、命名清楚、先寫主幹後補邊界。卡住就講出你卡在哪,別沉默。
6. **Test(測)**:寫完**主動**用你 step 2 的例子 + 邊界 dry-run / 跑一遍,自己抓 bug。不要等面試官說「你要不要測一下」。

> 紅旗就是:聽完題目直接埋頭寫(跳過 1-4)、寫完說「好了」不測(跳過 6)、全程沉默。

#### 3.2 Worked example A — DSA:Longest Substring Without Repeating Characters
- **Clarify**:字元集?(ASCII/Unicode)空字串回 0?
- **Approach**:sliding window + hashmap 存「字元 → 最後出現 index」;右指標掃,遇到重複就把左指標跳到 `max(left, last[c]+1)`。
- **Complexity**:O(n) time、O(min(n, charset)) space。
- **Code**:
```python
def length_of_longest_substring(s: str) -> int:
    last = {}            # char -> last seen index
    left = 0
    best = 0
    for right, c in enumerate(s):
        if c in last and last[c] >= left:
            left = last[c] + 1     # 跳過重複,window 不回退
        last[c] = right
        best = max(best, right - left + 1)
    return best
```
- **Test**:`""→0`、`"abcabcbb"→3`、`"bbbbb"→1`、`"pwwkew"→3`、`"abba"→2`(這個會抓出沒寫 `last[c] >= left` 的 bug)。

#### 3.3 Worked example B — ML:numerically-stable softmax + 為什麼
- **Clarify**:輸入 1D 還是 2D(batch)?要不要沿某個 axis?
- **Approach**:直接 `exp(x)` 會 overflow(x 很大時 `exp` 爆 inf)。減去該軸的 max 後,最大項變 `exp(0)=1`,結果不變(分子分母同乘常數),數值安全。
- **Code(支援 batch、指定 axis)**:
```python
import numpy as np
def softmax(x, axis=-1):
    x = x - np.max(x, axis=axis, keepdims=True)  # 數值穩定關鍵
    e = np.exp(x)
    return e / np.sum(e, axis=axis, keepdims=True)
```
- **延伸口頭加分**:cross-entropy 不要 `log(softmax(x))`(會 log(0)),要用 log-sum-exp 合併:`logsumexp(x) - x[target]`。temperature `T`:`softmax(x / T)`。
- **Test**:`softmax([1000,1000,1000])` 不會 nan、每列和為 1、和 `scipy.special.softmax` 對齊。

#### 3.4 Worked example C — ML:scaled dot-product attention(向量化 + mask)
```python
import numpy as np
def attention(Q, K, V, mask=None):
    # Q:(..., Lq, d), K,V:(..., Lk, d)
    d_k = Q.shape[-1]
    scores = Q @ K.swapaxes(-1, -2) / np.sqrt(d_k)   # (..., Lq, Lk)
    if mask is not None:                              # mask: True=可看
        scores = np.where(mask, scores, -1e9)         # 被遮的位置 -> ~0 權重
    weights = softmax(scores, axis=-1)
    return weights @ V                                # (..., Lq, d)
```
- **必講要點**:① 除以 `√d_k` 是因為 dot product 隨維度變大、variance 變大,softmax 會飽和、梯度變小;② mask 是「在 softmax 之前」加 `-inf`(不是事後乘 0,那樣 row 和不為 1);③ causal mask 是下三角;④ 形狀全程口述。

#### 3.5 Worked example D — kNN(向量化,不准雙迴圈)
```python
def knn_predict(X_train, y_train, X_test, k=3):
    # pairwise squared dist via (a-b)^2 = a^2 - 2ab + b^2,全向量化
    d = (X_test**2).sum(1)[:, None] - 2 * X_test @ X_train.T + (X_train**2).sum(1)[None, :]
    idx = np.argpartition(d, k, axis=1)[:, :k]        # O(n) 取 top-k,不 full sort
    neigh = y_train[idx]
    # 多數投票
    return np.array([np.bincount(row).argmax() for row in neigh])
```
- **加分**:用 `argpartition` 而非 `argsort`(複雜度);講 tie-breaking;講距離度量可換 cosine。

#### 3.6 Worked example E — PyTorch Dataset + DataLoader + 變長 collate
```python
import torch
from torch.utils.data import Dataset, DataLoader
from torch.nn.utils.rnn import pad_sequence

class SeqDataset(Dataset):
    def __init__(self, seqs, labels):
        self.seqs, self.labels = seqs, labels
    def __len__(self):
        return len(self.seqs)
    def __getitem__(self, i):
        return torch.tensor(self.seqs[i]), self.labels[i]

def collate(batch):
    seqs, labels = zip(*batch)
    lengths = torch.tensor([len(s) for s in seqs])
    padded = pad_sequence(seqs, batch_first=True, padding_value=0)  # 變長 -> 對齊
    return padded, torch.tensor(labels), lengths

loader = DataLoader(SeqDataset(seqs, labels), batch_size=32,
                    shuffle=True, collate_fn=collate)
```
- **試金石**:能不能自己想到「變長序列要 custom collate_fn + padding + 回傳 lengths(給後面 pack/mask 用)」。這題答得好,基本證明你真的訓練過模型。

#### 3.7 Worked example F — gradient descent + gradient check
```python
def train_linreg(X, y, lr=0.01, epochs=100):
    w = np.zeros(X.shape[1]); b = 0.0
    n = len(y)
    for _ in range(epochs):
        pred = X @ w + b
        err = pred - y
        grad_w = (2/n) * X.T @ err          # 解析梯度
        grad_b = (2/n) * err.sum()
        w -= lr * grad_w; b -= lr * grad_b
    return w, b
```
- **加分絕招**:主動說「我可以用 finite difference 驗證梯度」:`(L(w+ε) - L(w-ε)) / 2ε ≈ grad`,證明你會自我驗證——面試官很吃這套。

#### 3.8 BatchNorm 的關鍵口述
forward:`(x - μ_B)/√(σ²_B+ε) * γ + β`;**train 用 batch 統計、eval 用 running mean/var(EMA)**;eps 防除零;backward 要會推 γ、β 與 x 的梯度(進階)。能講清楚 train/eval 差異就贏一半。

---

### 4. 常見坑 / 紅旗(這些會直接扣分或被刷)

**通用 etiquette 紅旗**
- 不澄清就寫(跳過 clarify);全程悶頭不講話(面試官無法給 hint、也看不到你思路)。
- 寫完不測、不 dry-run,等面試官抓 bug。
- 講不出複雜度,或講錯(把 O(n log n) 說成 O(n))。
- 卡住就硬撐沉默,而不是「我現在卡在 X,我想試 Y」。
- 過早優化、想一步到位寫 fancy 解,結果 bug 滿天;面試偏好「先 work 再 optimize」。

**DSA 專屬坑**
- off-by-one(window/binary search 的 `<=` vs `<`、`mid` 計算用 `lo + (hi-lo)//2` 防 overflow)。
- 沒處理空輸入 / 單元素 / 全相同 / 已排序 / 負數。
- 在迴圈裡修改正在迭代的容器;用了會 TLE 的 O(n²)。
- DP 沒定義清楚 state 與轉移就開寫。

**ML-coding 專屬坑(鑑別度最高)**
- softmax / log 沒做數值穩定(沒減 max、`log(0)`、`log(p)` 沒 clip)。**這幾乎是面試官故意埋的 trap**。
- attention 把 mask 用「事後乘 0」而非「softmax 前加 -inf」;除錯 `√d_k`;multi-head 的 reshape/transpose 維度搞錯。
- 寫雙重 Python for-loop 算距離(kNN/k-means)——面試官想看**向量化**與 broadcasting。
- k-means 沒處理**空 cluster**、沒講收斂條件、init 用全 0。
- PyTorch 訓練 loop 三大忘:忘 `optimizer.zero_grad()`(梯度累加)、忘 `model.eval()` + `torch.no_grad()`(eval 時 BN/Dropout 行為錯)、忘 `loss.backward()` 後才 `step()`。
- in-place 操作破壞 autograd(`x += ...` 對 requires_grad 的 tensor);用 `.data` 繞過 autograd。
- 把 `nn.CrossEntropyLoss` 餵已經 softmax 過的機率(它內含 log-softmax,會錯)。
- broadcasting 形狀「剛好不報錯但語意錯」(例如 `(n,) + (n,1)` 變成 `(n,n)`)——這種 silent bug 最危險,要會用 shape 假設去 dry-run。
- 宣稱「禁用內建」卻偷用 `torch.softmax` / `sklearn`。

**態度紅旗**:被指出 bug 時辯解或慌張,而不是冷靜複述、定位、修正。

---

### 5. 用 phantom-tutor 哪個模式練 + 怎麼練

phantom-tutor 四個模式對應這一關的不同肌群,建議**組合循環**而不是只用一個:

#### (a) coding-judge(跑你的 code 對 unit tests)— 這關的主力
- **練什麼**:所有「有明確 I/O 的可驗證題」——DSA 全部、以及 ML 手刻題(softmax/attention/kNN/k-means/DataLoader/gradient descent/BN)。
- **怎麼練**:
  - 建一個 **judge pack**,每題附 hidden tests + 邊界 + **數值斷言**。例如 softmax pack 要含 `softmax([1000,1000])` 不得是 nan、每軸和=1、與 reference 在 `atol=1e-6` 內對齊;attention pack 斷言 output shape、causal mask 後上三角權重為 0、row 和=1。
  - **計時模式**:每題設 25/45 分鐘 timer,模擬真實壓力。
  - **Debug 子模式**:judge 提供「植入 bug 的 attention / training loop」,你的任務是讓測試由紅轉綠——專練第 1.D 類題。
  - **向量化關卡**:同一題給「O(n²) 會超時」的大 input,逼你寫向量化版(kNN/k-means)。
  - **訊號迴圈**:judge 紅 → 把該 bug 類型(off-by-one / 忘 zero_grad / 沒減 max)記成一張 SRS 卡(見 a→b 串接)。

#### (b) knowledge-SRS(間隔重複,鎖住「為什麼」)
- **練什麼**:把容易忘的**原理與 trap** 變成卡片,讓你在面試能脫口而出(口頭加分項)。
- **卡片範例**:「softmax 為何減 max?」「attention 為何除 √d_k?」「BN 在 train vs eval 的差別?」「CrossEntropyLoss 該餵 logits 還是機率?」「argpartition vs argsort 複雜度?」「mask 為何 softmax 前加 -inf 而非事後乘 0?」「optimizer.zero_grad 為何必要?」
- **怎麼練**:每天 5~10 張,coding-judge 翻車的每個 bug 自動沉澱成一張卡(failure → flashcard 管線)。這樣 code 與口頭解釋同步變強。

#### (c) interview-mock(LLM 面試官,專打你的弱點)
- **練什麼**:完整 live-coding **etiquette**(CEACCT 流程)+ think-aloud + 被追問時的應變。
- **怎麼練**:
  - 開「coding mock」,LLM 出 1 DSA + 1 ML 手刻題,**全程要求你口述**(clarify→examples→approach→complexity→code→test);LLM 故意在中途丟 follow-up(「如果輸入 1 億筆呢?」「mask 改 causal 怎麼改?」「這裡為什麼不會 overflow?」)。
  - LLM 讀你的弱點檔(來自 judge/SRS 的失敗紀錄),**針對性出題**:你總忘 zero_grad,它就多給 training-loop 題;你 softmax 老不減 max,它就連續考數值穩定。
  - 結束給 rubric 化回饋:有沒有澄清、有沒有先講思路、有沒有自測、複雜度對不對、think-aloud 清不清楚——把 etiquette 內化成反射。

#### (d) system-design(rubric 評分)— 輔助,銜接 coding 與設計
- **練什麼**:把單題放大到「設計題裡的實作決策」——例如「設計一個 mini training pipeline / 一個向量檢索服務 / 一個 batched inference server」時,coding 直覺(向量化、batching、O 複雜度、memory)會被 rubric 檢驗。
- **怎麼練**:用 system-design 模式練「**implementation-aware design**」:被問到 attention 的 KV-cache、DataLoader 的 num_workers/pin_memory、k-means 的可擴展性時,能用 coding 級別的細節回答,而不是空談架構。

**建議的一週練法(組合拳)**:每天 30 分鐘 coding-judge(2 題,1 DSA + 1 ML,計時)→ 失敗點進 knowledge-SRS(5 卡)→ 每週 2 次 interview-mock 完整跑流程 → 每週 1 次 system-design 把當週手刻過的零件接成系統。這條 judge→SRS→mock→design 的迴圈,正好覆蓋「會寫、懂為什麼、講得出、串得起來」這四層,也就是 AI coding round 真正要的四個訊號。

---

## B. ML / DL 基礎概念

### 常見情境 / 題型（archetypes）

這一輪通常是 phone screen 後的「白板觀念對話」或現場口試，面試官隨機抽 concept 然後一路追問到你卡住為止。AI 工程師（不只 research scientist）也會被問，因為他們要確認你 debug 訓練/推論問題時有 first-principles，而不是只會 call API。下面把真實會遇到的題型分群：

**A. Bias–variance / over-underfitting 診斷題**
- 「training loss 很低但 validation loss 很高，發生什麼事？你會怎麼做？」（經典 overfitting）
- 「training 跟 validation loss 都很高且接近，怎麼辦？」（underfitting / capacity 不足 / bug）
- 「validation loss 比 training loss 還低，可能嗎？為什麼？」（陷阱題：dropout 在 train 開、eval 關；regularisation；val set 剛好簡單；data leakage）
- 「我加了更多資料但模型沒變好」→ 要你判斷現在是 bias-limited 還是 variance-limited（high bias 加資料沒用，要加 capacity / 改 features）。
- 「畫出 training/val error vs model complexity 的曲線，標出 sweet spot」；進階會問 double descent。

**B. Regularisation 題（L1 / L2 / dropout / 其它）**
- 「L1 跟 L2 的差別？為什麼 L1 會產生 sparse weights？」（幾何/次微分解釋）
- 「Dropout 在做什麼？inference 時要怎麼處理？」（inverted dropout / scale by 1/(1-p)）
- 「weight decay 跟 L2 regularisation 一樣嗎？」（陷阱：在 Adam 上不一樣 → AdamW）
- 「除了這些你還會用哪些 regularisation？」（early stopping、data augmentation、label smoothing、batchnorm 的附帶效果、更小模型、ensembling）。

**C. Optimisation 題（SGD / momentum / Adam / lr schedule）**
- 「SGD 跟 Adam 差在哪？什麼時候你會選 SGD+momentum 而不是 Adam？」
- 「learning rate 太大/太小各會怎樣？你怎麼找 lr？」（lr range test、warmup、cosine decay）
- 「為什麼 Transformer 訓練幾乎都要 warmup？」（早期 Adam 的二階動量估計不穩、LayerNorm/residual 早期梯度大）。
- 「batch size 變大要怎麼調 lr？」（linear scaling rule、large-batch generalisation gap）。

**D. Backprop / 梯度題**
- 「手算一個小 network 的 backprop」或「sigmoid/softmax+cross-entropy 的梯度推導」（softmax+CE 的梯度漂亮地化簡成 ŷ − y，常考）。
- 「vanishing / exploding gradient 為什麼發生？怎麼解？」（activation 飽和、weight 連乘、深度）。
- 「ReLU 怎麼緩解 vanishing gradient？它有什麼副作用？」（dying ReLU → LeakyReLU/GELU）。
- 「gradient clipping 在解什麼問題？」（exploding，尤其 RNN）。

**E. Loss function 與 metrics 題**
- 「分類為什麼用 cross-entropy 不用 MSE？」（梯度、機率 calibration、與 MLE 的關係、MSE+sigmoid 的梯度飽和）。
- 「precision / recall / F1 解釋一遍，什麼時候看哪個？」接「class imbalance 99:1，accuracy 99% 好不好？」
- 「ROC-AUC vs PR-AUC，imbalance 下選哪個？」（PR-AUC 對 positive 稀少更敏感）。
- 「你的模型輸出 0.9 代表 90% 機率嗎？怎麼驗證 calibration？」（reliability diagram、ECE、temperature scaling、Platt/isotonic）。
- 「怎麼選 threshold？」（依 business cost、PR curve、Youden's J）。

**F. 架構機制題（CNN / RNN / LSTM / Transformer / attention）**
- 「CNN 為什麼適合影像？parameter sharing 跟 translation invariance 講一下。」算 receptive field、output size `(W−K+2P)/S+1`、參數量。
- 「RNN 為什麼難訓練長序列？LSTM 的 gate 各做什麼？」（cell state 的加性路徑解 vanishing）。
- 「寫出 scaled dot-product attention 的公式，為什麼除以 √d_k？」
- 「self-attention 的時間/記憶體複雜度？為什麼是 O(n²)？」延伸到 FlashAttention / linear attention。
- 「multi-head attention 為什麼要多頭？positional encoding 為什麼需要？」
- 「causal mask 怎麼做的？」

**G. Normalisation 題**
- 「BatchNorm 在做什麼？train 跟 inference 行為差在哪？」（running stats）。
- 「為什麼 Transformer 用 LayerNorm 不用 BatchNorm？」（batch 維度、序列長度可變、batch 依賴性）。
- 「Pre-LN vs Post-LN 差別？」（Pre-LN 訓練穩、常省 warmup）。RMSNorm 為何流行。

**H. Data split / leakage 題（最容易刷掉人）**
- 「train/val/test 怎麼切？為什麼要三份不是兩份？」
- 「給你一個情境，找出 data leakage」（time-series 用未來資料、normalize 用了全資料的 mean/std、duplicate 跨 split、target 衍生特徵、group leakage：同一病人同時在 train 跟 test）。
- 「k-fold cross-validation 什麼時候用、什麼時候不能用？」（time-series 要用 forward-chaining；grouped data 要 GroupKFold）。

---

### 在考什麼（what's really being assessed）

1. **能不能從 symptom 反推 root cause**：面試官故意給「training 好 val 差」這種觀察，看你會不會系統性地列出 hypotheses（overfit? leakage? distribution shift? bug? metric 算錯?），而不是直接喊「加 dropout」。
2. **有沒有把數學跟直覺接起來**：能講「L1 sparse 因為次微分在 0 有一段 subgradient / loss contour 碰到 L1 菱形的角」比只背「L1 會 sparse」高一個檔次。
3. **知不知道理論在實務的破綻**：weight decay≠L2 on Adam、accuracy 在 imbalance 下無意義、BatchNorm 在小 batch 失效、val<train 的多種解釋——這些「但是…」是 senior signal。
4. **debug 品味**：面對訓練爆掉，你會不會先看 loss curve、先 overfit 一個 batch（sanity check）、檢查 data pipeline，而不是亂調超參。
5. **溝通結構**：能不能先給 30 秒的精煉答案再展開，trade-off 講清楚，並主動標出你的假設。

---

### 解法 / 答題策略（frameworks + 強答案長怎樣）

**通用結構（每題都套）：定義 → 機制/為什麼 → trade-off → 實務怎麼用 → 它失效的時候**。一句話定義先穩住，再加 depth，最後主動講「但這在 X 情況會壞」展現 seniority。

**框架 1：Overfit/Underfit 診斷樹（B 類必備）**
先問自己三個量：train metric、val metric、兩者 gap。
- gap 大（train≫val 好）→ **high variance / overfit** → 解法優先序：(1) 更多/更乾淨資料或 augmentation →(2) 加 regularisation（L2、dropout、early stopping）→(3) 降 capacity →(4) ensembling。
- 兩者都差 → **high bias / underfit** → 加 capacity、訓練更久、降 regularisation、改 feature/架構、檢查 lr 太小或 optimisation 卡住。
- val 比 train 好 → 先別恐慌，講出可能：dropout/BN 在 eval 關掉、regularisation penalty 只算在 train loss、val set 太小或太簡單、**leakage 讓 val 假性容易**。
強答案會明確說「我會先確認這是 generalisation gap 還是 train/val 分布不同或 pipeline bug」——把「不是只有 overfit 一種解釋」講出來。

**框架 2：L1 vs L2 worked example**
> 「L2 加 λ‖w‖²，梯度是 2λw，對大權重懲罰大、把所有權重平滑往 0 拉但不會剛好為 0；對應 MAP 下的 Gaussian prior。L1 加 λ‖w‖，次微分在 w≠0 是 λ·sign(w)——不管 w 多小懲罰力道固定，所以能把不重要的權重一路推到剛好 0，產生 sparsity；對應 Laplace prior。幾何上：L2 的 constraint 是圓，碰到 loss 等高線通常在非軸點；L1 是菱形，角落在軸上，最佳解容易落在角→某些座標=0。實務上 sparsity 想做 feature selection 用 L1，純抗 overfit 用 L2，想兩者兼得用 Elastic Net。」

**框架 3：Softmax + Cross-Entropy 梯度（D 類最常考的推導）**
給 logits z，softmax ŷ_i = e^{z_i}/Σe^{z_j}，CE loss L = −Σ y_i log ŷ_i。
關鍵結論：∂L/∂z_i = ŷ_i − y_i。
強答案會點出意義：**梯度正比於「預測機率減 one-hot 標籤」，乾淨、沒有飽和項**，這正是 CE 比 MSE 好的原因之一——MSE+sigmoid 的梯度會多乘一個 σ'(z)，飽和區趨近 0 → 學不動。
能順手講「CE = MLE under categorical / = KL(p_data‖p_model) 常數項外」更加分。

**框架 4：Attention 公式 + √d_k**
> Attention(Q,K,V)=softmax(QKᵀ/√d_k)V。除以 √d_k 是因為 q·k 是 d_k 個乘積項相加，若每項 ~ unit variance，dot product 的 variance ≈ d_k，d_k 大時 logits 量級大 → softmax 進入飽和區、梯度極小、近乎 argmax。除以 √d_k 把 variance 拉回 ~1，保持 softmax 在有梯度的區域。

**框架 5：Class imbalance metric 決策（E 類）**
> 「先拒絕 accuracy：99:1 下全猜 majority 就 99%。我會看 confusion matrix，依商業成本決定。漏掉 positive 很貴（詐欺、癌症篩檢）→ 重 recall；誤報很貴（垃圾信誤殺正常信）→ 重 precision；要單一數字比模型用 F1（或依成本加權的 Fβ）。排序能力看 PR-AUC（imbalance 下比 ROC-AUC 更誠實，因為 ROC 的 FPR 分母是大量 negative，會被稀釋得很好看）。最後 threshold 不該預設 0.5，要在 PR curve 上依成本挑。」

**框架 6：訓練爆掉/不收斂 debug ladder（跨 C/D/G）**
講出順序就贏一半：(1) **先 overfit 單一 batch** 確認模型+loss+反向能 memorize → 不行就是 bug；(2) 看 loss curve 形狀（NaN→exploding/lr 太大/除零，平坦→lr 太小/dead ReLU/梯度消失，鋸齒→batch noise/lr 偏大）；(3) check gradient norm（exploding→clip，~0→vanishing/init/activation）；(4) 檢查 data pipeline、normalisation、label 對齊；(5) 才開始調 lr/schedule/架構。

---

### 常見坑 / 紅旗（pitfalls）

- 🚩 把任何 train>val 直接喊 overfit，不提 leakage / pipeline bug / 分布差異。
- 🚩 說 dropout inference「也要 drop」——錯。inference 全開，用 inverted dropout 在 train 時除以 (1−p) 保持期望值一致。
- 🚩 宣稱「Adam 永遠比 SGD 好」。實務上 vision 大模型常 SGD+momentum 收斂到更好的 minima/泛化；Adam 收斂快但有時泛化略差。沒講 trade-off = 紅旗。
- 🚩 「weight decay 就是 L2」——在 vanilla SGD 等價，但在 Adam 上因為被自適應學習率縮放而**不等價**，要用 AdamW 才是真 decoupled weight decay。
- 🚩 accuracy 當 imbalance 的主指標。
- 🚩 把 normalisation/feature scaling 的統計量用整個 dataset（含 test）算 → 經典 leakage；必須只 fit 在 training fold。
- 🚩 time-series 用隨機 shuffle 切 split 或 k-fold（未來洩漏到過去）。
- 🚩 BatchNorm 在 batch 很小 / batch=1 / 推論時還用 batch 統計 → 行為崩壞；要用 running mean/var。
- 🚩 ReLU dying（大段神經元永遠輸出 0、梯度 0）卻不知道，或不知道 LeakyReLU/GELU 是解。
- 🚩 把 ROC-AUC 在嚴重 imbalance 下當萬靈丹（會虛高）。
- 🚩 說「softmax 輸出就是真機率」——未校準的 NN 常 over-confident，要 calibration（temperature scaling / reliability diagram / ECE）才能這樣解讀。
- 🚩 vanishing gradient 只會背名詞，講不出機制（深層 chain rule 連乘 < 1 的因子 + 飽和 activation 的 σ'≈0）。
- 🚩 self-attention 複雜度說成 O(n) 或不知道是 O(n²·d)。
- 🚩 三份 split 講不出「test 只能碰一次；多次調 test 等於把 test 洩漏成 val」。

---

### 用 phantom-tutor 哪個模式練 + 怎麼練

**1) knowledge-SRS（觀念/公式/定義的間隔重複）— 練 A~H 的「秒答」層**
把每個高頻定義、公式、trade-off 做成 SRS 卡，目標是面試時 5 秒內反射出來：
- 公式卡：softmax+CE 梯度=ŷ−y、attention=softmax(QKᵀ/√d_k)V、CNN output size、weight-decay≠L2-on-Adam、inverted dropout 的 1/(1−p)。
- 對比卡（cloze 雙面）：L1 vs L2、SGD vs Adam、BatchNorm vs LayerNorm、precision vs recall、ROC-AUC vs PR-AUC、Pre-LN vs Post-LN。
- 「為什麼」卡：為什麼除以 √d_k、為什麼 warmup、為什麼 CE 不用 MSE、為什麼 LSTM 的 cell state 解 vanishing。
練法：每天清到期卡；答錯的卡讓系統縮短間隔。重點是把「機制一句話」也塞進卡背面，避免只記結論。

**2) coding-judge（跑你的 code 對 unit tests）— 練把理論寫成正確程式**
最能逼出真懂沒懂。建議題庫（每題有 hidden tests 驗數值正確性）：
- 純 numpy 實作 `softmax`（含數值穩定 −max trick）、`cross_entropy` 及其 backward，對拍 autograd。
- 從零 `scaled_dot_product_attention` + causal mask，驗 shape 與 mask 後 softmax 為 0。
- 手刻 2-layer MLP 的 forward+backprop，gradient check（finite difference 比對）。
- 實作 `precision_recall_f1`、`roc_auc`、`pr_auc`、`expected_calibration_error`，對拍 sklearn。
- 實作 inverted dropout（train/eval 兩模式）與 BatchNorm forward（含 running stats 更新）。
- 寫一個「正確的」train/test split 並讓測試專門抓 leakage（scaler 只能 fit train）。
判定標準是 exit-code-gated 的數值測試，逼你寫對而不是「看起來對」。

**3) system-design（LLM 依 rubric 評分）— 練把觀念組成端到端方案**
出開放題、讓評分模型對著 rubric 打分（資料切分正確性、metric 選擇是否對齊商業成本、leakage 防護、regularisation/optimisation 取捨、failure mode 是否點到）：
- 「設計一個 99:1 imbalance 的詐欺偵測訓練+評估 pipeline」rubric 要包含：時間序 split、PR-AUC/Fβ、threshold by cost、防 leakage、calibration、漂移監控。
- 「設計訓練一個會 overfit 的小資料任務的防護策略」rubric：augmentation、early stopping、cross-val、capacity 取捨。
- 「為什麼你的 Transformer 訓練不穩，設計穩定化方案」rubric：warmup+cosine、Pre-LN/RMSNorm、grad clip、lr range test、AdamW、init。
練法：先自己寫答案 → 讓 system-design 模式打分並指出漏掉的 rubric 項 → 針對缺口回頭補 SRS 卡。

**4) interview-mock（LLM 面試官追問你的弱點）— 練抗追問與口語化**
這模式價值在「會盯著你含糊的地方一直追到你露餡」，正好模擬真實口試的 follow-up 鏈。練法：
- 開一場「ML fundamentals 連環追問」：從「train 好 val 差」開始，面試官會逐層逼問（leakage? 怎麼驗? dropout 在 val 的影響? 你怎麼分辨是 overfit 還是 distribution shift?）。
- 讓 mock 面試官**讀你過去 SRS/coding-judge 的弱點清單**，專挑你錯過的卡（例如你 weight-decay≠L2 答錯過，它就會在 Adam 題上設陷阱）。
- 每場結束讓它輸出「你哪句話含糊、哪個 trade-off 沒講、哪個機制只講結論沒講原理」→ 這些直接變成新的 SRS 卡與下一輪 coding-judge 題目，形成 SRS↔judge↔design↔mock 的閉環。

**閉環建議**：先用 mock/system-design 暴露弱點 → 把弱點轉成 SRS 卡（記憶）與 coding-judge 題（手感）→ 隔幾天再用 mock 驗收。fundamentals 這一輪靠的是「反射速度 + 機制深度 + 抗追問」三者，缺一不可，四個模式剛好各補一塊。

---

## C. LLM / GenAI 工程(AI 工程師核心)

這個 dimension 是 AI 工程師面試的「主菜」。面試官假設你能寫 code(那是 coding round 的事),這裡要看的是:**你能不能把一個 LLM 系統從 demo 推到 production**——也就是面對 retrieval 噪音、hallucination、cost/latency 預算、eval 不可信、prompt injection 這些「真實世界沒有標準答案」的問題時,你的工程判斷力。以下按面試最常出現的情境拆解。

---

### 1. RAG 系統設計與除錯(最高頻,幾乎每場都會碰)

#### 常見情境/題型

- **開放設計題**:「幫公司 10 萬份內部文件(PDF/Confluence/Slack)做一個問答系統,怎麼設計?」
- **除錯題(最常見、最能拉開差距)**:「我的 RAG 上線了,但答案經常錯/答非所問/說『找不到』,你會怎麼 debug?」
- **元件深挖**:「chunk size 怎麼選?」「為什麼要 rerank?」「embedding model 怎麼挑?」「hybrid search 是什麼、為什麼需要?」
- **eval 題**:「你怎麼知道你的 RAG 變好了還變壞了?」(這題見下面第 4 節,但常跟 RAG 綁一起問)

#### 在考什麼

- 你是否理解 RAG 是一條 **pipeline**,每一段(ingestion → chunking → embedding → indexing → retrieval → rerank → prompt assembly → generation)都會獨立壞掉,而不是把它當一個黑盒。
- 你能不能**定位失敗發生在 retrieval 還是 generation**——這是 RAG debug 的分水嶺,弱候選人一上來就調 prompt,強候選人先量 retrieval recall。
- 你對 embedding/向量檢索的**直覺與 tradeoff**(語意 vs 關鍵字、recall vs precision、cost vs quality)。

#### 解法/答題策略

**設計題的骨架(照這個順序講,面試官會覺得你做過):**

1. **先問需求再設計**(這一步就篩掉一半人):資料量級、更新頻率、查詢型態(事實型 vs 摘要型 vs 多跳推理)、latency/cost 預算、是否需要引用來源、誰是使用者(內部員工容忍度高 vs 對外客戶零容忍)。
2. **Ingestion & chunking**:依文件結構切(Markdown 標題、PDF section),而非盲目固定 token 數;典型 256–512 token + 10–20% overlap 起步,但**明說「這要靠 eval 調,不是拍腦袋」**。提 structure-aware chunking、保留 metadata(來源、標題、日期)供 filter 與引用。
3. **Embedding & index**:挑 model 看 MTEB + 自己 domain 的 retrieval eval,而非只看排行榜;維度/成本/是否要 fine-tune embedding。Index 用 HNSW(ANN),談 recall/latency 旋鈕。
4. **Retrieval = hybrid**:dense(語意)+ sparse(BM25/關鍵字)做 hybrid,因為純向量會漏掉專有名詞、產品代號、錯字;用 RRF(Reciprocal Rank Fusion)融合。
5. **Rerank**:retrieve top-50/100 → cross-encoder reranker → 取 top-5 餵 LLM。一句話講清為什麼:**bi-encoder(embedding)為了速度把 query 和 doc 分開編碼會損失精度,cross-encoder 同時看 query+doc 精度高但慢,所以「廣撒網用 bi-encoder,精挑用 cross-encoder」**。
6. **Generation**:prompt 裡強制「只根據提供的 context 回答,沒有就說不知道,並標註來源編號」。
7. **Eval & 監控**(沒講這段=紅旗):見第 4 節。

**除錯題的標準打法(背起來,這是送分題)——把問題二分到 retrieval vs generation:**

> 「我會先做 **retrieval/generation 二分**。拿一批已知答案的問題,檢查**正確的 chunk 到底有沒有被retrieve 進來**(量 retrieval recall@k / context precision)。
> - 如果**正確 chunk 根本沒進來** → 問題在 retrieval:可能 chunking 把答案切斷了、embedding model 不適合這個 domain、缺 hybrid 導致關鍵字漏掉、或 k 太小。
> - 如果**正確 chunk 進來了但答案還是錯** → 問題在 generation:prompt 沒約束好、context 太長被『lost in the middle』、模型無視 context 用內部知識亂答(這時加引用要求 + 降溫 + 重排 context 順序)。」

這個「先二分再對症下藥」的回答方式,比任何單一技巧都更能讓面試官打高分,因為它展現的是**系統性 debug 方法論**而非背招式。

#### 常見坑/紅旗

- 紅旗:一聽到 RAG 不好就說「換更大的 model / 調 prompt」——沒有先量 retrieval。
- 紅旗:固定 chunk size 講死一個數字當聖經,不提「要靠 eval 決定」。
- 紅旗:不知道 rerank 為何存在,或把 reranker 跟 embedding model 混為一談。
- 坑:忘了 **chunk 切斷語意**(答案橫跨兩個 chunk);忘了 metadata filter(時間/權限);忘了 **lost-in-the-middle**(把最相關的放中間反而被忽略);忘了文件會更新需要 re-index 策略。
- 坑:評估只看「我覺得變好了」,沒有 golden set。

---

### 2. Agents 與 Tool-use

#### 常見情境/題型

- 「設計一個能查資料庫、呼叫 API、訂會議的 agent。」
- 「你的 agent 卡在無限迴圈 / 一直呼叫錯工具 / 中途放棄,怎麼辦?」
- 「single agent 配很多 tool vs multi-agent,怎麼選?」
- 「ReAct、function calling、planner-executor 差在哪?」

#### 在考什麼

- 你是否分得清 **「LLM 自己亂編」vs「LLM 正確地呼叫工具拿真實資料」**(tool-use 的本質是把不確定的生成外包給確定的程式)。
- 你對 agent 可靠性的工程手感:錯誤處理、迴圈上限、可觀測性、人為審核點。
- 你知不知道 **agent 越自主越不可靠**,以及什麼時候該用 deterministic workflow 取代 agent。

#### 解法/答題策略

- 強答案的核心一句:**「能用固定 workflow(prompt chain / 條件分支)解的,就不要用 autonomous agent;agent 只在『步驟與順序事先不可知』時才值得它的不可靠性成本。」** 這直接呼應業界共識(少用 framework 魔法,多用可控的 building blocks)。
- 講 tool-use 要點:tool schema 要寫清楚(name/description/參數的語意,LLM 是靠 description 選工具的)、**強制 structured output / function calling** 而非 regex 解析、每個 tool call 要有 validation + 錯誤回饋給 model 讓它重試、設**最大步數**防無限迴圈。
- 可靠性框架:**觀測(trace 每一步)→ 限制(step cap、tool allowlist、權限最小化)→ 人類審核(高風險動作 human-in-the-loop)→ 可回滾**。
- multi-agent:只在子任務真正獨立可並行(如「分頭查 3 個來源再彙整」)時才用;否則 context 傳遞與協調成本通常不划算。

#### 常見坑/紅旗

- 紅旗:把所有東西都做成 autonomous agent,炫技但沒講可靠性與成本。
- 紅旗:不設 step 上限、不處理 tool 失敗、tool 回傳直接信任不 validate。
- 坑:tool description 寫得爛導致選錯工具;沒有 idempotency 導致重試造成重複下單/重複發信;權限給太大(prompt injection 一來就能刪庫,見第 8 節)。

---

### 3. Prompt Engineering

#### 常見情境/題型

- 「這個 prompt 輸出不穩定 / 格式跑掉 / 偶爾不照指令,怎麼修?」
- 「few-shot vs zero-shot 怎麼選?」「CoT 什麼時候有用、什麼時候是浪費?」
- 「給你一個爛 prompt,當場改好。」

#### 在考什麼

- 你是把 prompt 當「碰運氣調咒語」還是當**可被 eval 驅動、可迭代的工程產物**。
- 你懂不懂便宜手段(prompt)和昂貴手段(fine-tune)的順序。

#### 解法/答題策略

- 結構化打法:**清楚角色/任務 → 明確輸出格式(最好給 schema)→ 約束與禁止 → few-shot 範例(尤其要放 edge case 與反例)→ 思考步驟(需要推理時才上 CoT)**。
- 穩定輸出三招:**降 temperature、要求 structured output(JSON schema / function calling 強制)、提供 few-shot 把格式釘死**。
- 講「prompt 要被 eval」:任何 prompt 改動都跑 golden set 比對,不靠手感。
- **答題策略的層級鐵律(被高頻追問)**:**Prompt → RAG/few-shot → Fine-tune**,先用便宜可逆的手段,證明不夠才往上爬。能說出這個順序本身就是強訊號。

#### 常見坑/紅旗

- 紅旗:無腦加「think step by step」到所有 prompt(簡單分類任務上 CoT 只增加 latency/cost 還可能變差)。
- 紅旗:prompt 塞超長、矛盾指令、把所有 instruction 堆在最後(被截斷或忽略)。
- 坑:不知道 instruction 位置會影響遵從度;不知道 delimiter / structured output 能大幅穩定格式。

---

### 4. Evals(離線/線上、LLM-as-judge、golden set)——資深度的真正分水嶺

#### 常見情境/題型

- 「你怎麼證明你的改動讓系統變好了?」(幾乎是所有題的收尾追問)
- 「你怎麼評估一個沒有標準答案的生成任務(摘要、客服回覆)?」
- 「LLM-as-judge 可靠嗎?它的 bias 是什麼?」
- 「線上怎麼監控品質?A/B 怎麼設?」

#### 在考什麼

- 這題是**junior vs senior 的照妖鏡**。能把 eval 講透的人,等於宣告「我做過真的 production」。面試官最怕的是「靠肉眼看 demo 就上線」的人。

#### 解法/答題策略

- **先分層**:
  - **Offline eval**:固定 **golden set**(代表性 + 含 edge case)、CI 裡每次改動都跑、可比對 regression。RAG 拆兩段量:**retrieval 指標(recall@k、context precision/relevance)** 與 **generation 指標(faithfulness/groundedness、answer relevance、有無幻覺)**。
  - **Online eval**:真實流量上的 **A/B test**、隱性訊號(使用者是否重問、是否複製答案、thumbs up/down、人工抽審)、線上品質監控與告警。
- **LLM-as-judge 怎麼答出深度**:它可擴展、適合無標準答案任務,但要點名它的 bias 並給對策:
  - **position bias**(偏好前/後者)→ 交換順序跑兩次取平均;
  - **verbosity/length bias**(偏好長答案)、**self-preference**(偏好同家模型);
  - 用 **pairwise 比較比絕對打分更穩**;judge prompt 要給明確 rubric;**judge 本身要被校準**(拿一批人類標註驗證 judge 與人類的 agreement)。
- **金句**:「**我不靠 vibe check,任何改動都過 golden set 的 offline eval,上線後用 A/B + 隱性訊號做 online eval,LLM-as-judge 我會先用人類標註校準它再信它。**」

#### 常見坑/紅旗

- 紅旗:「我看了幾個例子覺得不錯就上了」——沒有 systematic eval = 直接出局訊號。
- 紅旗:無條件相信 LLM-as-judge,不知道它有 bias、不校準。
- 坑:golden set 沒涵蓋 edge case、會 data leak、永遠不更新;只量最終答案不拆 retrieval/generation;沒有線上監控(offline 好不代表線上好)。

---

### 5. Fine-tuning(SFT/LoRA/QLoRA/RLHF/DPO)與「何時 fine-tune vs RAG vs prompt」

#### 常見情境/題型

- 「客戶說要 fine-tune 一個模型,你會怎麼建議?」(陷阱題:多數情況不該先 fine-tune)
- 「LoRA / QLoRA / full fine-tune 差在哪?為什麼省記憶體?」
- 「RLHF 跟 DPO 差在哪?」
- 「fine-tune 完模型『忘記』原本會的東西(catastrophic forgetting),怎麼辦?」

#### 在考什麼

- **決策框架**:你是不是無腦 fine-tune 派,還是懂得「fine-tune 是最貴最不可逆的選項,通常排最後」。
- 對參數高效微調(PEFT)機制的真實理解,而非名詞背誦。

#### 解法/答題策略

- **決策樹(必背)**:
  - 缺**知識/即時資料** → **RAG**(知識會變、要引用、要避免幻覺,fine-tune 救不了「事實更新」)。
  - 缺**格式/風格/語氣/特定 task 行為的穩定遵從** → 先 **prompt + few-shot**,真的不夠再 **fine-tune(SFT/LoRA)**。
  - 要**省 latency/把長 prompt 蒸餾進權重 / 在小模型上達到大模型行為(distillation)** → fine-tune 有價值。
  - **一句總結**:**「RAG 給知識,fine-tune 給行為;先 prompt,再 RAG,最後才 fine-tune。」**
- **機制要點**(能簡述就贏):
  - **LoRA**:凍結原權重,只訓練注入的低秩矩陣(A·B),參數量與顯存大降,可熱插拔多個 adapter。
  - **QLoRA**:把 base model **量化到 4-bit**(NF4)後再做 LoRA,讓單張消費級 GPU 也能微調大模型;省顯存但有少量精度代價。
  - **SFT vs preference 對齊**:SFT 教「正確示範」;**RLHF** = 訓 reward model + PPO,效果好但工程複雜、不穩;**DPO** 直接用 preference pairs 優化、**省掉 reward model 與 RL**,更簡單穩定,是現在的常見首選。
  - **forgetting** → 用 PEFT(LoRA)而非 full fine-tune、混入通用資料、控制 epoch/LR。
- **資料才是重點**:fine-tune 的成敗 80% 在資料品質與量,要講「我會先確認有沒有乾淨、有代表性的標註資料」。

#### 常見坑/紅旗

- 紅旗:想用 fine-tune 解「知識更新/時事/引用來源」問題(那是 RAG 的活)。
- 紅旗:說不出 LoRA 為什麼省記憶體,或把 QLoRA 跟推論時量化混為一談。
- 坑:忽略資料品質、忽略 eval(微調完不知道有沒有變好/有沒有 forgetting)、忽略不可逆與維運成本(model 要重訓、要重新評估)。

---

### 6. Context window / Hallucination / Structured output

#### 常見情境/題型

- 「context 放不下(文件太長 / 對話太久),怎麼辦?」
- 「為什麼把重要資訊放中間模型會漏掉?」(lost in the middle)
- 「怎麼降低 hallucination?」
- 「我要 100% 拿到合法 JSON,怎麼保證?」

#### 解法/答題策略

- **Context 超限**:不是塞更滿,而是**retrieve only what's needed**(好的 retrieval 本身就是 context 管理)、摘要壓縮、滑動視窗 + 對話摘要記憶、把重要內容放**開頭或結尾**避開 lost-in-the-middle。提一句「context 越長 latency/cost 越高且品質可能下降,長 ≠ 好」。
- **Hallucination 緩解(分層給)**:
  1. **接地**:RAG 提供來源 + 強制「只根據 context、無則說不知道、標引用」;
  2. **解碼**:降 temperature;
  3. **驗證**:輸出後做 groundedness check(可用 NLI / LLM-judge 驗答案是否被 context 支撐)、self-consistency、citations 可被點回原文;
  4. **eval**:用 faithfulness 指標持續量。
  5. 並承認「**無法歸零,只能降低 + 量測 + 給 fallback(說不知道、轉人工)**」。
- **Structured output 三層保證**:
  1. **function calling / JSON mode / constrained decoding(grammar/規範解碼)** 強制合法 schema;
  2. **schema 驗證(Pydantic 等)+ 失敗自動重試**(把 validation error 餵回去);
  3. few-shot 範例釘住格式。不要用 regex 硬解自由文字。

#### 常見坑/紅旗

- 紅旗:hallucination 只會答「換更強的 model」;不知道接地 + 驗證 + 量測的層次。
- 紅旗:認為「context window 變大就沒問題了」,不知道 lost-in-the-middle 與成本問題。
- 坑:structured output 靠 prompt 求神拜佛而不用 constrained decoding + 驗證重試。

---

### 7. Inference 最佳化與 cost/latency tradeoff

#### 常見情境/題型

- 「你的 LLM 服務太慢 / 太貴,怎麼優化?」(極高頻,因為這是 production 天天面對的)
- 「quantisation / KV-cache / batching / speculative decoding 是什麼、各省什麼?」
- 「first token 很慢 vs 整體吞吐低,診斷與對策?」

#### 在考什麼

- 你懂不懂 **prefill(算 prompt,compute-bound)vs decode(逐 token,memory-bandwidth-bound)** 的差別——這是所有推論優化的底層心智模型。
- 你能否把優化對應到正確的指標:**TTFT(首 token 延遲)、TPOT/inter-token latency、throughput、$/1k tokens**。

#### 解法/答題策略

- **先量再優化**:定位是 TTFT 慢(prefill / 排隊)還是 token 生成慢(decode),還是吞吐不足(batching)。
- 各招對應什麼(能一句講清就加分):
  - **KV-cache**:避免每步重算前面 token 的 attention,decode 必備;代價是顯存,長 context 會爆 → 帶出 paged attention / KV-cache 量化。
  - **Continuous/in-flight batching**(vLLM 那套):把不同長度的請求動態併批,**大幅拉高 throughput、降 $/token**,是降成本第一槓桿。
  - **Quantisation**(INT8/INT4/FP8):縮小權重、提升記憶體頻寬利用 → 更快更省顯存,代價是少量精度;區分**訓練期量化(QLoRA)vs 推論期量化**。
  - **Speculative decoding**:小 draft model 先猜多個 token,大 model 一次驗證 → **降 latency 不掉品質**(輸出分布等價)。
  - **架構/系統面**:prompt caching(共用前綴)、模型蒸餾成小模型、路由(簡單請求走小模型,難的才上大模型)、串流回應改善體感延遲。
- **Cost/latency 框架金句**:**「先量 TTFT/TPOT/throughput 定位瓶頸 → 用 continuous batching 拉吞吐降單價、KV-cache + speculative 降延遲、quantisation/蒸餾/模型路由降單位成本,而不是無腦換硬體或換最大模型。」**
- 永遠把優化跟**品質 eval 綁一起**:量化/蒸餾/換小模型後一定回跑 golden set,確認沒掉太多。

#### 常見坑/紅旗

- 紅旗:分不清 prefill/decode、不知道 LLM decode 是 memory-bound 而非 compute-bound。
- 紅旗:把 quantisation 跟 distillation 混為一談;不知道 batching 是降成本主力。
- 坑:只看平均 latency 不看 p95/p99;優化完不回測品質;用 token 計費卻不估算 input/output token 成本結構。

---

### 8. Guardrails 與 Prompt Injection / 安全

#### 常見情境/題型

- 「使用者能不能讓你的 bot 洩漏 system prompt / 忽略指令 / 執行危險操作?怎麼防?」
- 「RAG 抓到的文件裡藏了惡意指令(indirect/間接 prompt injection),agent 照做了,怎麼辦?」
- 「怎麼防止有害輸出 / PII 外洩?」

#### 在考什麼

- 你有沒有 **security mindset**:把 LLM 當成「不可信、可被操控的元件」來設計,而不是假設它聽話。
- 知不知道 **prompt injection 目前無法靠單一手段根治**,要靠縱深防禦 + 權限最小化。

#### 解法/答題策略

- **縱深防禦(分輸入/輸出/系統三層)**:
  - **輸入**:把使用者輸入與系統指令明確分隔(delimiter / 結構化),不要把 untrusted 內容當指令;對 retrieved 內容也視為不可信(間接注入)。
  - **輸出**:輸出過濾(有害內容 / PII / system prompt 外洩偵測)、structured output 限制可輸出範圍。
  - **系統/架構(最關鍵)**:**最小權限**——agent 能做的危險動作(刪資料、付款、發信)一律 **human-in-the-loop 審核或 allowlist**;沙箱化工具;把「能力」而非「prompt」當作安全邊界。
- **金句**:**「prompt injection 沒有銀彈,我不靠『請不要聽壞人的話』這種 prompt,而是假設模型會被攻破,用權限最小化 + 危險動作人工審核 + 輸入輸出過濾做縱深防禦。」**

#### 常見坑/紅旗

- 紅旗:以為「在 system prompt 寫『不要洩漏指令 / 不要照使用者的惡意要求做』就安全了」。
- 紅旗:沒想到 **indirect injection**(惡意內容藏在被 retrieve 的文件 / 網頁裡)。
- 坑:給 agent 過大權限、tool 不沙箱、輸出不過濾 PII。

---

### 9. 跨題型的「萬用強答案結構」

不管被問哪一題,套這個結構幾乎不會錯,而且正中面試官想看的東西:

1. **先澄清需求與約束**(資料、流量、latency/cost 預算、品質容忍度、是否要引用/合規)。
2. **給最簡可行解**,並明說「先上便宜可逆的版本」。
3. **指出失敗模式**(這題會怎麼壞)與**對應緩解**。
4. **怎麼量測**(offline golden set + online A/B / 隱性訊號)——**永遠以 eval 收尾**。
5. **講 tradeoff**,不假裝有完美解。

把「**先量測、便宜手段優先、承認 tradeoff、用 eval 收尾**」變成你的反射動作,就是這個 dimension 的高分公式。

---

### 用 phantom-tutor 哪個模式練 + 怎麼練

| 情境 / 題型 | 主要模式 | 怎麼練(具體) |
|---|---|---|
| 名詞與機制速記:LoRA/QLoRA、DPO vs RLHF、KV-cache、speculative decoding、bi- vs cross-encoder、hybrid search、RRF、faithfulness、lost-in-the-middle、TTFT/TPOT | **knowledge-SRS** | 把每個概念做成卡片,正面問「為什麼/差在哪/各省什麼」,背面是一句話精要 + 一個 tradeoff。每天複習,目標是**被追問時能秒答機制與代價**,而不是只認得名詞。重點卡:「fine-tune vs RAG vs prompt 決策樹」「prefill vs decode 是什麼 bound」「LLM-judge 三大 bias 與對策」。 |
| RAG 設計題、agent 設計題、inference 優化題、「系統太慢/太貴怎麼辦」 | **system-design**(LLM 依 rubric 評分) | 對著題目寫完整設計或 debug 流程,讓 judge 用 rubric 打分。**rubric 必含**:有沒有先問需求、有沒有把 pipeline 拆段、有沒有 retrieval/generation 二分、有沒有講 eval、有沒有講 cost/latency tradeoff、有沒有 fallback。刻意練「**eval 收尾**」這個常被漏掉的得分點。 |
| 寫 structured-output 解析 + 重試、寫 retrieval recall@k / RRF / chunking、寫一個 judge 校準的 agreement 計算 | **coding-judge**(跑你的 code 對 unit tests) | 出小題:① 給 schema,寫一個「呼叫 → 驗證 → 失敗把 error 餵回重試」的 wrapper;② 實作 BM25+dense 的 RRF 融合並對固定 query 驗 top-k;③ 實作 chunking with overlap 並驗證邊界不切斷;④ 寫 recall@k / context-precision 的計算。用 unit test 確保你**真的會動手做 eval 與 retrieval 邏輯**,而非只會嘴。 |
| 被追問到底(「為什麼不直接 fine-tune?」「judge 怎麼校準?」「injection 你的 prompt 防得住嗎?」)、暴露知識盲點 | **interview-mock**(LLM 面試官讀你的弱點) | 跑模擬面試,讓 interviewer **專挑紅旗追問**:每次你說「換更大的 model」就反問「先量 retrieval 了嗎」;每次漏掉 eval 就追問「你怎麼證明變好」;故意丟 prompt-injection 與 LLM-judge bias 的陷阱題。練到能反射性地**先二分、先量測、承認 tradeoff、用 eval 收尾**。事後讓它輸出你的弱點清單,回灌成 knowledge-SRS 新卡片,形成閉環。 |

**建議練法循環**:先用 **knowledge-SRS** 把機制與決策樹背到能秒答 → 用 **system-design** 練完整設計/debug 流程的結構 → 用 **coding-judge** 把「會說」變成「會做」(eval、retrieval、structured output 真的寫得出來)→ 最後用 **interview-mock** 模擬高壓追問暴露盲點,把盲點回灌成新 SRS 卡片,循環收斂。

---

## D. ML / LLM System Design

這一輪是 AI/ML 工程師面試裡分量最重、最能拉開差距的一關。面試官給你一句模糊的需求(「設計一個 RAG 客服助理」),期待你在 35–50 分鐘內把它拆成一個能上線、能擴容、能監控、能 degrade 的系統。它考的不是你會不會背 transformer 公式,而是你能不能在**模糊需求 + 多重 trade-off + 有限時間**下做出**有依據的工程決策**,並主動暴露失敗模式。下面把常見題型、評分點、答題框架、坑、以及怎麼用 phantom-tutor 練,逐一講透。

### 一、常見情境 / 題型(archetypes)

ML system design 的題目幾乎都落在這 6–8 個原型裡。先認得原型,你就知道每題的「隱藏難點」在哪:

1. **RAG 知識助理 / 文件問答 / 企業客服 bot**
   - 例:「設計一個讓員工問內部 wiki 的助理」「給法律文件做問答」「設計 Perplexity 那樣的 web-grounded 問答」。
   - 隱藏難點:chunking 策略、retrieval 品質(recall vs precision)、grounding/citation、hallucination 控制、權限(ACL-aware retrieval — A 部門不能檢索到 B 部門文件)、知識新鮮度(re-index 頻率)、prompt + context window 預算。

2. **推薦系統 / feed ranking / 你會看到的下一個影片**
   - 例:「設計 YouTube 首頁推薦」「電商『猜你喜歡』」「短影音 feed」。
   - 隱藏難點:candidate generation → ranking → re-ranking 的**多階段漏斗**、retrieval(雙塔/ANN)、特徵新鮮度、cold start(新用戶/新物品)、隱式回饋(click/watch-time)當 label 的偏差、position bias、exploration vs exploitation、real-time vs batch feature。

3. **Feature Store / ML 平台基礎設施**
   - 例:「設計一個 feature store」「怎麼解決 training/serving skew」。
   - 隱藏難點:offline(訓練,批次,點時正確 point-in-time correctness)與 online(推論,低延遲 KV store)雙寫一致、防止 label leakage、feature 版本化、backfill、materialization、time-travel join。

4. **LLM serving / inference stack**
   - 例:「設計一個自架 LLM 推論服務,QPS 5k」「多租戶 LLM gateway」。
   - 隱藏難點:KV-cache、continuous batching(vLLM/TGI)、prefix caching、tensor/pipeline parallelism、量化(INT8/FP8/AWQ/GPTQ)、autoscaling on GPU(冷啟動慢)、p50 vs p99 latency、TTFT(time-to-first-token)vs TPOT(time-per-output-token)、streaming、speculative decoding、KV-cache 記憶體 = batch×seqlen 的爆量。

5. **訓練 + 評估 pipeline / fine-tuning 平台**
   - 例:「設計一個重訓練 + 評估 + 部署的 pipeline」「設計一個離線 eval harness 評 LLM」「設計 fine-tune SFT/LoRA 流程」。
   - 隱藏難點:data versioning、reproducibility、distributed training(DDP/FSDP/ZeRO)、checkpoint、eval set 與 train set 不汙染、offline metric → online metric 落差、shadow/canary、回滾。

6. **即時詐欺偵測 / 異常偵測 / 風控**
   - 例:「設計信用卡即時詐欺偵測」「登入異常偵測」。
   - 隱藏難點:極度 class imbalance(0.1% 正樣本)、低延遲(<100ms 在交易路徑上)、label 延遲(chargeback 30–90 天後才知道真相)、concept drift(詐欺手法一直變)、precision/recall 與業務成本不對稱(漏抓 vs 誤殺)、特徵的時間視窗聚合(過去 5 分鐘刷卡次數)、feedback loop(模型擋掉的交易拿不到 label)。

7. **多模態 / 搜尋 / 語意檢索 / 內容審核**
   - 例:「設計以圖搜圖」「設計貼文違規偵測」「語意搜尋」。
   - 隱藏難點:embedding 選型、ANN index(HNSW/IVF/ScaNN)、multi-vector、人審 + 模型混合、申訴流程。

8. **Agent / 工具呼叫系統**(近一兩年新增)
   - 例:「設計一個會呼叫工具的 LLM agent」「設計一個自動化客服能改訂單」。
   - 隱藏難點:tool/function calling 可靠度、planning、guardrails、不可逆動作的審批、可觀測性、評估 agent 成功率比評估單次回答難很多。

> 小抄:聽到題目的第一件事,是把它**對號入座**到上面某個原型,然後立刻想「這原型的招牌難點是什麼」。面試官給 RAG 題,八成想聽你講 retrieval 品質、grounding、hallucination;給推薦題,想聽多階段漏斗 + cold start;給詐欺題,想聽 imbalance + label 延遲。先點到招牌難點,後面才有時間。

### 二、在考什麼(面試官真正評的維度)

強答案在面試官的 rubric 上會勾到這幾格,弱答案通常只勾到前兩格:

1. **需求澄清與問題框定**:你會不會把「設計推薦系統」逼問成可量化的問題?(目標 metric 是什麼?規模?延遲?既有資料?)不問就開幹是頭號紅旗。
2. **ML 問題建模**:你把它定義成什麼任務?(分類/排序/檢索/生成/回歸)label 從哪來?用什麼 metric?這一步定錯,後面全錯。
3. **資料與特徵**:資料從哪來、有多髒、怎麼標、怎麼防 leakage、怎麼處理 imbalance/skew。資深與否在這裡一眼看出。
4. **模型選型的取捨能力**:不是「我要用最大的模型」,而是「以這個延遲/成本/資料量,baseline 先用 X,因為 Y;若不夠再上 Z」。
5. **Serving / inference 的工程現實感**:延遲預算、batching、cache、autoscale、成本。LLM 題尤其考 KV-cache 與 batching 的理解。
6. **評估與監控**:offline metric ≠ online metric;怎麼做 A/B、shadow、canary;上線後怎麼偵測 drift、品質衰退、回饋汙染。**很多候選人完全不講 eval/monitoring,這是最大失分區。**
7. **規模與成本**:back-of-envelope 估算(QPS、儲存、GPU 數、月成本)。能不能在白板上算出「embedding 1 億筆 × 768 維 × 4 byte ≈ 300GB,塞不進單機記憶體,所以要 sharded ANN」。
8. **失敗模式與 degradation**:依賴掛了怎麼辦?retrieval 回空?LLM 超時?模型回毒?有沒有 fallback、rate-limit、circuit breaker、人類兜底。
9. **溝通與主導**:你能不能結構化地講、主動停下來確認、畫得清楚、誠實說「這我不確定,我會這樣驗證」。

### 三、解法 / 答題策略(框架 + 一個 worked example)

#### 3.1 萬用九步框架(把它背到變肌肉記憶)

把這九步當成清單,每題都走一遍,時間不夠就壓縮,但**順序不要跳、不要直接跳到模型**:

1. **澄清需求與規模(花 5–8 分鐘,別省)**
   - 功能需求:具體要做什麼?成功長什麼樣?誰用?
   - 業務目標 → ML 目標:把「提升參與度」翻成「優化 watch-time 的 ranking」,把成功翻成可量化 metric。
   - 規模:DAU / QPS(平均 + 尖峰)、資料量、物品數、文件數。
   - 約束:延遲 SLA(p99 < ?ms)、成本上限、隱私/合規、on-prem vs cloud、即時 vs 批次。
   - **把假設大聲說出來並寫在白板**:「我假設 1000 萬用戶、10 萬 QPS 尖峰、p99 200ms,對嗎?」
2. **定義 ML 問題與 metric**
   - 任務型別(分類/排序/檢索/生成/回歸)。
   - 線下 metric(AUC、NDCG、recall@k、F1、precision@k、faithfulness)與**線上業務 metric**(CTR、留存、營收、申訴率),並說明兩者怎麼關聯。
   - imbalance 的話講清楚為何 accuracy 沒用、改看 PR-AUC / recall@fixed-precision。
3. **資料**:來源、規模、labeling 策略(人標/隱式/weak supervision)、清洗、leakage 防範、train/val/test 切分(時間切分對時序資料是必須)。
4. **特徵**:user/item/context/cross 特徵;online vs offline 特徵;feature store 解 training-serving skew;embedding 怎麼來。
5. **模型選型**:**一定要先給一個簡單 baseline**(LR/GBDT/BM25/熱門榜),再講進階(雙塔、DLRM、cross-encoder、fine-tuned LLM),並說每一步「為什麼升級、升級的代價」。
6. **訓練**:batch vs online、重訓頻率、distributed(資料量大才提)、超參、reproducibility、checkpoint。
7. **Serving / inference**:畫資料流圖(request → feature fetch → candidate gen → rank → post-process → response)。講延遲預算分配、cache、batching、ANN、precompute、async。
8. **評估與監控**:offline → shadow → canary → A/B 漸進放量;線上監控 metric drift、feature drift、prediction drift、latency、cost;設 alert 與自動回滾。
9. **規模、成本、失敗模式**:back-of-envelope 估;熱點與 shard;每個依賴失敗的 fallback;graceful degradation;feedback loop 風險。

> 時間分配參考(45 分鐘):澄清 7、建模+資料+特徵 12、模型 8、serving 8、eval/monitoring 6、scale/failure 4。**一定要留時間給 eval/monitoring 與 failure**,那是區分 senior 的地方。

#### 3.2 Worked example A:RAG 內部文件問答助理

- **澄清**:幾份文件?(假設 50 萬篇,平均 3 頁)更新頻率?(每天)誰問、要不要權限隔離?(要,ACL-aware)延遲?(p95 < 3s 含生成)準確比速度重要?(對,要 citation,不能亂編)。**先把這些釘死。**
- **建模**:這是 retrieval-augmented generation,不是純生成。離線 metric:retrieval 看 recall@k / MRR,生成看 faithfulness/groundedness、answer relevance(用 LLM-as-judge + 人工標的 golden set)。線上:答對率、引用正確率、deflection rate、人工升級率。
- **資料/索引**:文件 → 清洗 → **chunking**(我會用語意/標題邊界切,512–1024 token,帶 overlap,保留 metadata:來源、權限標籤、時間)→ embedding(先用成熟 embedding 模型,維度與成本權衡)→ 寫進 vector DB(HNSW),metadata 寫進可過濾的欄位。每日增量 re-index,刪改用 soft-delete + 版本。
- **檢索**:**hybrid**(BM25 稀疏 + dense 向量)→ 合併 → **cross-encoder re-rank** top-k。**ACL filter 必須在檢索層做**(pre-filter by permission),不能檢索完才過濾(會洩漏存在性 + recall 掉)。
- **生成**:把 top-N chunk 塞進 prompt(注意 context 預算與 lost-in-the-middle),要求模型**只根據提供內容作答並標引用**,檢索為空時回「找不到」而非硬掰。
- **Serving**:request → query rewrite(可選)→ embed query → ANN + BM25 → rerank → LLM(streaming TTFT 給體感)。延遲預算:embed 30ms、檢索 50ms、rerank 100ms、LLM 生成串流。embedding/rerank 可 cache 熱門 query。
- **Eval/monitoring**:建 golden Q-A 集做迴歸;線上記錄 retrieval recall proxy、faithfulness 抽樣評、引用點擊、踩讚、升級率;偵測「答非所問率」上升。**離線過 → shadow → 小流量 canary → 放量**。
- **失敗模式**:檢索空 → 誠實回退;LLM 超時/被限流 → 退到只給檢索片段或排隊;hallucination → faithfulness 低於閾值就不顯示或加警語;新文件未索引 → 標示知識截止時間;**權限洩漏 = 最嚴重,要有測試守門**。
- **成本/規模**:50 萬 chunk × 768 維 × 4B ≈ 1.5GB 向量,單機 HNSW 可行;但若 5000 萬 chunk 就要 sharded / 量化向量。LLM 生成是主成本,用較小模型 + 好檢索常勝過大模型 + 爛檢索。

#### 3.3 Worked example B(壓縮版):即時詐欺偵測

- **澄清**:在交易路徑上嗎?(是,需 <50ms)正樣本比例?(~0.1%)label 何時到?(chargeback 延遲 30–90 天)漏抓 vs 誤殺成本?(漏抓一筆 = 損失金額;誤殺 = 客訴 + 流失,**不對稱,要可調閾值**)。
- **建模**:二元分類但看 **PR-AUC / recall@fixed-precision**,accuracy 無意義。處理 imbalance:class weight / focal loss / 下採樣多數類(別過度,保留分布)。
- **特徵**:時間視窗聚合(過去 1/5/60 分鐘該卡刷卡次數、金額、地理跳變、device fingerprint)。**training-serving skew 致命** → feature store 雙寫,確保線上算的視窗特徵和訓練時 point-in-time 一致。
- **模型**:baseline 規則引擎 + GBDT(可解釋、低延遲、表格資料王者);圖特徵/GNN 抓團夥詐欺是進階。
- **Serving**:同步打分 <50ms,GBDT 適合;高風險才走更貴模型(分級)。**人審佇列**接收灰色地帶。
- **Eval/monitoring**:label 延遲 → 用 proxy(規則命中、人審結果)做近線監控;偵測 concept drift(詐欺手法變)→ 定期重訓 + drift alert。**feedback loop 陷阱**:被擋的交易拿不到真 label → 要保留一小撮「放行對照組」收集反事實 label,否則模型越學越偏。
- **失敗模式**:模型服務掛 → fallback 到規則引擎(fail-safe,寧可保守攔);延遲超時 → 預設放行還是攔?(依風險策略,通常低額放行、高額攔)。

### 四、常見坑 / 紅旗(面試官心裡的扣分表)

- **不澄清就開幹**:直接畫架構、選最潮模型。第一紅旗。
- **跳過 baseline**:張口就上 LLM / 深度模型,不講「先用 LR/GBDT/BM25 看看」。資深的人一定先 baseline。
- **沒定義 metric,或只講 accuracy**:imbalance 還講 accuracy = 立刻露餡。排序題不講 NDCG/recall@k 也是。
- **忽略 eval 與 monitoring**:這是**最常見也最致命**的失分。設計到「模型訓好部署」就停,沒講 A/B、shadow、drift、回滾。Senior 與 junior 的分水嶺。
- **不談 training-serving skew / feature 一致性**:推薦與風控題必踩。
- **不談 data leakage / 時間切分**:時序資料用隨機切分、用未來特徵預測過去 = 嚴重。
- **沒有 back-of-envelope**:不會估 QPS/儲存/GPU 數,講不出「為什麼要 shard」。
- **LLM serving 題不懂 KV-cache / batching / TTFT vs TPOT**:只會說「加機器」,不知道 GPU 記憶體是 KV-cache 在吃、continuous batching 才是吞吐關鍵。
- **沒有失敗模式 / fallback / degradation**:假設依賴永遠在、LLM 永遠正常回。
- **RAG 題不談 hallucination / grounding / 權限**:只接個 vector DB 就當完成。
- **過度設計**:還沒問規模就上 Kafka + Flink + 多區多活。面試官會問「你真的需要嗎」。**先簡單能跑,再講何時升級**。
- **回饋迴圈盲區**:推薦/風控不講 position bias、被擋交易無 label、模型影響自己的訓練資料。
- **只講 happy path 不講冷啟動**:推薦題沒講新用戶/新物品 cold start。
- **講得發散、不收斂、不主導節奏**:每講一塊不停下來和面試官對齊優先順序。
- **嘴硬不認知**:被追問不懂的點還硬掰,而不是說「我不確定,我會這樣驗證/查」。誠實 + 驗證方法 > 假裝懂。

### 五、用 phantom-tutor 哪個模式練 + 怎麼練

把上面拆成「知識零件 → 能寫的零件 → 完整設計 → 臨場主導」四層,對應四個模式,從下往上練:

- **knowledge-SRS(間隔重複,補硬知識,先做)**
  - 做什麼:把零碎但必背的事實卡片化,確保白板上隨手就答得出。卡片例:「NDCG vs recall@k 各衡量什麼、何時用」「KV-cache 記憶體 ≈ 2×layers×heads×dim×seqlen×batch,所以長 context 會爆」「TTFT vs TPOT 差別與各自的優化手段(prefix cache / speculative decoding)」「training-serving skew 的成因與 feature store 怎麼解」「imbalance 為何看 PR-AUC 不看 accuracy」「HNSW vs IVF vs ScaNN 的 trade-off」「point-in-time correctness 是什麼、不做會怎樣」「RAG 的 lost-in-the-middle」「continuous batching 為何提升吞吐」。
  - 怎麼練:每天 15 張,把九步框架的每個術語都變一張可被反問的卡;重點背「在什麼情境用什麼 + 代價」,不是背定義。

- **system-design(LLM 依 rubric 評分,主力模式)**
  - 做什麼:給你一個原型題(RAG/推薦/feature store/LLM serving/訓練 eval/詐欺),你寫出完整九步設計,LLM 對照 rubric(澄清、建模、metric、資料、特徵、模型 baseline→進階、serving 延遲預算、eval/monitoring、scale 估算、失敗模式)逐格給分並指出缺哪格。
  - 怎麼練:第一輪「完整寫」,目標把九格全勾到;第二輪「限時 40 分鐘 + 故意只給模糊一句需求」,逼自己先澄清;第三輪挑自己最弱的格(多數人是 eval/monitoring 與 failure mode)單獨加練,讓 rubric 專評那一格。每題刻意換一個原型,確保六大原型都跑過至少兩遍。

- **interview-mock(LLM 當面試官,讀你的弱點追問,進階)**
  - 做什麼:模擬真實口頭 round。LLM 丟一句模糊需求,你一段段講,它**專挑你跳過的步驟與含糊處追問**:「你說用向量檢索,recall 不夠怎麼辦?」「QPS 多少?記憶體放得下嗎,算給我看」「label 延遲 90 天,你線上怎麼監控?」「依賴的 LLM 服務掛了?」「為什麼不先用 GBDT?」
  - 怎麼練:練「被打斷還能維持結構」、練主動停下來對齊優先順序、練誠實回「不確定 + 驗證方式」。讓 mock 記錄你的慣性弱點(例:總忘記 eval、總不做估算、被追問就發散),下一場開場就針對性壓力測。

- **coding-judge(跑你的程式對單元測試,打底子用)**
  - 做什麼:system design 是口頭的,但底層元件可以用實作來「真的懂」。用 coding-judge 練可驗證的小零件:寫一個 cosine/dot-product top-k 檢索、實作 NDCG@k / recall@k / PR-AUC 計算、寫一個簡易 token-bucket rate limiter、實作 point-in-time join 避免 leakage、寫一個 sliding-window 特徵聚合、簡易 HNSW/暴力 ANN、focal loss。
  - 怎麼練:每個 metric/元件親手寫一遍並過測,之後在 system-design 與 mock 裡你講「我會用 NDCG」時是真的知道它怎麼算、邊界(全錯/全對/部分相關)在哪,追問不慌。

> 練習編排建議:第 1 週用 knowledge-SRS 鋪硬知識 + coding-judge 把 metric/檢索零件寫過一遍;第 2–3 週每天一題 system-design 走完整九步、刻意輪原型;最後一週進 interview-mock 限時口頭、讓它讀弱點窮追,把「忘記 eval/monitoring、不做估算、被追問就發散」這三個最常見扣分點逐一磨掉。判定出師標準:任給一個原型,40 分鐘內九格全勾、主動澄清、敢算數、講得出 ≥3 個失敗模式與 fallback。

---

## E. 行為題 + 專案深挖 / 防守你的作品

行為面試與專案深挖，是「軟性題」中最被低估的硬骨頭。對 AI 工程師而言，這一輪通常由 hiring manager 或資深工程師主持，目的不是聽故事，而是用故事反推你的**工程判斷力、所有權意識、與系統性思考**。一個技術很強但講不清楚「為什麼這樣設計」的候選人，會在這輪被刷掉；反之，一個能用 STAR 把一個 bug 講成一段「我如何在不確定中做決策」的人，會被記住。以下把這一維度拆到可操作的顆粒度。

### 一、常見情境/題型(archetypes)

行為與專案題在 AI 工程師面試裡可以歸成七大類原型，每一類都有可預測的追問路徑:

**A. 困難 bug / debugging 戰役**
- 「Tell me about the hardest bug you've debugged.」
- AI 領域的特化版:「講一個 non-deterministic 的問題」「一個只在 production 重現、本地無法重現的問題」「一個你以為是模型問題、結果是資料/基礎設施問題的案例」。
- 追問會往「你怎麼縮小範圍」「怎麼確認 root cause 而不是症狀」「怎麼防止 regression」鑽。
- phantom-mesh 範例素材:`PHANTOM_HOME` 在 Windows 上解析成 OS home 而非 data-dir,導致每一張 phone-approval 卡片都不顯示(@c52e6521);或 claude 2.1.170 的 gating 用 `--permission-prompt-tool` 不會觸發、必須改用 PreToolUse hook 才真正攔得到 pre-action。後者特別好,因為它示範了「我以為是設定問題,實際是 API 行為與文件不符,我靠實測而非假設定位」。

**B. 你 own 過的專案 (project you owned)**
- 「Walk me through a project you owned end-to-end.」
- AI 版會追問:資料從哪來、怎麼評估(eval)、上線後怎麼監控、模型/prompt 怎麼迭代、成本怎麼控。
- 危險追問:「如果重做你會怎麼改?」「這個專案的 scope 是你定的還是別人給的?」(在測 ownership vs 執行者)。

**C. 衝突 (conflict)**
- 「Tell me about a disagreement with a teammate / your manager / across teams.」
- 變體:「你和一個資深工程師對架構意見不合,怎麼處理?」「PM 要砍掉你認為必要的安全機制,你怎麼辦?」
- 在測你能否「對事不對人」「用資料而非音量說服」「以及輸了之後能否 disagree-and-commit」。

**D. 取捨 (tradeoff)**
- 「Tell me about a hard technical tradeoff you made.」
- AI 版高頻:latency vs accuracy、build vs buy(自建 RAG vs 用託管)、fine-tune vs prompt vs retrieval、local model vs API、本地隱私 vs 雲端能力、自動化程度 vs 安全(governed vs fire-and-forget)。

**E. 失敗 / 犯錯 (mistake / failure)**
- 「Tell me about a time you failed / a decision you regret / something that broke in production because of you.」
- 在測誠實度與成長曲線。最致命的紅旗是「我想不到」或把失敗包裝成偽缺點(「我太追求完美」)。

**F. 影響力 / 敘事 (impact)**
- 「What are you most proud of?」「What was the impact of your work?」
- 在測你能否把工程動作翻譯成業務/使用者語言,且用數字。

**G. 捍衛你自己的架構決策 (defend your design — 這是 AI/資深職位的重頭戲)**
- 面試官會拿你 resume 或作品(如 phantom-mesh)逐項拷問:「Why local-first?」「Why owned-memory 而不是直接用 vector DB SaaS?」「Why governed 而非 fire-and-forget?」「Why this provider abstraction 而不是直接綁一家?」「Why AGPL?」
- 這類題沒有標準答案,考的是你**有沒有真的想過 alternatives、有沒有意識到自己決策的代價、能不能在被質疑時不崩潰也不硬拗**。下面第三節會給完整 worked example。

### 二、在考什麼 (what each archetype really assesses)

把表面題型對應到面試官真正想驗證的訊號:

| 題型 | 表面問題 | 真正在測 |
|---|---|---|
| 困難 bug | 你解過難題嗎 | 系統性除錯 vs 亂槍打鳥;能否區分 root cause 與症狀;能否量化「如何確認修好」 |
| 你 own 的專案 | 你做過什麼 | Ownership 邊界(你定義問題還是只執行)、端到端思維、是否懂 eval/監控/成本 |
| 衝突 | 你好不好相處 | 成熟度、用證據說服、disagree-and-commit、把人與事分開 |
| 取捨 | 你會權衡嗎 | 是否意識到「沒有免費的午餐」、有沒有明確的決策準則(decision criteria)、有沒有事後驗證取捨是否正確 |
| 失敗 | 你誠實嗎 | 心理安全感、是否會把責任外推、是否從中改了流程而非只改自己 |
| 影響力 | 你的價值 | 能否把技術翻成 outcome、用數字、區分「我做的」vs「團隊做的」 |
| 捍衛架構 | 你的判斷深度 | 是否真的考慮過 alternatives、是否認知 trade-off 的代價、被壓時的 intellectual honesty |

對 AI 工程師特別加權的訊號:**(1) 對不確定性的處理**(模型本質是機率性的,面試官想看你怎麼在 non-deterministic 系統裡做工程);**(2) eval 紀律**(會不會「我覺得變好了」就上線,還是有量化 eval);**(3) 安全/對齊意識**(尤其涉及 agent、autonomous run);**(4) 成本意識**(token/GPU 都是錢)。

### 三、解法/答題策略 (frameworks + 強答案的內容)

#### 3.1 核心骨架:STAR,但要「AI 工程師化」

STAR = Situation / Task / Action / Result。多數人講得太散,正確的時間配比是 **S+T 各 15%、A 50%、R 20%**。Action 是你拿分的地方,要講「決策」不是「步驟」。

把 STAR 升級成適合 AI 工程的 **STAR(R)**:最後多一個 **Reflection**(學到什麼、之後怎麼系統性地改),這正是面試官在失敗題與專案題裡最想聽的。

對 debugging 題,我建議內嵌一個更細的子框架 **「症狀 → 假設 → 隔離 → 驗證 → 防回歸」**:
1. 症狀:量化(「approval 卡片 0 顯示,但後端 store 明明有 pending」)。
2. 假設:列出你考慮過的多個假設(「我懷疑是前端輪詢、後端寫入、或路徑解析三者之一」)——這展示系統性。
3. 隔離:用什麼手段二分定位(log、打斷點、最小重現、對比 working/broken 環境)。
4. 驗證 root cause:你怎麼確認真因而非巧合(「我把 `PHANTOM_HOME` 印出來,發現它指向 `C:\Users\m4932` 而非 data-dir,前後端讀的是兩個 DB」)。
5. 防回歸:加 test、加 assertion、加 invariant、或統一 resolver——「我不只修 bug,我消滅了這一類 bug」。最後這句是資深訊號。

#### 3.2 捍衛架構決策的萬用模板 (the design-defense template)

被問「Why X not Y」時,**永遠不要直接辯護**,先做四步:

1. **重述約束/目標**(我的 anchor 是什麼)——把對話拉回「給定這些約束,X 是合理解」。
2. **承認 Y 的優點**(intellectual honesty,先點頭再轉折,避免防衛姿態)。
3. **給出我選 X 的 1–2 個 decision criteria**(可量化或可驗證的準則)。
4. **承認 X 的代價,並說我如何 mitigate**(顯示你知道沒有 free lunch)。

公式句型:「我的核心約束是 ___。Y 在 ___ 這點確實更好。但給定我最在意的 ___ 準則,X 勝出,因為 ___。X 的代價是 ___,我用 ___ 來緩解,且如果約束變成 ___,我會重新考慮 Y。」最後那句「如果約束變了我會換」是高手訊號——代表你的決策是 conditional 而非 dogmatic。

#### 3.3 Worked Example A — 捍衛「Why local-first / 為何 owned-memory」

> **面試官**:你這個 phantom-mesh 為什麼堅持 local-first?直接用雲端不是更省事、能力更強嗎?
>
> **強答案**:
> 「(重述約束)這個產品的 anchor 是『一個我每天都用、且會隨我複利成長的私人 AI』,而它的差異化能力是 ②owned-memory——我長期累積的對話與知識,完全由我擁有、不外流。給定這個 anchor,**隱私與資料所有權不是 feature,是 thesis**。
>
> (承認雲端優點)雲端方案確實在能力上限、零維運、跨裝置同步上都更輕鬆,如果我做的是一個泛用聊天產品,我會直接上雲。
>
> (decision criteria)但我的判準是兩個:第一,使用者的記憶資料能不能在不信任任何第三方的前提下持續累積;第二,即使我未來收掉服務,使用者的 AI 還能不能繼續跑。Local-first(backend 可以是自己的桌機,或自架的 cloud Linux sandbox)同時滿足這兩點,雲端 SaaS 兩點都不滿足。
>
> (承認代價 + mitigate)代價很實在:跨裝置同步要自己做、能力受限於本地模型、新手上手摩擦高。我的緩解是——onboarding 走 local-first 但帳號 opt-in,給三個明確 carrot(mesh 配對、金鑰備份、金鑰同步);且 provider 與 account 解耦,BYOM 的人完全不需要註冊。所以隱私是預設,雲端能力是選配,不是反過來。
>
> (conditional)如果有一天約束變成『要服務百萬不在乎隱私的使用者』,那我會承認 local-first 是錯的架構——但那不是我這個產品的定位。」

這個答案的厲害之處:它不辯護「local 比較好」這種立不住的命題,而是把問題重構成「given my thesis, local-first is forced」,並且主動承認代價、給出緩解、且劃出「什麼情況我會反悔」的邊界。

#### 3.4 Worked Example B — 捍衛「Why governed, not fire-and-forget」+ provider abstraction

> **面試官**:你的 agent 為什麼要做 governor + flight-recorder + 手機審批這麼重?讓它自己跑(fire-and-forget)不是更快?
>
> **強答案**:
> 「(約束)我的第四個能力是『safe unattended runs』——讓 agent 在我不在時也能動,但不會闖禍。這正是現有 OSS agent 普遍的缺口:它們能跑,但出事你只能事後從一堆 log 拼湊。
>
> (承認對方優點)Fire-and-forget 在 happy path 上確實又快又簡單,demo 很漂亮。
>
> (判準)但我的判準是『可逆性與可問責性』:任何高風險動作(刪檔、執行 shell、改設定)在執行『前』要能被攔截與升級到我手機審批,而不是執行後才告訴我。所以我做了 L1 governed run:L0 把 claude/codex/opencode/agy 正規化成統一事件流,L1 在外層包 governor(預設 PAUSE,高風險強制 pause)+ flight-recorder(EventStore + jsonl,逐一記成 approval_requested/execute_high/post_action_observed)+ phone(notify + inbox 可 approve/deny/stop)。關鍵實作是 claude 的 *true pre-action* gate 必須用 PreToolUse hook,因為 `--permission-prompt-tool` 實測不觸發——我為此關掉了四個 fail-open(preflight、allow:[]、permission-mode dedupe、deny-json)。
>
> (代價 + mitigate)代價是延遲與複雜度,以及『每個動作都問會很煩』的風險。緩解是 risk-classify:只有高風險動作才強制 pause,低風險直接放行;governor 預設可設定,不是寫死。所以它不是『把所有自動化變慢』,是『把不可逆的動作變成需要一次點頭』。
>
> 至於 provider abstraction——我不綁單一 CLI,是因為(a)沒有任何一家 agent CLI 的能力/可用性是穩定的,我需要 source-redundant reconcile;(b)把它們正規化成同一個事件流後,governor 與 flight-recorder 才能用同一套邏輯治理所有 provider,而不是每接一家就重寫一次治理層。代價是要為每家做 envelope 適配(像 agy 要走 native portable-pty、Windows 要處理 cmd /C),但這是一次性成本,換來的是治理層的單一實作。」

注意這裡同時回答了兩個「why not X」並且把它們**用同一條 thesis(可逆+可問責)串起來**——這讓面試官看到你的決策不是一堆獨立 hack,而是有一致的 architectural principle。

#### 3.5 影響力敘事:用「指標 + 對比 + 歸因」

弱:「我做了一個 agent 治理系統。」
強:「上線前 agent 的高風險動作 0% 可被事前攔截,出事只能事後撈 log;上線後 100% 高風險動作在執行前升級到手機審批,且每個動作都有結構化記錄可回放。我用一次 z13→ayaneo 的跨機實測驗證:flight-recorder 確實捕捉到 codex 的 command_execution + file_change tool_calls,EventStore 逐一記錄。」——有 before/after、有量化、有驗證手段。

歸因誠實也很重要:用「I」講你的決策與實作,用「we」講團隊脈絡,絕不把團隊成果整碗端走(面試官會 reference check)。

#### 3.6 失敗題的正確結構

選一個**真的失敗、但低 blast-radius、且你從中改了系統性流程**的故事。結構:錯誤 → 立即影響 → 我當下怎麼止血 → root cause 是我的什麼判斷失誤 → 我改了什麼『流程/機制』讓這類錯不再發生(不是「我以後會更小心」)。
範例骨架:「我曾假設 `dirs::home_dir()` 在 Windows 上會吃 `$HOME`,結果它不會,我的 $HOME-redirect 測試污染了真實的 `~/.phantom-mesh`。立即影響是測試互相干擾、且差點動到真實資料。止血是隔離測試環境。Root cause 是我『憑記憶假設平台行為而沒實測』。系統性修正是:引入 `PHANTOM_HOME` 作為 spec 化的 data-root override、`#[cfg(unix)]` gate 平台專屬測試、並加 `crate::env_lock`。我學到的是——跨平台假設一律要實測落地,不能靠直覺。」這比「我學到要更細心」強十倍,因為它改的是機制不是態度。

### 四、常見坑 / 紅旗 (pitfalls & red flags)

- **講步驟不講決策**:把 debugging 講成「我看 log、我改 code、它就好了」——零判斷力訊號。每個動作後面要接「為什麼這樣做、我排除了什麼」。
- **沒有 Result / 不量化**:故事爛尾,或全程沒有任何數字、對比、驗證。AI 工程師尤其要展示 eval 思維。
- **過度防衛(defending too hard)**:被問 why-not-X 時硬拗 X 全面勝出、不肯承認任何代價。面試官會故意加壓看你會不會崩;**承認代價 = 加分,不是扣分**。
- **完全沒想過 alternatives**:答不出「你考慮過什麼別的方案」——代表你只是照做,沒有真的設計。
- **偽失敗 / 偽缺點**:「我最大的失敗是太投入工作」。立刻出局。
- **把功勞整碗端走 / 把鍋全甩給別人**:衝突題裡把同事描述成笨蛋、失敗題裡 root cause 全在別人——成熟度紅旗。
- **disagree 但不 commit,或 commit 但記恨**:衝突題要展示「我據理力爭,輸了之後我全力執行團隊決定,且回頭看我能說那也是合理的賭注」。
- **故事太大講不完 / scope 模糊**:選一個 6–10 分鐘能講透、你是明確主角的故事;太大的專案會稀釋你的個人貢獻。
- **AI 特有紅旗**:把「我覺得 prompt 變好了」當成果(無 eval)、宣稱模型解決了其實是資料問題、對 agent 安全/成本毫無敏感度、把「跑得動」當成「做完了」(verification 紀律缺失)。
- **記憶不可靠**:臨場才想故事 → 卡頓、細節對不上、被追問就破功。必須事前備好 6–8 個故事庫並演練過。

### 五、用 phantom-tutor 哪個模式練 + 怎麼練

這一維度的核心不是「知識」,是「在壓力下結構化敘事 + 被追問時守得住判斷」,所以**主力是 interview-mock,system-design 輔助,knowledge-SRS 養彈藥,coding-judge 邊路支援**。

**1) interview-mock(主力,LLM 面試官讀你的弱點)**
- 怎麼練:先建一個「故事庫」(6–8 個 STAR(R) 骨架:1 hard bug、1 owned project、1 conflict、2 tradeoff、1 failure、1 proud-impact),把 phantom-mesh 的真實素材(PHANTOM_HOME bug、L1 governed run、local-first thesis、provider abstraction、AGPL 商業模式)各掛到對應原型上。
- 讓 interview-mock 扮 hiring manager,**逐題追問三層**:第一層問故事,第二層問「why not X / what would you change / what was the cost」,第三層故意施壓(「我覺得這個決定是錯的」)看你會不會崩或硬拗。
- 弱點偵測:讓 LLM 面試官在每輪結束輸出「你哪裡只講步驟沒講決策」「哪裡沒量化」「哪裡防衛過度」「哪個故事你是配角卻講得像主角」。把這些標記回灌成下一輪的訓練重點。
- 專練「捍衛架構」單元:把第三節的 design-defense 模板貼進去,要求面試官對 local-first / owned-memory / governed / provider-abstraction / AGPL 五個決策各打一輪 why-not,並用 rubric(有沒有重述約束、有沒有承認對方優點、有沒有給判準、有沒有承認代價、有沒有劃出反悔邊界)逐項評分。

**2) system-design(輔助,LLM 依 rubric 評分)**
- 捍衛架構題本質是「逆向的系統設計題」。用 system-design 模式正向練一遍「設計一個 safe autonomous agent / 一個 local-first 私人 AI memory 系統」,把 governor、flight-recorder、provider abstraction、eval、成本各個面向都被 rubric 打分。
- 正向設計練熟後,你在行為輪被反問「why this not that」時就有完整的 alternatives 地圖可調用——因為你真的在 design 模式裡比較過 trade-off,而不是臨場編。

**3) knowledge-SRS(養彈藥,間隔重複)**
- 把可被追問的「事實彈藥」做成卡片:你專案的關鍵數字(before/after 指標)、你做過的每個 trade-off 的 decision criteria、每個架構決策的「對方優點 + 我的判準 + 我承認的代價 + 反悔邊界」四件組。
- 也做「反問題庫」卡片:面試官最可能的 30 個追問(why not cloud / why not fine-tune / how did you eval / what was the cost / what would you change)——用 SRS 確保臨場每題都有現成、不卡頓的兩句話答案。

**4) coding-judge(邊路,跑你的程式對 unit test)**
- 行為輪本身不寫 code,但你的「hard bug」故事若涉及具體技術,coding-judge 可以幫你把那段 bug 用最小重現寫出來並用測試固化——這麼做有兩個好處:(a) 你講故事時細節是真的、追問打不倒;(b) 你能順口說出「我加了一個 regression test 防止它再發生」,而那個 test 是真的存在、跑得過的,展示 verification 紀律。
- 建議把每個 debugging 故事都配一個「最小重現 + regression test」的小 repo 片段,coding-judge 確認綠燈,讓你的敘事有可驗證的底氣。

**循環建議**:knowledge-SRS 養好彈藥與反問庫 → system-design 把架構 trade-off 比較透 → interview-mock 做三層追問實戰並抓弱點 → 弱點回灌 SRS → 每週一次完整 mock 録音自評(計時、配比、有沒有量化、有沒有防衛過度)。重點 KPI:每個故事能在 8 分鐘內講完且 Action 佔一半、每個架構決策都能扛三層追問不崩、每個失敗故事都改的是機制不是態度。

---

## F. 實作 / 流程 / 面試 meta

這個維度是面試裡最被低估、卻最容易拉開差距的部分。技術深度題大家都在準備,但「拿到 take-home 怎麼 scope」「model 不 learn 怎麼系統化 debug」「讀 paper 怎麼被問到痛點」「production 上線後怎麼管 drift」「面試流程每一關到底在 filter 什麼」——這些才是把一個「會寫 model 的人」和「能被信任獨立交付的 AI engineer」區分開的地方。下面把每個情境拆到可以直接練的程度。

---

### A. Take-home project(帶回家專案)

#### 常見情境/題型
- **開放型資料集**:給你一份 CSV(churn / fraud / 房價 / 評論情感),「建一個 model 預測 X,寫個 README,我們會看你的 code」。沒有明確 metric 門檻。
- **半開放 NLP/LLM 題**:「給這 500 筆客服對話,做一個 intent classifier」或「用 LLM 做一個 RAG 問答,我們給你一份 PDF」。
- **接近真實工程題**:「這裡有一個跑很慢/準確率很差的 baseline notebook,改進它並說明你做了什麼」。
- **時間盒**:常見「我們預期你花 4-6 小時」,但你交出來的東西會被當成「你最好的工程品味」來看,grader 不知道你真的花了 4 小時還是 14 小時。

#### 在考什麼
take-home 幾乎不在考「你能不能把 accuracy 衝到 0.92」。它在考五件事,按權重排:
1. **Problem framing / scoping**:你有沒有先定義成功長什麼樣(metric、baseline、約束),還是直接 `model.fit()`。
2. **工程衛生**:能不能 reproduce(`requirements.txt`/`environment.yml`、固定 seed、一鍵跑)、code 乾不乾淨、有沒有 leakage。
3. **判斷力與取捨**:你知不知道什麼該做、什麼故意不做,並寫出來(scope cut 是加分不是扣分)。
4. **溝通**:README 能不能讓一個沒看過的人 5 分鐘內理解「你做了什麼、為什麼、結果如何、限制是什麼」。
5. **誠實**:有沒有自己標出弱點與「如果有更多時間我會…」。

#### 解法/答題策略(可直接照抄的交付結構)
把 take-home 當成一個**迷你 production 專案 + 一份決策日誌**,而不是一個 Kaggle notebook。

**第一個小時先寫一份 `APPROACH.md`(在寫任何 model 前)**,內容:
- 問題重述 + 我假設的成功定義(例:「這是 imbalanced binary classification,正類 4%,我用 PR-AUC 當主 metric,因為 accuracy 會被 majority class 騙」)。
- baseline 計畫:先跑一個 dumb baseline(majority class / logistic regression),所有複雜 model 都要打贏它才有意義。
- 我故意不做的事 + 原因(明確 scope cut)。

**交付物的目錄結構(強訊號)**:
```
README.md            # 5分鐘看懂:問題/做法/結果表/限制/如何跑
APPROACH.md          # 決策日誌:為什麼這樣切
requirements.txt     # 或 pyproject + 鎖版本
src/                 # 可 import 的模組,不是一坨 notebook
  data.py  features.py  model.py  evaluate.py
notebooks/           # 探索用,但結論搬進 src
tests/               # 至少 2-3 個 unit test:feature 函式、no-leakage 檢查
Makefile / run.sh    # `make all` 一鍵 reproduce
```

**README 必含的「結果表」**(這是 grader 第一個看的):
| Model | PR-AUC | 訓練時間 | 備註 |
|---|---|---|---|
| Majority baseline | 0.04 | — | 下限 |
| Logistic Reg | 0.31 | 2s | 可解釋 baseline |
| LightGBM | 0.52 | 40s | 選用;特徵重要度見圖 |

**一定要寫的三段話**:
- *「我如何驗證沒有 data leakage」*:時間切分 / group split / 確認沒有用到 future 或 target-derived feature。這是資深訊號。
- *「限制與已知弱點」*:例如「我用單一 random split,正式應該 cross-validate / 用 time-based split」。
- *「給我更多時間我會做」*:error analysis、calibration、把 inference 包成 service、加 monitoring。

**worked example(churn take-home 的強答骨架)**:
> 「我先確認 label 定義(30 天內未活躍),發現有 8% 缺失值集中在新用戶 → 我把『新用戶』獨立成一個 feature 而非 impute,因為缺失本身有訊號。主 metric 選 PR-AUC + 在固定 threshold 下的 recall@precision=0.5,因為商業上漏掉 churner 比誤報貴。baseline LR 給 0.31,LightGBM 到 0.52。我刻意沒做 hyperparameter 大搜,因為邊際效益低於先處理 leakage 與 feature 品質;這在 README 有寫。」

#### 常見坑/紅旗
- **一個 5000 行的 notebook、變數叫 `df2`、`df_final`、`df_final2`** → 立刻被歸類「不能進 codebase」。
- **沒有 baseline,直接上 XGBoost/transformer**,無法判斷模型到底有沒有用。
- **Data leakage**:在 split 前 `fit` scaler/encoder、用 target 編碼沒做 fold、用了上線時拿不到的 feature。grader 常常故意埋這個。
- **過度工程**:為一個 1000 筆的題目寫 Airflow DAG + Docker compose + k8s。scope 判斷力是負分。
- **不可重現**:沒鎖版本、用了本機絕對路徑、seed 沒固定、跑兩次結果不同。
- **README 只有 `pip install -r requirements.txt && python main.py`**,沒有結果、沒有取捨、沒有限制。
- **隱藏弱點**:假裝沒有問題。grader 反而想看你**主動**指出自己的弱點——這是 senior 的標誌。

#### 用 phantom-tutor 哪個模式練 + 怎麼練
- **coding-judge**:把「no-leakage 檢查」「feature 函式」「metric 計算(PR-AUC、recall@precision)」做成可被 unit test 跑的小函式題。judge 餵你一個埋了 leakage 的 pipeline,要你寫 test 抓出來。練的是「能不能把 ML 邏輯拆成可測單元」。
- **system-design(LLM 對 rubric 打分)**:把整份交付物的 `APPROACH.md` + 目錄結構貼進去,rubric 涵蓋 scoping / baseline / leakage / reproducibility / 溝通 / scope-cut 是否有寫。LLM 模擬 grader 給逐項分數 + 「哪一項會讓你被刷」。
- **interview-mock**:模擬 take-home review 的 follow-up 口試——LLM 讀你的 README,專挑「你這裡為什麼不 cross-validate」「這個 feature 上線拿得到嗎」「baseline 呢」這類追問,訓練你當場辯護設計決策。
- **knowledge-SRS**:把「leakage 的 N 種型態」「imbalanced 該用哪個 metric」「reproducibility checklist」做成卡片反覆背成肌肉記憶。

---

### B. Debug「model 不 learn / learn 不好」

#### 常見情境/題型
- 給你一個 training loop,loss 不降 / loss 變 NaN / train loss 降但 val 不動 / accuracy 卡在隨機水準。
- 「這個 model 過擬合很嚴重,怎麼辦?」(train 0.99 / val 0.6)。
- 白板或 live:「你訓練一個網路,loss 一直是 2.3 都不動,你會怎麼一步步查?」——這是**最高頻的 ML debugging 口試題**。
- LLM/微調版:「fine-tune 後 model 一直輸出垃圾 / 重複 / 拒答」。

#### 在考什麼
不是考你知道哪個答案,是考你有沒有**系統化、由便宜到貴、由可隔離到全局的 debugging 思路**,以及你會不會用「假設 → 最小實驗 → 觀測」這個 loop,而不是亂調 hyperparameter。面試官最怕聽到「我就 lr 調小試試、加 dropout 試試」這種亂槍打鳥。

#### 解法/答題策略(一個可背誦的決策樹)
口頭回答時,用「先確認問題在哪一層」的順序講,展現你會 **bisect**:

**Step 0 — 先分類症狀**:loss 是 (a) 完全不動 (b) NaN/爆炸 (c) train 降 val 不降(overfit)(d) train 也不太降(underfit/欠擬合)。不同症狀走不同支線。

**支線 (a/d) train loss 不降 → 先做「過擬合一個 batch」這個黃金測試**:
> 「我會先拿單一個 mini-batch,關掉 regularization,讓 model 去 memorize 它。如果連一個 batch 都壓不到接近 0 loss,問題在 **model/optimization/code**,不是 data 量。」
這一句話幾乎所有強面試官都想聽到。接著查:
- **資料管線**:label 有沒有對齊?normalization 做了沒?輸入是不是全 0 / 全相同?把一個 batch 印出來眼睛看。
- **loss / 輸出對不對**:分類用了對的 loss 嗎(CrossEntropy 吃 logits 還是 probabilities?有沒有重複 softmax)?初始 loss 是否約等於 `ln(num_classes)`(對的話表示初始化正常)?
- **learning rate**:做一次 LR range test。太小→不動,太大→NaN/震盪。
- **gradient**:print grad norm。全 0 → 斷在某層(detach?no_grad?activation 死掉,ReLU dead?)。爆炸 → 加 grad clipping。
- **forward 正確性**:requires_grad、optimizer 有沒有 `.step()`、有沒有忘了 `zero_grad`。

**支線 (b) NaN**:lr 太大 / log(0) / 除 0 / mixed precision 溢位 / 資料有 NaN。查順序:先看資料,再降 lr,再加 clipping,再關 AMP。

**支線 (c) overfit(train 好 val 爛)**:這是「容量夠但泛化差」。手段排序:more data / augmentation → regularization(weight decay, dropout)→ early stopping → 降容量。先確認**不是 leakage 造成的假高 train**,也確認 val 集分布跟 train 一致。

**LLM fine-tune 版的特有支線**:
- 輸出重複/退化 → learning rate 太高燒掉了 base、或 prompt template 跟訓練格式不一致、或缺 EOS。
- 拒答/變笨 → catastrophic forgetting / 資料品質 / over-fit 到小資料 → 用 LoRA + 低 lr + 混入一般資料。

**強答的 meta 句**:「我 debug 的原則是**一次只改一個變數、每個假設配一個最便宜能證偽的實驗**,並且先隔離是 data、code、還是 optimization 三層哪一層出問題。」

#### 常見坑/紅旗
- 一上來就調 lr/加層數,沒有先**看資料**、沒有先**過擬合一個 batch**。
- 不會 print/inspect:不看 loss 曲線、不看 grad norm、不看一個 batch 的實際內容。
- 把「val 不降」直接當成「需要更大 model」(常常其實是 leakage 或 val 分布問題)。
- 不知道初始 loss 該是多少(失去一個免費的 sanity check)。
- 改一堆東西同時改,出問題了講不清是哪個。

#### 用 phantom-tutor 哪個模式練
- **interview-mock**:這題本質是口試。讓 LLM 當面試官丟症狀(「loss 卡在 2.3」),你講 debugging 步驟,它扮演「我試了你說的,grad norm 是 0」逐步逼你往下查,並標出你跳過了哪個便宜檢查(weak-spot:你從沒提『overfit 一個 batch』)。
- **coding-judge**:給一段**故意有 bug 的 training loop**(忘了 `zero_grad`、loss 用錯、label 偏移一格),要你找出並修好,judge 用「修好後 loss 能在 N 步內降到閾值」當測試。
- **knowledge-SRS**:把決策樹做成卡片——「症狀 NaN → 查哪四件事、順序」「初始 CE loss ≈ ?」「dead ReLU 的徵兆」反覆抽考。

---

### C. 讀 paper / 討論 paper

#### 常見情境/題型
- 「介紹一篇你最近讀、覺得有意思的 paper」(self-選)。
- 「你怎麼看 Transformer / RLHF / LoRA / RAG?它解決什麼、代價是什麼?」
- 給你一頁 paper 摘要或一張架構圖,當場讓你 critique:「這個方法的 limitation 是什麼?baseline 公平嗎?」
- research-leaning 職缺:「如果讓你改進這篇,你會怎麼做下一步實驗?」

#### 在考什麼
- 你能不能把一篇 paper **壓縮成 problem → key idea → why it works → cost/limitation → 適用場景**,而不是背 abstract。
- 你有沒有 **critical reading**:會質疑 baseline 公不公平、ablation 有沒有支持 claim、評測有沒有 cherry-pick。
- 你能不能把 paper 連到**你會不會在 production 用它、什麼條件下用**——工程落地視角。

#### 解法/答題策略(一個萬用敘述框架)
回答任何 paper 都用這 5 段,30-60 秒講完核心,再展開:
1. **它要解的痛點**(一句:之前的方法在 X 上不行/太貴)。
2. **核心 idea**(一句機制 + 一個直覺類比)。
3. **為什麼會 work**(關鍵 insight,不是流程)。
4. **代價/限制**(compute、資料、假設、什麼時候會壞)——**這段最展現深度**。
5. **我會在什麼場景用它 / 不用它**。

**worked example(LoRA)**:
> 「痛點:full fine-tune 一個大 model 要更新所有權重,顯存和儲存都貴,每個任務一份權重不可行。核心 idea:凍結原權重,只在每層注入一對低秩矩陣 A·B,假設『適配某任務所需的權重變化是低秩的』。為什麼 work:下游適配的有效自由度遠小於參數量,低秩就夠表達。代價:rank 太低表達不足、對某些需要大幅改變表徵的任務不夠;但好處是每任務只存幾 MB、可熱插拔。我會在『一個 base model 服務多任務、要省顯存』時用 LoRA;若要榨最後一點性能或任務跟 pretrain 差很遠,才考慮 full fine-tune 或 QLoRA。」

**被問 critique 時的句型**:「我會先看它的 baseline 是不是 under-tuned(常見不公平來源),再看 ablation 有沒有把『真正貢獻的部件』隔離出來,最後看評測集會不會剛好對它有利。」

**如果沒讀過那篇**:誠實說「沒讀過,但聽起來像是在解 X 類問題,我猜機制大概是 Y,代價會是 Z」——展現你能**從第一性原理推**,比硬掰好太多。

#### 常見坑/紅旗
- 背 abstract、講流程("它有 encoder 有 attention"),講不出**為什麼 work** 和**代價**。
- 只會吹優點,問 limitation 就空白 → 顯示沒有批判性。
- 對「最近有趣的 paper」答不出來 → 顯示沒在跟領域。
- 硬掰沒讀過的細節被抓包(誠實 + 推理永遠贏)。

#### 用 phantom-tutor 哪個模式練
- **knowledge-SRS**:把經典 paper(Transformer/BERT/RLHF/LoRA/RAG/Chinchilla scaling/FlashAttention…)各做成一張「5 段壓縮卡」,正面是名稱,背面是 problem/idea/why/cost/when。反覆抽到能 60 秒口述。
- **interview-mock**:LLM 當 reviewer,要你介紹一篇 paper,然後專打第 4 段——「它的 baseline 公平嗎」「這個 claim 哪個 ablation 支持」「什麼情況它會壞」,標出你 critique 能力的 weak-spot。
- **system-design**:給一個 limitation,要你設計「下一步實驗 / 改進方案」,LLM 用「假設是否被隔離驗證、實驗是否能證偽」當 rubric。

---

### D. MLOps / production 關切(drift、monitoring、CI for ML、reproducibility)

#### 常見情境/題型
- 「你的 model 上線後 accuracy 掉了,怎麼查?」
- 「怎麼監控一個 production ML 系統?要看哪些指標?」
- 「怎麼做 ML 的 CI/CD?跟一般 software CI 差在哪?」
- 「怎麼確保一個訓練實驗可重現?」
- 「怎麼安全地 rollout 新 model?」(shadow / canary / A-B)。

#### 在考什麼
你有沒有**「model 不是交付終點,是維運起點」**的心智模型。面試官在分辨「只會 train」的人 vs 「能為線上負責」的人。重點是你知道 ML 系統會以 software 不會的方式默默壞掉(資料變了,但 code 沒變,沒有 exception,只是慢慢爛)。

#### 解法/答題策略

**「上線後 accuracy 掉了」的查法(講出分層)**:
1. 是真的掉還是**監控/label 延遲**造成的假象?
2. **Data drift / training-serving skew**:input 分布變了?上下游 feature pipeline 改了?(最常見:offline 用某版特徵,線上是另一版)。
3. **Concept drift**:X→y 的關係本身變了(疫情、政策、季節)。
4. 上游壞了:某個 feature 變全 null、單位變了、新類別出現。
5. 確認問題後再決定 retrain / rollback / 修 pipeline。

**Monitoring 要分三層講(背起來)**:
- **Operational**:latency、throughput、error rate、QPS。(像一般服務)
- **Data quality**:schema、null rate、值域、新類別、feature 分布(用 PSI / KL / KS 偵測 drift)。
- **Model quality**:prediction 分布、confidence 分布、(有 label 時)滾動 accuracy/AUC;label 常延遲,所以**先靠 proxy(drift、prediction 分布)報警**。

**CI for ML 跟一般 CI 的差異(高頻題)**:
- 一般 CI 測 code;ML 還要測 **data + model**。
- CI 階段:lint/unit test(feature 函式、可重現性) → data validation(schema、分布) → train smoke(小資料能跑通) → **model 驗收 gate**(新 model 在 holdout 上不能比 production 差超過 ε,且 fairness/slice metric 不退) → package。
- 加 **behavioral test**(CheckList 式):對已知關係寫斷言(「漲價→churn 機率不該下降」)。

**Reproducibility checklist(被問必背)**:固定 seed、鎖套件版本、版本化**資料**(DVC / 存 snapshot+hash)、版本化 model + 訓練 config、記錄 git commit、用 experiment tracker(MLflow/W&B)存 params/metrics/artifact。一句話:「code、data、config、環境四者都要可釘住到某次 run。」

**安全 rollout**:shadow(線上跑但不採用,比對)→ canary(小流量)→ A/B(看商業 metric)→ 全量;永遠保留一鍵 **rollback**。

#### 常見坑/紅旗
- 把 ML monitoring 講成只有 latency/uptime,漏掉 **data/model quality**。
- 不知道 **training-serving skew**(離線線上特徵不一致)這個 production #1 殺手。
- 認為「重新訓練」就能解 drift,沒先 diagnose 是 data 還是 concept drift。
- reproducibility 只說「固定 seed」,漏掉**資料版本化**(最常被忽略的一塊)。
- 把 model artifact 直接覆蓋上線,沒 versioning、沒 rollback、沒 shadow。

#### 用 phantom-tutor 哪個模式練
- **system-design**:出「設計一個 production ML 系統的 monitoring + retraining + safe rollout」,LLM 用 rubric 打分:有沒有覆蓋三層 monitoring、有沒有區分 data/concept drift、有沒有 rollback、有沒有處理 label 延遲。這是這個維度的主力練法。
- **knowledge-SRS**:三層 monitoring、drift 指標(PSI/KL/KS)、reproducibility checklist、CI-for-ML 階段——全做成卡片。
- **interview-mock**:LLM 丟「accuracy 掉了」情境,逐步追問逼你分層 diagnose,抓你是否跳到 retrain。
- **coding-judge**:寫一個 drift 偵測函式(算 PSI / null-rate 報警)或 data-validation 斷言,judge 用準備好的「正常 vs drift」資料測你閾值對不對。

---

### E. 面試流程本身(rounds、各關 filter 什麼、紅旗、要問的問題、offer)

#### 常見情境/各關在 filter 什麼
1. **Recruiter / HR screen(20-30 min)**:filter 動機、薪資期待是否對得上、基本 logistics(可否到職、visa)。不考技術。**坑**:在這關亂報薪資錨點、講不清楚為何想離職/想加入。
2. **Technical / hiring-manager screen**:履歷深挖 + 一兩個概念題,filter「履歷是否真實、能不能講清楚自己做過什麼」。**坑**:履歷寫「improved accuracy by 20%」但講不出 baseline、metric、你個人的貢獻。
3. **Coding round**:多半 DS&A(LeetCode 中等)或「實作一個 ML 小函式(KNN/k-means/從零寫 logistic regression/實作 attention)」。filter 基本 coding 與把數學翻成 code 的能力。
4. **ML depth / ML breadth**:bias-variance、regularization、為什麼用這個 loss、evaluation、處理 imbalance、過擬合…… filter 基礎是否扎實、有沒有 hand-wave。
5. **ML system design**:「設計推薦/搜尋/詐欺偵測/feed ranking」。filter 端到端思維(資料→特徵→model→serving→monitoring→loop)。**這關和 D 高度重疊。**
6. **Behavioral**:衝突、失敗、跨組合作、ownership。filter 協作風險、是否會把問題推給別人、ego。
7. **Team match / bar raiser / hiring committee**:文化、長期潛力、跨關一致性。

#### 解法/答題策略
- **Behavioral 用 STAR**(Situation-Task-Action-Result),每個故事準備:**衝突一個、失敗一個、領導/ownership 一個、技術取捨一個**。Result 一定要量化 + 一句「我學到什麼」。失敗題的重點是**你怎麼處理 + 學到什麼**,不是有沒有失敗。
- **履歷深挖**對每個 bullet 都要能回答:problem、你的角色(用「我」不是「我們」)、為什麼這樣做、結果、若重來會怎樣。
- **薪資**:recruiter 問期待時,先反問 range,或給一個有 research 的區間(用 levels.fyi 等),不要先自爆一個低數字。
- **跨關一致性**:不同關會交叉比對你講的同一個專案,別在 A 關說「我主導」、B 關說「我只是幫忙」。

#### 要 ASK interviewer 的好問題(每關都要準備 2-3 個,問題本身就是訊號)
- 給工程主管:「團隊現在最大的技術瓶頸是什麼?」「一個 model 從想法到上線的週期多長、卡點在哪?」「on-call / 維運怎麼分?」
- 給未來同事:「最近一次有人交付了什麼讓你印象深刻?」「team 怎麼做 code/design review?」
- 給 manager:「這個 role 6 個月後成功長什麼樣?」「team 怎麼定義 senior?」
- **探團隊健康度的問題**(也是幫你篩雇主):「ML 專案大概多少比例真的上線?」「有沒有 model monitoring / retraining 的流程,還是還在建?」——對方答不出來就是紅旗。

#### 你該警覺的「雇主紅旗」
- 描述不清這個 role 要做什麼 / 半年內換了好幾個 JD。
- 「我們還沒有任何 ML 上線但想找你來建一切」+ 沒有資料基礎建設 → 你可能會變成獨自蓋地基。
- 面試官遲到/不專業/問歧視性問題。
- 流程拖很久、每關都加新關卡、不給回饋。

#### 你自己會踩的紅旗(候選人側)
- 講「我們」不講「我」,聽不出你個人貢獻。
- 抱怨前公司/前同事。
- 對自己履歷上的東西答不出細節(寫了 transformer 但講不出 attention 是什麼)。
- 沒問任何問題(訊號:沒興趣 / 沒準備)。
- 給 take-home 後玩消失或交一坨 notebook。

#### Post-interview / offer 基本功
- 24 小時內寄簡短 thank-you / follow-up(尤其有想補充的點)。
- **拿到 offer 一定可以談**:base、bonus、equity、sign-on、start date、level 都是變數;有競品 offer 是最強籌碼但別虛張。
- 評估時看 **level / scope / 團隊 / 學習曲線**,不要只看數字。
- 被 reject:可禮貌要 feedback,把這次的弱點變成下一輪的卡片。

#### 用 phantom-tutor 哪個模式練
- **interview-mock**:這是整個 E 段的主場。設定不同關卡 persona——recruiter screen / behavioral(STAR,LLM 追問「具體你做了什麼、結果數字、學到什麼」)/ 履歷深挖(LLM 拿你貼的履歷 bullet 逐條逼問)/ team-match(練你要問的問題品質)。讓 LLM 在結尾輸出 weak-spot 報告:「你 behavioral 都在講『我們』、失敗題沒有 learning、沒反問任何問題」。
- **knowledge-SRS**:把「每關在 filter 什麼」「STAR 結構」「要問的好問題清單」「offer 可談項目」做成卡片,面試前一天快速過。
- **coding-judge**:對應 coding round——刷 LeetCode 中等 + 從零實作 ML 基本元件(logistic regression / k-means / attention forward),judge 跑 unit test 驗正確性與邊界。
- **system-design**:對應 ML system design round,直接用 D 段的 rubric 練端到端設計。

---

### 跨維度的一句總結(meta)
這個維度的共同主軸是:**「展現判斷力與工程成熟度,而非單點技術炫技」**。Take-home 看你 scope 與誠實,debug 看你系統化,paper 看你批判,MLOps 看你對「上線後」負責,流程看你一致與協作。phantom-tutor 的練法分工很清楚——**會被「跑起來驗證對錯」的(coding 元件、debug 修 bug、drift 函式)用 coding-judge;會被「對著 rubric 評端到端設計」的(MLOps、system design、take-home 交付結構)用 system-design;需要「壓縮成可背框架」的(paper 5 段、monitoring 三層、各關 filter)用 knowledge-SRS;需要「被人盯著問、暴露盲點」的(ML debug 口試、behavioral、paper critique、履歷深挖)用 interview-mock**。每一關都先用 mock 暴露 weak-spot,再用 SRS 把缺口補成肌肉記憶,形成閉環。

---


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
