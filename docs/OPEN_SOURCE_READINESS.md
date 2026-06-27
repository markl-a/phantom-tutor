# Open Source Readiness

Project: `phantom-tutor`
Current phase: P4 installable public release candidate verified
Master plan: `../../PHANTOM-SATELLITES-OPEN-SOURCE-MASTER-PLAN.md`

## Shipped Features

- Local-first job-learning and interview-practice CLI.
- CLI entrypoint: `tutor = phantom_tutor.cli:main`.
- Help surface verified with `python -m phantom_tutor.cli --help`.
- Subcommands include `quiz`, `code`, `design`, `interview`, `today`, `weak-spots`, `stats`, `jobs`, `demo-loop`, `learning-plan-demo`, and `practice-scenario`.
- Root README now includes an explicit anti-cheating policy.
- Root README points to `docs/phantom-tutor.md`.
- Synthetic job gap -> weak spot -> due review -> quiz update loop verified with isolated `PHANTOM_TUTOR_HOME`.
- P2 synthetic career loop contract is documented in `docs/SYNTHETIC_CAREER_LOOP.md`.
- `demo-loop` writes a deterministic synthetic jobs/profile, gap report, review result, weak-spots store, attempts log, summary, and `manifest.json`.
- P2 learning-plan/evidence tracker contract is documented in `docs/LEARNING_PLAN_BUNDLE.md`.
- `learning-plan-demo` accepts only safe synthetic `demo-loop` bundles and writes deterministic `learning-plan.json`, `evidence-tracker.json`, `summary.md`, and `manifest.json`.
- P3 weak-spot-to-practice scenario contract is documented in `docs/PRACTICE_SCENARIO_BUNDLE.md`.
- `practice-scenario` accepts only safe synthetic `demo-loop` bundles and writes deterministic `practice-scenario.json`, `practice-evidence.json`, `summary.md`, and `manifest.json`.
- `learning-plan-demo` and `practice-scenario` validate manifest artifact paths as bundle-relative and contained inside the source bundle before reading.
- `pyproject.toml` defines installable package metadata for version `0.1.0a0`, Apache-2.0 license metadata, Python `>=3.11`, classifiers, project URLs, `fsrs` runtime dependency, dev extra, and packaged seed content.
- Test suite baseline after P2 synthetic career loop additions: `python -m pytest -q` passed with 74 tests.
- Test suite baseline after P2 learning-plan/evidence additions: `python -m pytest -q` passed with 78 tests.
- Test suite baseline after P3 weak-spot-to-practice additions and manifest-path hardening: `python -m pytest -q` passed with 83 tests.

## Planned Or Deferred Features

- Broader career learning OS: weak spot graph, portfolio evidence, richer job gap planning.
- Live job-board scraping, real application submission, and covert live interview assistance are out of initial release scope.

## Install And Test Commands

```powershell
python -m pip install -e .
python -m pytest -q
python -m phantom_tutor.cli --help
python -m phantom_tutor.cli jobs ingest --src <synthetic-jobs.json>
python -m phantom_tutor.cli --now 2026-06-26 jobs gap --n 5
python -m phantom_tutor.cli --now 2026-06-26 today
python -m phantom_tutor.cli --now 2026-06-26 quiz --id k-softmax --answer "no idea"
python -m phantom_tutor.cli demo-loop --out <temp>\bundle --now 2026-06-26
python -m phantom_tutor.cli learning-plan-demo --source <temp>\bundle --out <temp>\plan --horizon-days 14
python -m phantom_tutor.cli practice-scenario --source <temp>\bundle --out <temp>\practice-scenario
```

Observed P2 result on 2026-06-26:

```text
74 passed in 3.20s
```

Observed P2 learning-plan targeted result on 2026-06-26:

```text
3 passed in 0.08s
```

Observed P2 learning-plan full-suite result on 2026-06-26:

```text
78 passed in 4.04s
```

Observed P3 weak-spot-to-practice targeted result on 2026-06-26:

```text
3 passed in 0.09s
```

Observed P3 contract bundle result on 2026-06-26:

```text
11 passed in 0.20s
```

