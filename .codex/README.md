# .codex/

Communication folder for delegating work to Codex, Gemini, and other agents.

## Structure

```
.codex/
├── specs/          # Task specifications (input to agents)
├── reports/        # Agent outputs, analysis, implementation reports
└── README.md
```

## Convention

- Specs are numbered: `001-core-library-extraction.md`
- Reports reference their spec: `001-report-codex.md`, `001-report-gemini.md`
- Specs include context, constraints, acceptance criteria, and file references
- Agents save their work products (code, analysis) in reports/
