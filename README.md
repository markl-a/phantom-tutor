# phantom-tutor

> 一條跑在 phantom-mesh core 上的「求職 copilot」——從「準備 → 作品 → 找到工作 → 副業」的連續流程,由 `weak_spots` owned-memory + SRS + wealth-score + governor 串起來(本地優先;加密 owned-memory / wealth-score / governor 為**規劃中的護城河方向**,目前 `weak_spots` 仍為本地 JSON,見路線圖)。AI 工程師面試準備是旗艦用例。

📄 完整文件(定位/快速上手/端到端流程/路線圖/開源生態/營利):見 [docs/phantom-tutor.md](docs/phantom-tutor.md)

個人化求職資料在 gitignored 的 `personalized/`(不在公開文件內);舊版見 `docs/_archive/`。

## Quickstart

```powershell
python -m pip install -e .
python -m pip install -e . --dry-run --no-deps
python -m pytest -q
python -m phantom_tutor.cli --help
```

Deterministic synthetic demo:

```powershell
$bundle = Join-Path $env:TEMP ("phantom-tutor-loop-" + [guid]::NewGuid().ToString("N"))
python -m phantom_tutor.cli demo-loop --out $bundle --now 2026-06-26
Get-Content (Join-Path $bundle "manifest.json")
```

The bundle uses synthetic jobs and a synthetic skill profile to run job gap
seeding, weak-spot review, and SRS update locally. The artifact contract is
documented in [docs/SYNTHETIC_CAREER_LOOP.md](docs/SYNTHETIC_CAREER_LOOP.md).

Deterministic learning-plan artifact bundle:

```powershell
$plan = Join-Path $env:TEMP ("phantom-tutor-plan-" + [guid]::NewGuid().ToString("N"))
python -m phantom_tutor.cli learning-plan-demo --source $bundle --out $plan --horizon-days 14
Get-Content (Join-Path $plan "learning-plan.json")
```

The plan bundle derives practice items and an evidence tracker from the
synthetic career loop. It does not include raw answers, full interview question
text, real resumes, application history, private interview notes, job-board
scraping, network output, or live LLM text. The contract is documented in
[docs/LEARNING_PLAN_BUNDLE.md](docs/LEARNING_PLAN_BUNDLE.md).

Deterministic weak-spot to practice scenario:

```powershell
$scenario = Join-Path $env:TEMP ("phantom-tutor-practice-" + [guid]::NewGuid().ToString("N"))
python -m phantom_tutor.cli practice-scenario --source $bundle --out $scenario
Get-Content (Join-Path $scenario "practice-scenario.json")
```

The scenario bundle proves the P3 loop: select a synthetic job-gap weak spot,
run a deterministic practice result, record metadata-only evidence, and schedule
the next review. The contract is documented in
[docs/PRACTICE_SCENARIO_BUNDLE.md](docs/PRACTICE_SCENARIO_BUNDLE.md).

## Anti-cheating policy

`phantom-tutor` is a prep-side learning tool. It is for practice before an
interview and review after an interview; it must not be used as a covert live
interview assistant or to generate hidden real-time answers during an interview.
Job scraping, application submission, and any external action are out of the
initial open-source scope unless a future governed, explicit approval path is
added.
