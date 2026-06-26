# Final Release Audit

Status: release-tagged locally; remote publication pending.

Date: 2026-06-26

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

## Remaining Publication Gates

- Manual maintainer approval is recorded in `docs/PUBLIC_RELEASE_APPROVAL.md`.
- Local annotated tag `v0.1.0-alpha.0` was created after the root strict approval verifier and conductor sign-off passed.
- Any future live job-board, application-submission, or interview-assistant integration requires separate dependency/license and anti-cheating review.
