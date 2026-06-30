# Host Compatibility

Install or expose the entire `carrel/` skill folder. Do not copy only
`SKILL.md`: runtime imports need `scripts/carrel_core/`, and vault setup needs
`assets/templates/`.

## Invocation

The examples assume the current directory is the skill folder. When a host runs
from a project or vault directory, call the runtime by absolute path:

```bash
python3 <skill-dir>/scripts/carrel.py env validate --vault <vault> --format json
```

Python 3.10 or newer is required.

## Harness Notes

| Harness | Compatibility | Adapter work |
| --- | --- | --- |
| Codex CLI and Codex desktop | High | Copy or symlink the full folder into a Codex skill location. |
| Claude Code | High | Copy or symlink the full folder into a Claude Code skill location; optional slash commands should call this runtime. |
| Claude desktop/chat | Partial | Can use the instructions as a skill-like artifact, but local vault filesystem writes require a connector, extension, or code-execution adapter. |
| Kimi Code | Likely high | Use if the installed Kimi surface can read local skill folders and run shell commands; otherwise wrap as a plugin/marketplace adapter. |
| Kimi desktop/chat | Uncertain | Do not assume local `SKILL.md` folder loading or local filesystem script execution without confirming the active app. |
| Other local agent harnesses | Medium-high | Needs local file access, shell execution, Python 3.10+, and a way to pass the skill directory path. |

Cloud provider calls (`mineru`, `groq`, `gemini`) are not implemented in the
portable stdlib runtime. Host adapters may add them behind the same routing
policy.
