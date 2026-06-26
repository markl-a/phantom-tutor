# Synthetic Career Loop Contract

`tutor demo-loop` is the P2 public alpha artifact loop for `phantom-tutor`.
It proves the career-learning flow without real resumes, real applications,
private interview notes, job-board scraping, cloud LLM calls, or hidden
real-time assistance.

## Command

```powershell
python -m phantom_tutor.cli demo-loop --out <bundle> --now 2026-06-26
```

The command prints `<bundle>\manifest.json`.

## Bundle Layout

```text
<bundle>/
  manifest.json
  artifacts/
    source-jobs.json
    source-operator-skills.json
    jobs.json
    operator_skills.json
    gap-report.json
    review-result.json
    weak_spots.json
    attempts.jsonl
    summary.md
```

## Manifest Schema

`manifest.json` is stable JSON with sorted keys and schema version `1`.

Required top-level fields:

- `schema_version`: currently `1`.
- `mode`: `synthetic_career_learning_loop`.
- `now`: the deterministic review date.
- `data_policy`: `synthetic_only`.
- `private_data_included`: always `false`.
- `external_network`: always `false`.
- `llm_provider`: `stub_or_disabled`.
- `anti_cheating_boundary`: `practice_only_no_live_interview_assistance`.
- `artifacts`: bundle-relative paths for `source_jobs`, `source_profile`,
  `jobs`, `profile`, `gap_report`, `review_result`, `weak_spots`, `attempts`,
  and `summary`.

## Artifact Contract

- `jobs.json`: ingested synthetic job postings after duplicate/agency filtering.
- `operator_skills.json`: synthetic skill profile used for coverage/gap scoring.
- `source-jobs.json`: source synthetic postings before ingest filtering.
- `source-operator-skills.json`: source synthetic profile before it is copied
  into the isolated tutor home.
- `gap-report.json`: seeded job-gap weak spots and due review list.
- `review-result.json`: deterministic quiz/practice result for one review.
- `weak_spots.json`: local weak-spot store after gap seeding and review update.
- `attempts.jsonl`: append-only review attempt history.
- `summary.md`: human-readable summary of the synthetic loop.

## Safety Contract

The loop is practice-side only. It must not:

- include real resumes, application history, private interview notes, or personal
  career records;
- scrape job boards, submit applications, or contact employers;
- call a cloud LLM or require API keys;
- provide hidden assistance during an interview.

All public examples must remain synthetic and local. Optional online providers
or external actions, if added later, require an explicit governed approval path
and must stay out of this default demo loop.
