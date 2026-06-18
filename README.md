# phantom-tutor

學習輔助 / personal study assistant — built on phantom-mesh core (owned-memory + multi-provider LLM + governor). AI-engineer interview prep is the headline use case.

Status: see [ROADMAP.md](ROADMAP.md). Design: [docs/2026-06-18-phantom-tutor-design.md](docs/2026-06-18-phantom-tutor-design.md). All docs: [docs/INDEX.md](docs/INDEX.md).

## Usage (hermetic, LLM-stubbed by default in dev)

    tutor quiz --id k-softmax --answer "subtract max for numerical stability"
    tutor code --id c-add --solution my_add.py
    tutor design --id d-rag --answer my_answer.txt
    tutor interview --focus LLM --answer "RAG retrieves and grounds the answer"
    tutor today          # SRS-due topics, weakest first
    tutor weak-spots     # your weakest topics
    tutor stats          # progress

Modes write to the weak_spots spine (`$PHANTOM_TUTOR_HOME/weak_spots.json`); SRS resurfaces
the weak/due ones via `tutor today`. LLM goes through `phantom exec` (set
`PHANTOM_TUTOR_STUB_LLM=1` for offline/dev).

For what has shipped and what's planned next, see [ROADMAP.md](ROADMAP.md).
