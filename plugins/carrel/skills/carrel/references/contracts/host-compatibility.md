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

Python 3.10 or newer is required. Before invoking the runtime on an unfamiliar
host, run `python3 --version` and stop if it reports an older interpreter.

## Harness Notes

| Harness | Compatibility | Adapter work |
| --- | --- | --- |
| Claude Code native Carrel plugin | Fullest adapter | The repository-root plugin provides native commands, agents, hooks, and typed CLI integrations. Its hooks and commands use the installed `carrel` CLI. |
| Claude Code, portable skill only | Shared core | Install the full folder as `.claude/skills/carrel` or `~/.claude/skills/carrel`; this uses the bundled runtime and does not provide the native plugin's commands, hooks, or agents. |
| Codex CLI and supported Codex plugin surfaces | Shared core, host-dependent execution | Install through the Agent Plugins package/marketplace or install the full folder as `.agents/skills/carrel` / `~/.agents/skills/carrel`. Confirm that the selected surface can execute Python and access the intended vault. `agents/openai.yaml` is Codex-facing metadata. |
| GitHub Copilot app and CLI | Shared core, host-dependent execution | Install the Agent Plugins package from a marketplace (`.github/plugin/marketplace.json`) or directly with `copilot plugin install linxule/carrel:plugins/carrel`. This package currently provides the portable skill; it does not yet include Copilot-specific agents, commands, or hooks. Confirm that the selected surface can execute Python and access the intended vault. |
| Claude app / Cowork | Partial | Upload `carrel.zip` (built by `scripts/build-skill-zip.py`; published at the `skill-latest` release) in Customize > Skills > + > Create skill > Upload a skill, with code execution enabled. The ZIP's root folder must be named `carrel`. Local vault writes require a connected folder or another supported local-file integration; remote-only execution cannot be assumed to reach a local vault. |
| Kimi Code CLI | Shared core, host-dependent execution | Install the plugin with `/plugins install https://github.com/linxule/carrel` (Kimi reads `kimi.plugin.json`, whose explicit `skills` path exposes only this skill), or install the full folder under `.kimi-code/skills/carrel`, `.agents/skills/carrel`, `~/.kimi-code/skills/carrel`, or `~/.agents/skills/carrel`. Plugin installs are per-user and copied to a managed directory; reinstall after updating. Kimi does not run plugin scripts on install, so confirm `python3 scripts/carrel.py --help` works on first use. |
| OpenCode | Skill compatibility documented; plugin behavior not verified here | Install under `.agents/skills/carrel`, `.opencode/skills/carrel`, `~/.agents/skills/carrel`, or `~/.config/opencode/skills/carrel`; ensure read/bash/skill permissions allow `scripts/carrel.py`. |
| Gemini CLI | Skill compatibility where Agent Skills are enabled; plugin behavior not verified here | Install under `.agents/skills/carrel` or `.gemini/skills/carrel`; skill activation must be allowed to access bundled scripts/assets. |
| Other harnesses | Not verified | Require explicit support for `SKILL.md` discovery, bundled files, local shell execution, Python 3.10+, and a stable skill-dir path. Do not infer plugin-format or lifecycle-hook support from skill support alone. |

## Parity Contract

The portable skill is the shared workflow core, not a copy of every host's
plugin components. Claude-native commands, hooks, agents, setup-state, and
migration behavior are adapters. Other hosts may expose different entry points,
but shared workflows must preserve trust checks, sensitivity/cloud-consent
decisions, vault containment, idempotency, and clear reporting when a tool or
host capability is unavailable. See the repository's cross-host parity
assessment maintained with the repository's planning and review artifacts.

Cloud provider calls (`mineru`, `mistral_ocr`, `groq`, `gemini`) are not
implemented in the portable stdlib runtime. Host adapters may add them behind
the same routing policy.