Observed P3 weak-spot-to-practice full-suite result on 2026-06-26:

```text
83 passed in 3.46s
```

## Fixture And Data Policy

- Public fixtures must be synthetic and must not include real resumes, real application history, or private interview notes.
- `personalized/` is gitignored and must remain out of public fixtures.
- LLM behavior in tests must remain stubbed or deterministic.
- Learning-plan/evidence artifacts must not include raw answers, full interview question text, resumes, application history, employer contacts, live job-board data, or live LLM output.
- Practice-scenario artifacts must not include raw answers, full prompts, resumes, application history, private interview notes, employer contacts, live job-board data, network output, or live LLM text.

## Safety And Privacy Risks

- Interview practice can be misused as covert live interview assistance; README/docs need an explicit anti-cheating policy.
- Job data and weak spots can reveal sensitive career information.
- Online LLM use must be optional and disabled by default for private data.

## Blockers To Next Phase

- None for the current P3 weak-spot-to-practice scenario proof slice. Next phase should harden weak-spot graph semantics or portfolio evidence without enabling live job-board scraping, application submission, or covert interview assistance.

## Evidence

- `pyproject.toml` declares package `phantom-tutor` and script `tutor`.
- `README.md` points to `docs/phantom-tutor.md`.
- `README.md` includes anti-cheating policy.
- `README.md` includes `demo-loop` as the deterministic synthetic career-learning artifact bundle.
- `README.md` includes `learning-plan-demo` as the deterministic learning-plan/evidence artifact bundle.
- `README.md` includes `practice-scenario` as the deterministic weak-spot-to-practice scenario bundle.
- `docs/SYNTHETIC_CAREER_LOOP.md` documents `manifest.json`, `synthetic_career_learning_loop`, `synthetic_only`, `private_data_included=false`, `external_network=false`, `stub_or_disabled`, and `practice_only_no_live_interview_assistance`.
- `docs/LEARNING_PLAN_BUNDLE.md` documents `manifest.json`, `learning-plan.json`, `evidence-tracker.json`, `synthetic_learning_plan_bundle`, `synthetic_only`, `private_data_included=false`, `external_network=false`, `stub_or_disabled`, and raw-answer/private-interview-note exclusions.
- `docs/PRACTICE_SCENARIO_BUNDLE.md` documents `manifest.json`, `practice-scenario.json`, `practice-evidence.json`, `synthetic_practice_scenario_bundle`, `synthetic_only`, `private_data_included=false`, `external_network=false`, `stub_or_disabled`, and anti-cheating/raw-answer exclusions.
- `python -m pytest tests/test_learning_plan_contract.py -q`: 3 passed.
- `python -m pytest tests/test_practice_scenario_contract.py -q`: 3 passed.
- `python -m pytest tests/test_open_source_contract.py tests/test_learning_plan_contract.py tests/test_practice_scenario_contract.py -q`: 11 passed.
- `python -m pytest tests/test_learning_plan_contract.py tests/test_open_source_contract.py tests/test_demo_loop_contract.py -q`: 9 passed.
- `python -m pytest tests/test_cli_module_entrypoint.py -q`: 1 passed.
- `python -m pytest tests/test_demo_loop_contract.py tests/test_open_source_contract.py tests/test_cli_jobs_e2e.py tests/test_jobs.py tests/test_cli_today_e2e.py tests/test_cli_module_entrypoint.py -q`: 19 passed.
- `python -m pytest -q`: 78 passed.
- `python -m pytest --collect-only -q`: 78 tests collected.
- `python -m phantom_tutor.cli --help`: help OK.
- Isolated smoke with `PHANTOM_TUTOR_HOME=<temp>`:
  - `jobs ingest` accepted 1 synthetic product job and dropped 1 agency record.
  - `jobs gap --n 5` seeded `mlops`, `rag`, `governance`, `platform`, and `python` as due weak spots.
  - `today` listed the seeded weak spots weakest-first.
  - `quiz --id k-softmax --answer "no idea"` recorded `softmax` mastery 0.00 and next due 2026-06-27.
  - `stats` reported 6 topics, 1 attempt, avg mastery 0.183.
