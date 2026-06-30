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
| Codex CLI, IDE, and Codex desktop | High | Install the full folder as `.agents/skills/carrel`, `~/.agents/skills/carrel`, or a Codex plugin skill; symlinked skill folders are supported. `agents/openai.yaml` is Codex-facing metadata. |
| Claude Code | High | Install the full folder as `.claude/skills/carrel` or `~/.claude/skills/carrel`; optional slash commands and hooks should call this runtime. |
| Claude app/API | Partial | Upload as a custom Agent Skill zip for cloud/container execution; local vault writes require uploaded/downloaded files, a connector, or a desktop/Cowork flow. |
| Claude Desktop/Cowork | Partial | Local vault access requires connected folders, desktop extensions, local MCP, or Cowork. Do not assume local `SKILL.md` folder discovery like Claude Code. |
| Kimi Code CLI | High | Install the full folder under `.kimi-code/skills/carrel`, `.agents/skills/carrel`, `~/.kimi-code/skills/carrel`, or `~/.agents/skills/carrel`; plugin packaging can point at `./skills/`. |
| Kimi app / Kimi Work | Partial | Good fit for instruction/document skills, but not a verified host for bundled local scripts. Use Kimi Code or another local harness when `scripts/carrel.py` must write a vault. |
| OpenCode | High | Install under `.agents/skills/carrel`, `.opencode/skills/carrel`, `~/.agents/skills/carrel`, or `~/.config/opencode/skills/carrel`; ensure read/bash/skill permissions allow `scripts/carrel.py`. |
| Gemini CLI | High where Agent Skills are enabled | Install under `.agents/skills/carrel` or `.gemini/skills/carrel`; skill activation must be allowed to access bundled scripts/assets. |
| Other local harnesses | Unknown until verified | Require explicit support for `SKILL.md` discovery, bundled files, local shell execution, Python 3.10+, and a stable skill-dir path. |

Cloud provider calls (`mineru`, `groq`, `gemini`) are not implemented in the
portable stdlib runtime. Host adapters may add them behind the same routing
policy.
