# Practice Scenario Bundle Contract

`phantom-tutor practice-scenario` turns a synthetic `demo-loop` bundle into a
P3 weak-spot-to-practice evidence package. It proves that the tutor can select a
job-gap weak spot, run a deterministic practice result, record evidence, and
schedule the next review without private data, network access, live job-board
scraping, application submission, cloud LLM output, or covert live interview
assistance.

## Command

```powershell
python -m phantom_tutor.cli demo-loop --out <source-bundle> --now 2026-06-26
python -m phantom_tutor.cli practice-scenario --source <source-bundle> --out <scenario-bundle>
```

The command prints `<scenario-bundle>\manifest.json`.

## Accepted Source

`practice-scenario` accepts only a `demo-loop` bundle whose manifest declares:

- `mode=synthetic_career_learning_loop`
- `data_policy=synthetic_only`
- `private_data_included=false`
- `external_network=false`
- `llm_provider=stub_or_disabled`
- `anti_cheating_boundary=practice_only_no_live_interview_assistance`

Any artifact path declared by the source manifest must be bundle-relative and
must resolve inside the source bundle before it is read.

## Bundle Layout

```text
<scenario-bundle>/
  manifest.json
  practice-scenario.json
  practice-evidence.json
  summary.md
```

## Manifest Schema

`manifest.json` is stable JSON with sorted keys and schema version `1`.

Required fields:

- `mode`: `synthetic_practice_scenario_bundle`
- `source_mode`: `synthetic_career_learning_loop`
- `data_policy`: `synthetic_only`
- `private_data_included`: always `false`
- `external_network`: always `false`
- `llm_provider`: `stub_or_disabled`
- `anti_cheating_boundary`: `practice_only_no_live_interview_assistance`
- `artifacts`: bundle-relative paths to scenario JSON, evidence JSON, and summary

## Scenario JSON

`practice-scenario.json` contains:

- selected weak spot: key, topic, dimension, mastery, due date, and source
- deterministic practice result: mode, score, grading stub, command hint, and
  explicit `raw_answer_included=false` / `full_prompt_included=false`
- SRS update summary: attempts before/after, mastery before/after, next review,
  interval days, and `fsrs_state_included=false`
- readiness flags for weak-spot selection, practice completion, evidence
  recording, and next-review scheduling
- unsupported boundaries for covert live interview assistance, job-board
  scraping, application submission, raw private export, and cloud LLM default

## Evidence JSON

`practice-evidence.json` contains metadata-only evidence items:

- `weak_spot_selection`
- `practice_result`
- `srs_update`

It does not include raw answers, full interview or practice prompts, real
resumes, application history, private interview notes, employer contacts, live
job-board data, network output, or live LLM text.

## Determinism

Two practice scenario bundles from the same source bundle must produce
byte-stable `manifest.json`, `practice-scenario.json`, `practice-evidence.json`,
and `summary.md`.