- P2 synthetic career learning smoke:
  - `demo-loop --out <temp> --now 2026-06-26` wrote `manifest.json`.
  - Manifest recorded `mode=synthetic_career_learning_loop`, `data_policy=synthetic_only`, `private_data_included=false`, `external_network=false`, `llm_provider=stub_or_disabled`, and `anti_cheating_boundary=practice_only_no_live_interview_assistance`.
  - Bundle contained 9 declared artifacts, including source inputs, `weak_spots.json`, and `attempts.jsonl`; same-output rerun stayed idempotent with one attempt line and `softmax.attempts=1`.
- P2 learning-plan/evidence smoke:
  - `learning-plan-demo --source <temp>\bundle --out <temp>\plan --horizon-days 14` wrote `manifest.json`.
  - Manifest recorded `mode=synthetic_learning_plan_bundle`, `source_mode=synthetic_career_learning_loop`, `data_policy=synthetic_only`, `private_data_included=false`, `external_network=false`, `llm_provider=stub_or_disabled`, and `anti_cheating_boundary=practice_only_no_live_interview_assistance`.
  - Bundle contained `learning-plan.json`, `evidence-tracker.json`, and `summary.md`; tests verify raw answer text, private interview terms, application submission, live interview assistant wording, and job-board scraping wording are excluded from artifacts.
- P3 weak-spot-to-practice smoke:
  - `practice-scenario --source <temp>\bundle --out <temp>\practice-scenario` wrote `manifest.json`.
  - Manifest recorded `mode=synthetic_practice_scenario_bundle`, `source_mode=synthetic_career_learning_loop`, `data_policy=synthetic_only`, `private_data_included=false`, `external_network=false`, `llm_provider=stub_or_disabled`, and `anti_cheating_boundary=practice_only_no_live_interview_assistance`.
  - `practice-scenario.json` selected the synthetic job-gap weak spot `governance`, recorded deterministic design practice score `0.72`, updated mastery and SRS next-review metadata, and marked evidence/next-review readiness true.
  - `practice-evidence.json` contained metadata-only `weak_spot_selection`, `practice_result`, and `srs_update` items.
  - Contract tests verify raw answer text, full prompt text, private interview notes, application submission wording, live interview assistant wording, job-board scraping wording, and manifest path traversal are excluded or rejected.
- `agy` reviewer result: found a deterministic-output blocker around same-output reruns plus low-severity manifest/source-file gaps. Follow-ups were fixed by resetting bundle-local stores before each run, adding same-output idempotency coverage, adding source artifacts to the manifest, and documenting the expanded artifact set.
- `agy` P2 learning-plan/evidence reviewer result: `NO BLOCKERS` for live scraping, application submission, covert live-interview drift, raw answer/full-question/resume/private-interview/application-history leaks, cloud LLM/network implication, nondeterminism, docs/tests mismatch, missing synthetic/no-live flags, or missing anti-cheating boundary.
- `agy` P3 practice-scenario reviewer result: `NO BLOCKERS` for unsafe manifest/artifact paths, raw/private leaks, covert live-interview drift, job-board scraping/application submission drift, cloud LLM/network implication, nondeterminism, false readiness/SRS evidence, or CLI/docs/tests mismatch.

## P4 Release-Prep Slice 1

Status: governance baseline added; this does not mark the project release-ready.

Evidence:
- `CONTRIBUTING.md` defines the contribution workflow, required test command, readiness-doc update rule, and no-private-data/no-credentials boundary.
- `SECURITY.md` defines private vulnerability reporting, supported version scope, 7-day acknowledgement target, and safe report contents.
- `python -m pytest tests/test_release_prep_contract.py -q`: 1 passed.
- `python -m pytest -q`: 84 passed.

Remaining P4 work: full release gate, final docs audit, package metadata audit, release notes, tag plan, and maintainer sign-off.

## P4 Release-Prep Slice 2

Status: final release gate checklist added; this does not mark the project release-ready.

