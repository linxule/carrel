# Review: 001 Core Library Extraction (v2)

## 1. Overall Assessment
The v2 specification is exceptionally strong. It thoughtfully synthesizes the feedback from all previous reviews into a rigorous set of rules and constraints. By explicitly defining the boundaries of local vs. cloud toolsets and strictly enforcing deterministic behaviors, this spec outlines a highly robust, agent-friendly core library.

## 2. Key Improvements & Resolutions
- **Local-First & Cloud Opt-In (Rule 1 & 2)**: This is the most crucial improvement. Forcing an explicit `cloud_consent` or `--cloud` flag entirely eliminates privacy risks for sensitive research data. Deferring `mlx-whisper` to the transport layer (MCP) cleanly enforces the "deterministic core" philosophy.
- **Explicit Vault Resolution (Rule 5)**: Defining a strict path resolution hierarchy (Flag → Env Var → Upward Walk) solves a major UX pain point and simplifies internal function signatures.
- **Deterministic Fallbacks (Rule 4)**: The metadata fallback table prevents the system from getting "stuck" when parsing fails. Proceeding with known data (like filename) is exactly what a sub-agent pipeline needs to remain unbroken.
- **Structured Errors (`errors.py`)**: The introduction of `CarrelError` with a mandatory `hint` field is a masterclass in "CLI for Agents" design. When an agent (or human) fails an invocation, providing the exact fix in the error output drastically reduces recovery time. 

## 3. Data Models & Routing
- The new `ToolAvailability` model nicely segregates binaries, API keys, and MCP servers. This separation acknowledges that checking for a local binary requires a `subprocess` call, whereas checking an API key is just an `os.environ` lookup.
- The `FileResult` and `ScaffoldResult` schemas provide necessary granularity, clarifying exactly what the library *did* (e.g., created, skipped, updated) instead of just returning a path.
- The timeouts added to subprocess operations (e.g., 30s for `lit parse`, 300s for transcribed audio) will prevent zombie processes and hanging agents. 

## 4. Minor Observations
- **Hash Idempotency**: The decision to check source file hashes before skipping (added in `filer.py`) is brilliant. This ensures that if a user replaces an audio file with an edited version but keeps the same filename, the system will correctly realize the output is stale.
- **Timeouts & Large Videos**: A 300s timeout for YouTube/Gemini transcription is generally safe, but for extremely long videos (e.g., 2+ hour lectures), the Gemini API might take longer or require polling. If `httpx` timeouts become an issue in practice, consider allowing a `--timeout` override flag on the CLI for edge cases.

## 5. Conclusion
This v2 spec leaves no ambiguity. The acceptance criteria are testable, constraints are rigid, and the design rules solve the core architectural paradoxes of building an AI-orchestrated deterministic tool. It is 100% ready for implementation.
