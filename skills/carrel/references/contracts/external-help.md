# External Help And Source Links

Use `external-refresh.json` as Carrel's source map for upstream packages,
cloud APIs, host harness claims, and documentation contracts.

## When To Open Upstream Sources

Open the `sources` links for an entry when:

- an adapter call fails with a schema, endpoint, auth, or CLI-shape error;
- a package install command, binary name, model alias, or version appears stale;
- a host harness claim affects install instructions or local script execution;
- a scheduled refresh is checking whether captured skill guidance drifted.

Prefer local skill references first for ordinary Carrel workflows. Use upstream
sources to resolve uncertainty, not as required context for every invocation.

## How To Refresh An Entry

For each changed upstream contract:

1. Check the entry's `sources`.
2. Run `version_probe` when it exists.
3. Compare the live contract with `contract_marker`.
4. Update affected files listed in `skill_references` and, when working in the
   source repo, `repo_references`.
5. Update `observed_version`, `last_reviewed`, `refresh_checks`, and tests when
   the contract changes.

If a new package, API, or host adapter is added, create an entry before wiring
it into skill prose. Every entry must include actionable `sources`,
`skill_references`, `repo_references`, `refresh_checks`, and `rationale`.

## Current OCR Pointers

- Mistral OCR: see the `mistral-ocr` entry for the OCR endpoint, Files API,
  OCR guide, and OpenAPI schema links.
- PaddleOCR: see the `paddleocr` entry for install docs, PP-StructureV3 API
  docs, and PyPI version tracking. Treat PaddleOCR as an evaluated optional
  local OCR candidate until a deterministic adapter is added.