Evidence:
- `CHANGELOG.md` records the unreleased governance/release-checklist work and points back to readiness evidence.
- `docs/RELEASE_CHECKLIST.md` documents final tests, dependency/license review, secret/private-data scan, known limitations, and manual maintainer approval.
- `python -m pytest tests/test_release_prep_contract.py -q`: 2 passed.
- `python -m pytest -q`: 85 passed.

Remaining P4 work: execute final scans, complete dependency/license review, finalize release notes, and record manual maintainer approval.

## P4 Release-Prep Slice 3

Status: final scan and direct dependency/license audit recorded; not release-ready.

Evidence:
- `docs/FINAL_RELEASE_AUDIT.md` records scan scope, `high_conf_secret_hits=0`, direct dependency/license review, and remaining release blockers.
- Direct release-scope dependency metadata reviewed: `fsrs==6.3.1` MIT.
- `python -m pytest tests/test_release_prep_contract.py -q`: 3 passed.
- `python -m pytest -q`: 86 passed.

Remaining P4 work: release notes finalization, tag plan, final maintainer approval, and separate review for any live job-board/application/interview integration.

## P4 Release-Prep Slice 4

Status: maintainer approval recorded, conductor sign-off complete, and release-candidate tag created.

Evidence:
- `docs/RELEASE_NOTES.md` records public release-candidate notes, known limitations, and verification pointers.
- `docs/TAG_PLAN.md` records proposed tag `v0.1.0-alpha.0`, required approval-before-tag sequence, and rollback steps.
- `docs/PUBLIC_RELEASE_APPROVAL.md` records `Status: approved` with approver, approval date, and approved tag.
- Conductor root approval packet `PHANTOM-SATELLITES-PUBLIC-RELEASE-APPROVAL.md` records all ten candidate tags as approved.
- `.github/workflows/ci.yml` runs an explicit `release-prep gate` against `tests/test_release_prep_contract.py`.
- `python -m pytest tests/test_release_prep_contract.py -q`: 5 passed.
- `python -m pytest -q`: 88 passed.

Remaining P4 work: none for the approved release-candidate tag.

## P4 Release-Prep Slice 5

Status: installable public package gate added and ready with documented limitations.

Evidence:
- `pyproject.toml` defines `phantom-tutor` version `0.1.0a0`, Apache-2.0 license metadata, Python `>=3.11`, classifiers, project URLs, `fsrs` runtime dependency, dev extra, package discovery, package data, and console script.
- Seed banks under `content/knowledge`, `content/coding`, and `content/design` are packaged so installed CLI modes can load the same public practice content as source checkouts.
- `.github/workflows/ci.yml` now runs editable install, install dry-run, wheel build, ruff, deterministic demo/learning-plan/practice smokes, full `python -m pytest -q`, and release-prep gate.
- `tests/test_packaging.py` verifies package metadata, console script, packaged seed content, and module help.
- Current verification on 2026-06-27 is recorded in `docs/FINAL_RELEASE_AUDIT.md`.
- `python -m pytest tests/test_packaging.py tests/test_release_prep_contract.py tests/test_open_source_contract.py -q`: 14 passed.
- `python -m pytest -q`: 93 passed.
- `python -m pip install -e . --dry-run --no-deps`: would install `phantom-tutor-0.1.0a0`.
- `python -m pip wheel . --no-deps -w <temp>`: built `phantom_tutor-0.1.0a0-py3-none-any.whl`.
- Wheel package-data verification: `content/knowledge/seed.json`, `content/coding/seed.json`, and `content/design/seed.json` are present.
- `python -m ruff check phantom_tutor tests`: all checks passed.
- `python -m pip install -e . --no-deps`: installed `phantom-tutor-0.1.0a0`.
- Installed console script `tutor --help`: OK.
- Deterministic demo/learning-plan/practice smoke wrote manifests with `data_policy=synthetic_only`, `private_data_included=false`, `external_network=false`, `llm_provider=stub_or_disabled`, and `anti_cheating_boundary=practice_only_no_live_interview_assistance`.
- High-confidence secret scan: `high_conf_secret_hits=0`.

Remaining P4 work: none for the installable public release-candidate gate; live job-board scraping, application submission, live LLM output, personalized data sync, and covert interview assistance remain out of public release scope.
