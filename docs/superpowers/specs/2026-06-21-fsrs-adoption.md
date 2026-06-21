# R1: adopt FSRS (py-fsrs) — design spec

> 日期:2026-06-21 · 分支 `feat/fsrs`。公開、零 PII。
> roadmap R1。對應 `docs/phantom-tutor.md` 階段一「FSRS 換手刻 SM-2」。

## 目標

把 `srs.py` 的手刻 SM-2-lite 換成 **FSRS**(`fsrs` PyPI 套件,import `fsrs`,MIT,純 Python)。FSRS = 有學術根據的 SM-2 後繼(stability/difficulty/retrievability),磨利護城河的「越用越懂你」排程。

## 與既有模型的落差(為何不是 byte-compatible)

- FSRS 用 **datetime(UTC)**;本專案全用 **date 字串**(`now_iso`、`is_due`)。
- 評分是 **Rating(Again/Hard/Good/Easy = 1–4)**;本專案是 **score 0–1**。
- FSRS 需 **per-card 狀態**(stability/difficulty/state/last_review/step);現 record 只有 interval。

→ 採用 FSRS 必然(a)在 record 存一個 FSRS card dict、(b)改變確切排程間隔。這是採用它的代價與好處。**決策已與 operator 確認**:採用 py-fsrs;day-level(`learning_steps=()`)。

## 設計

### 依賴
- `pyproject.toml` 加 `dependencies = ["fsrs>=6.3.1,<7"]`(pin major)。CI 既有 `pip install -e .` 自動帶入,無需改 CI。
- 純 Python、零網路 → hermetic 不破。**決定性**靠:`enable_fuzzing=False` + 每次 review 顯式傳 `review_datetime`(由 `now_iso`)。

### `srs.py`(重寫排程核心,保留 `is_due`/`PASS_THRESHOLD`)
- 模組級 `_scheduler = Scheduler(learning_steps=(), relearning_steps=(), enable_fuzzing=False)`(day-level、決定性)。
- `score_to_rating(score) -> Rating`:`<0.6 Again` / `<0.75 Hard` / `<0.9 Good` / `≥0.9 Easy`。
- `review(card: dict | None, score: float, now_iso: str) -> tuple[dict, str]`:`Card.from_dict(card)` 或新 `Card()` → `review_card(c, score_to_rating(score), review_datetime=midnight_utc(now_iso))` → 回 `(c.to_dict(), c.due.date().isoformat())`。
- `is_due(due_iso, now_iso)`:**不變**(date 比較,保住 `tutor today`/全鏈)。
- `PASS_THRESHOLD = 0.6`:**保留**(memory 的 streak 仍用它)。
- 移除 `next_interval_days` / `EASE` / `FIRST_INTERVAL`(SM-2 殘留)。

### `memory.py`(record_attempt 接縫)
- 取代「`next_interval_days` + `date+timedelta`」三行為:
  ```python
  card_dict, due_iso = srs.review(rec.get("fsrs"), float(score), now_iso)
  rec["fsrs"] = card_dict
  rec["due"] = due_iso
  rec["interval"] = (date.fromisoformat(due_iso) - date.fromisoformat(now_iso)).days
  ```
- 其餘不變:mastery EMA、streak(`score >= srs.PASS_THRESHOLD`)、attempts、`_append_attempt`。
- `import` 移除不再用的 `timedelta`(`date` 仍用)。
- **舊 record 無 `fsrs` key**:`srs.review(None, ...)` 自動新建 card,平滑遷移(保留既有 topic/mastery/attempts)。
- `seed_weak_spot`(gap 播種):**不變**——它直接設 `due=now`、`mastery=coverage`,不走 SRS,FSRS 只在真實 graded attempt 時介入。

## 行為變化(精算,learning_steps=()、enable_fuzzing=False)

| 情境 | SM-2-lite(舊) | FSRS(新) |
|---|---|---|
| 首次 fail(score<0.6) | +1 天 | +1 天 |
| 首次 pass(Good) | +3 天 | +2 天 |
| 首次 perfect(Easy) | +3 天 | +8 天 |
| 重複 pass | ×2 成長 | stability 成長(更長) |

既有 memory/cli e2e 測試的 due 斷言皆為**寬鬆不等式**,精算確認仍通過(transformer:0.4→06-13、1.0→06-16;due_topics:a 06-11、b 06-18)。**唯一需改寫**:`test_srs.py`(直接測 `next_interval_days`)。

## 測試(TDD,hermetic)

- `tests/test_srs.py`(改寫):
  - `score_to_rating` 四段邊界(0.5→Again, 0.6/0.7→Hard, 0.8→Good, 0.95→Easy)
  - `review(None, 1.0, d)` → due 在未來、回傳 card dict 含 `stability`
  - `review(None, 0.2, "2026-06-10")` → due `2026-06-11`(fail +1)
  - 重複 pass:第二次間隔 > 第一次(stability 成長)
  - `is_due` 三例(不變)
- 既有測試全綠(memory/cli/mode e2e 不動)。
- `tests/test_memory.py` 新增一例:第二次 attempt 後 record 帶 `fsrs` card dict(roundtrip 可序列化)。

## 驗收

- `python -m pytest -q` 全綠(含改寫的 srs 測試);`python -m ruff check .` clean。
- `tutor quiz`/`today` 端到端仍正常(due 為 date 字串、weakest-first 不變)。
- record JSON 內出現 `fsrs` card dict;舊無-card record 下次 review 自動升級。
- (CI)ubuntu 上 `pip install -e .` 帶入 fsrs、測試綠。
