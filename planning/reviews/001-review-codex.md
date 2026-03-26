# Review: 001 Core Library Extraction

## Findings

### 1. Auto-routing to cloud tools contradicts the spec's own privacy constraint

`planning/specs/001-core-library-extraction.md:241-247` makes `mineru` the default PDF choice when available, and `planning/specs/001-core-library-extraction.md:300-307` makes `gemini` or `groq` automatic transcription choices. That directly conflicts with `planning/specs/001-core-library-extraction.md:514-516`, which says the library must not make network calls unless the user explicitly chose a cloud tool. As written, an implementation can either follow the router or follow the constraint, but not both. This needs one rule: either cloud tools are opt-in only via `--tool`, or automatic routing is allowed for profiles that explicitly permit cloud processing.

### 2. The transcription spec can select `mlx-whisper`, but no implementation path is defined

`planning/specs/001-core-library-extraction.md:77-85` defines adapters only for `coli`, `groq`, and `gemini`, but `planning/specs/001-core-library-extraction.md:129-134` and `planning/specs/001-core-library-extraction.md:300-307` include `mlx-whisper` as a first-class tool and even make it the preferred local choice on capable hardware. The referenced skill also treats MLX Whisper as an MCP-backed capability rather than a local Python library (`skills/transcribe/SKILL.md:37-49`). Without an adapter contract or transport boundary for that tool, the router can legitimately return a tool the package cannot execute.

### 3. The filesystem constraint forbids behavior required elsewhere in the same spec

`planning/specs/001-core-library-extraction.md:516` says "Do NOT read or write files outside the vault path," but the same spec requires reading project and desktop MCP configs in `env doctor` (`planning/specs/001-core-library-extraction.md:206-210`), and the acceptance criteria require converting arbitrary input files via `carrel paper convert <any-pdf>` and `carrel transcript create <audio-file>` (`planning/specs/001-core-library-extraction.md:502-506`). Those source files will often live outside the vault before filing. The constraint should be narrowed to something like "do not write outside the target vault, except explicit input paths and read-only config inspection."

### 4. The acceptance criteria disagree with the router on which PDF tool should be used

Acceptance criterion 4 says `carrel paper convert <any-pdf>` should convert using LiteParse if installed (`planning/specs/001-core-library-extraction.md:505`), but the router spec prefers `mineru` whenever it is available and the file is not high-sensitivity (`planning/specs/001-core-library-extraction.md:243-247`). That means the same environment can satisfy the routing rules and fail the acceptance test. The spec should decide whether LiteParse is the default local baseline or whether MineRU is the preferred automatic choice.

### 5. Several function signatures cannot represent the behavior the spec requires

`file_paper()` returns only `Path`, but the same section requires idempotent behavior with `skipped=True` (`planning/specs/001-core-library-extraction.md:275-286`). `scaffold_vault()` returns `list[str]`, but the required behavior is to report what was created versus skipped (`planning/specs/001-core-library-extraction.md:330-341`). These contracts will force the implementation either to invent undocumented side channels or to ignore part of the behavior. Result models for file operations should be specified explicitly.

### 6. The library is defined as non-judgmental and non-interactive, but key metadata flows still depend on human interpretation

The top-level rule says the core library never asks questions and only works from explicit parameters (`planning/specs/001-core-library-extraction.md:15`). But the referenced conversion and transcription flows still rely on "extract or ask researcher" metadata and descriptive naming decisions (`skills/convert/SKILL.md:82-130`, `skills/transcribe/SKILL.md:92-115`). The current Python API does not define what happens when title, authors, year, participant code, or transcript topic cannot be inferred. Without deterministic fallback rules, different transports will implement incompatible heuristics.

### 7. Tool availability inputs are underspecified for the routers and `env doctor`

Both routers depend on `available_tools: dict[str, bool]`, but the audit spec only clearly covers installed binaries plus Obsidian/Zotero (`planning/specs/001-core-library-extraction.md:206-212`). The example output for `env doctor` also expects configured cloud-tool status such as "MINERU_API_KEY missing" (`planning/specs/001-core-library-extraction.md:433-441`), which is not represented in `AuditResult` and is not part of the referenced JS audit script (`skills/environment-setup/scripts/check-environment.js:84-149`). The spec should define one canonical availability model covering binaries, MCP-backed tools, and API-key-backed tools; otherwise routing decisions and doctor output will drift.

## Open Questions

1. Should cloud tools ever be auto-selected, or must `--tool mineru|groq|gemini` always be explicit?
2. Is `mlx-whisper` supposed to be part of the core package, or should it stay transport-only via MCP?
3. What are the deterministic fallback naming rules when paper or transcript metadata is incomplete?

## Summary

The spec is directionally solid, but it currently has a few hard contradictions around cloud routing, filesystem access, and tool availability. Tightening those contracts before implementation will prevent the Python package from baking in transport-specific assumptions or privacy regressions.
