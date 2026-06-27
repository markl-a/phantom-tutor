# Final Release Audit

Status: release candidate approved and tagged.

Date: 2026-06-27

## Scope

- Default release surface: `phantom_tutor` package and synthetic/local study commands.
- Excluded scan noise: `.git`, `.ensemble`, `.venv`, `venv`, `__pycache__`, `.pytest_cache`, `reports`, `dist`, and `build`.

## Secret And Private-Data Scan

Command class: `rg` high-confidence patterns for private keys, AWS access keys, GitHub tokens, OpenAI-shaped keys, Slack tokens, and Google API keys.

Result: `high_conf_secret_hits=0`.

## Dependency/License Review

- Project license: Apache-2.0.
- Default runtime dependency: `fsrs>=6.3.1,<7`; metadata sample reviewed as `fsrs==6.3.1`, MIT.

Direct default release-scope dependency/license review result: pass.

## Install And Wheel Verification

- Install dry-run: `python -m pip install -e . --dry-run --no-deps` passed and would install `phantom-tutor-0.1.0a0`.
- Wheel build: `python -m pip wheel . --no-deps -w <temp>` passed and built `phantom_tutor-0.1.0a0-py3-none-any.whl`.
- Editable install: `python -m pip install -e . --no-deps` passed.
- Package-data check: wheel includes `content/knowledge/seed.json`, `content/coding/seed.json`, and `content/design/seed.json` so installed CLI modes can load public practice banks.
- CLI help: `python -m phantom_tutor.cli --help` and installed `tutor --help` expose deterministic synthetic public demo paths.
- Lint: `python -m ruff check phantom_tutor tests` passed.

## Current Verification

- `python -m pytest tests/test_packaging.py tests/test_release_prep_contract.py tests/test_open_source_contract.py -q`: 14 passed.
- `python -m pytest -q`: 93 passed.
- Deterministic public smoke: `phantom_tutor.cli demo-loop`, `learning-plan-demo`, and `practice-scenario` wrote manifests with synthetic/offline/no-private-data/no-live-LLM/practice-only boundaries.
- High-confidence secret scan: `high_conf_secret_hits=0`.

## Remaining Publication Gates

- Manual maintainer approval is recorded in `docs/PUBLIC_RELEASE_APPROVAL.md`.
- Local annotated tag `v0.1.0-alpha.0` was created after the root strict approval verifier and conductor sign-off passed.
- Any future live job-board, application-submission, or interview-assistant integration requires separate dependency/license and anti-cheating review.
