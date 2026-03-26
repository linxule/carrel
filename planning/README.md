# planning/

Open planning folder for Carrel's core library extraction. Any model (Claude, Codex, Gemini, Kimi, GPT) can read, review, and contribute.

## Structure

```
planning/
├── specs/      # Task specifications — the "what" and "how"
├── reviews/    # Feedback on specs from any model — improvements, concerns, alternatives
├── reports/    # Implementation reports — what was built, decisions made, issues found
└── README.md
```

## Workflow

1. **Spec** goes in `specs/` — numbered, detailed, with acceptance criteria
2. **Any model reviews** — saves feedback in `reviews/` referencing the spec number
3. **Spec gets refined** based on reviews
4. **Codex (or whoever) implements** — saves report in `reports/`
5. **Human decides** what ships

## Naming

- Specs: `001-short-title.md`
- Reviews: `001-review-<model>.md` (e.g., `001-review-gemini.md`)
- Reports: `001-report-<model>.md` (e.g., `001-report-codex.md`)

## Current

- `specs/001-core-library-extraction.md` — Extract Carrel's mechanical layer into a Python core library (pydantic + typer + rich)
