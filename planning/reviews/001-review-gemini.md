# Review: 001 Core Library Extraction

## 1. Overall Assessment
The specification for extracting Carrel's deterministic operations into a Python core library is well-structured, clear, and highly feasible. Moving away from prompt-driven execution for mechanical tasks (file conversion, tool orchestration, vault scaffolding) into a typed, testable Python library (`carrel`) will significantly improve reliability, observability, and speed.

## 2. Architecture & Tech Stack
- **Python 3.11+, uv**: Excellent choice for isolated, reproducible environments.
- **Pydantic + Typer + Rich**: The industry standard for modern, robust Python CLI applications. This combination guarantees strict type validation for inputs/outputs, seamless help generation, and an excellent terminal UX.
- **Asyncio + httpx**: Proper usage of `asyncio.create_subprocess_exec` and async HTTP clients will prevent blocking operations, which is crucial for long-running shell tasks like transcription or local PDF conversion.

## 3. Data Models (`models.py`)
- The data models are comprehensive and well-tailored. `ConvertResult` and `TranscribeResult` providing `duration_seconds` and `skipped` flags directly support the observability and idempotency requirements.
- **Suggestion**: `ConvertOptions` and `TranscribeOptions` require a `vault` Path. Consider allowing the CLI app to implicitly resolve the vault path either via an environment variable (e.g., `CARREL_VAULT`) or by looking for the `.carrel/environment.json` file in parent directories, to reduce repetitive flags.

## 4. Module Boundaries & Routing
- The separation of concerns is clean. Adapters (`liteparse.py`, `mineru.py`, `coli.py`) encapsulate the messy details of subprocess and API calls, while routers (`convert/router.py`, `transcribe/router.py`) handle the complex decision matrix.
- The routing logic correctly falls back to more accessible methods (e.g., `markdownify`) if specialized tools aren't available or if hardware is constrained. This ensures graceful degradation across different environments.

## 5. CLI Design Principles
- The 10 CLI design principles outlined are excellent, particularly the emphasis on non-interactive execution, idempotency, `--dry-run`, and structured `--format json` output. This ensures the CLI is extremely "agent-friendly" and composable for higher-level AI orchestration.
- Having the CLI return actionable errors instead of crashing is a crucial insight that aligns perfectly with the needs of thin-layer transports and LLM tools.

## 6. Potential Edge Cases & Risks
- **Subprocess Management**: When shelling out to tools like `coli` or `lit`, ensure graceful timeout handling and standard error parsing. Obscure native crash logs from these tools should be caught and translated into the structured "actionable errors" required by the spec.
- **Path Resolution**: Ensure `pathlib.Path` variables are properly resolved using `.expanduser()` and `.resolve()` early in the CLI pipeline, as file paths from agents/users can often be relative or contain bash expansions (`~/...`).
- **Idempotency Hashing**: For `TranscribeOptions` and `ConvertOptions`, consider how idempotency is verified. If checking just by filename, changes in the source file won't trigger a re-run. A fast hash of the source file or relying strictly on explicit `--force` flags might be necessary.

## 7. Conclusion
The specification is mature and ready for implementation. The boundaries between the ML/AI reasoning layer and the deterministic execution layer are strictly and smartly defined, which will make both Carrel and eventually ItDepends much easier to test, extend, and scale.
