# Roadmap

> Single source of truth for project status. Date-stamped **2026-06-19**.
> Everything below is grounded in the actual git history of this repo — nothing is aspirational
> unless it sits under **Planned-next**. For *what the product is*, see [README.md](README.md);
> for *how it is designed*, see [docs/2026-06-18-phantom-tutor-design.md](docs/2026-06-18-phantom-tutor-design.md).

phantom-tutor is an early repo: the Phase-1 skeleton and the Phase-2 additive deepening
have both landed. It runs a real `tutor` CLI end-to-end, but most modes are still
deliberately thin (a seed-sized content bank + simple grading), with the deeper
work explicitly deferred. The sections below are honest about what is a skeleton
versus what is built out.

## Shipped

**Phase-1 MVP — the spine (merged `14c4cc0`).** A real `tutor` CLI standing on a
`weak_spots` owned-memory spine, every mode proven by an end-to-end test through
`cli.main([...])`, fully hermetic (LLM stubbed via `PHANTOM_TUTOR_STUB_LLM=1`, tmp
`PHANTOM_TUTOR_HOME`, never the real `~/.phantom-mesh`):

- **`weak_spots` memory spine** (`memory.py`) — `record_attempt` / `due_topics` /
  `list_weak`; local-JSON backend behind a swappable interface (deep enough for daily
  use; the Phase-2 swap to phantom core owned-memory is still pending).
- **SRS scheduler** (`srs.py`) — SM-2-lite interval growth + `is_due`. *(built out)*
- **4 practice modes**, all CLI-reachable and writing to the spine:
  - `tutor quiz` — knowledge, keyword-graded. *(thin: simple keyword overlap)*
  - `tutor code` — sandboxed subprocess runner, pass-rate score. *(runner built out;
    bank still small)*
  - `tutor design` — LLM-graded against a rubric (stubbed in tests). *(thin)*
  - `tutor interview` — mock interviewer that reads your weak spots (single-turn in
    Phase-1). *(thin)*
- **Daily loop** — `tutor today` (SRS-due, weakest-first) + `tutor weak-spots` +
  `tutor stats`.
- **Sandboxed code-runner** (`runner.py`) — subprocess + timeout + pass-rate. *(built out)*
- **Content layer** — seed banks + `content/scenarios.md`, the canonical 6-dimension
  interview-scenario playbook.

**Phase-2 — additive deepening (merged `f990361`).** Three backward-compatible slices,
all CLI-reachable and e2e-tested; every Phase-1 default byte-unchanged:

- **Bigger seed banks** grounded in `scenarios.md`: knowledge 2 → 19 items, +4
  sandbox-verified coding problems (6 total), +3 design rubrics (4 total). *(still
  seed-sized, not exhaustive)*
- **Optional LLM-graded knowledge** — `tutor quiz --llm` (keyword grading stays the
  default and byte-unchanged).
- **Multi-turn mock interview** — `tutor interview --turns N` (single-turn stays the
  default).

## In progress

- Nothing is mid-flight as of 2026-06-19. The `phase-1` and `phase-2` branches are both
  merged into `master`; the working tree is clean.

## Planned-next

Deferred from the design spec (see §4 and §9 of
[the design doc](docs/2026-06-18-phantom-tutor-design.md)); none of these have landed yet:

- **Real owned-memory backend** — re-point the `weak_spots` interface from local JSON at
  phantom core owned-memory (Hermes / FTS5) so weak spots are encrypted, cross-device,
  and vendor-invisible. This is the headline apex-② moat and is **not yet implemented**.
- **Deeper modes** — richer knowledge bank + LLM free-answer grading quality; coding
  hint tiers + complexity feedback; design reference-architecture library + follow-ups;
  interview deeper follow-up chains and tone/pacing.
- **Governor / mesh integration** — wrap long sessions in `phantom govern`; dispatch
  heavy grading to GPU mesh nodes.
- **Progress visualisation.**

## Explicitly out of scope

Per the design spec §10: no `ai-feed`/`training` composition (parallel satellites, core
only); no changes to phantom core/apex; no accounts / cloud sync / paid tiers; no scraping
of question-bank sites (seed + self-authored to avoid copyright); never touch real
LLM / real mesh / real `~/.phantom-mesh` in tests.
