# Learning Plan Bundle Contract

`tutor learning-plan-demo` is the P2 artifact slice for learning-plan and
evidence-tracker ergonomics. It derives a short practice plan from a synthetic
`demo-loop` bundle and writes a reviewable evidence tracker without exposing
real career data.

## Command

```powershell
python -m phantom_tutor.cli demo-loop --out <source-bundle> --now 2026-06-26
python -m phantom_tutor.cli learning-plan-demo --source <source-bundle> --out <plan-bundle> --horizon-days 14
```

The command prints `<plan-bundle>\manifest.json`.

## Accepted Source

`learning-plan-demo` accepts only a `demo-loop` bundle whose manifest declares:

- `mode=synthetic_career_learning_loop`
- `data_policy=synthetic_only`
- `private_data_included=false`
- `external_network=false`
- `llm_provider=stub_or_disabled`
- `anti_cheating_boundary=practice_only_no_live_interview_assistance`

Bundles that declare private data, network access, live LLM output, or a weaker
anti-cheating boundary are rejected.

Any artifact path declared by the source manifest must be bundle-relative and
must resolve inside the source bundle before it is read.

## Bundle Layout

```text
<plan-bundle>/
  manifest.json
  learning-plan.json
  evidence-tracker.json
  summary.md
```

## Manifest Schema

`manifest.json` is stable JSON with sorted keys and schema version `1`.

Required top-level fields:

- `mode`: `synthetic_learning_plan_bundle`
- `source_mode`: `synthetic_career_learning_loop`
- `data_policy`: `synthetic_only`
- `private_data_included`: always `false`
- `external_network`: always `false`
- `llm_provider`: `stub_or_disabled`
- `anti_cheating_boundary`: `practice_only_no_live_interview_assistance`
- `artifacts`: bundle-relative paths for `learning_plan`, `evidence_tracker`,
  and `summary`

## Learning Plan

`learning-plan.json` contains:

- `start_date`, `end_date`, and `horizon_days`
- source counts for weak spots, due topics, and planned items
- ordered items derived from synthetic job-gap weak spots
- practice mode, command hint, scheduled date, and success criteria for each
  item

The plan uses synthetic job-gap topics only. It does not import resumes,
application history, private interview notes, live job-board data, or cloud LLM
feedback.

## Evidence Tracker

`evidence-tracker.json` contains metadata for the synthetic practice result and
attempt log. It records topic, dimension, score, mastery/attempt counters, and
date metadata, but not raw answers, full question text, resumes, employer
contacts, private interview notes, or application records.

## Determinism

Two runs against the same source bundle and horizon must produce byte-stable
`manifest.json`, `learning-plan.json`, `evidence-tracker.json`, and `summary.md`.
