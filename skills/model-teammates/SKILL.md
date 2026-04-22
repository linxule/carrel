---
name: model-teammates
description: "This skill should be used when a researcher wants to add, remove, or review multi-model agent teammates (Codex/ChatGPT, Gemini, Kimi) inside Claude Code. Triggers on 'teammates', 'multi-agent', 'multi-model', 'second opinion', 'add Gemini', 'use ChatGPT here', 'orchestrate models', or when `/carrel-setup` enters Phase 5b."
---

# model-teammates

Guides researchers through adding foundation models as teammates inside Claude Code via three community plugins. Most researchers don't realize this is possible — the interview protocol's "About Model Teammates" beat carries the spoken script; this skill owns the operational details.

## Research moves

| Teammate | Reach for when | Plugin |
|---|---|---|
| **Codex** (ChatGPT) | Adversarial / second-opinion review on a claim or methods paragraph | `openai/codex-plugin-cc` |
| **Gemini** | Long-context / whole-corpus synthesis (hundreds of PDFs, large codebases) | `thepushkarp/cc-gemini-plugin` |
| **Kimi** | Delegated bug hunts, refactors, free-form Q&A with CLI-auth privacy | `linxule/kimi-plugin-cc` |

If the researcher already pays for ChatGPT Plus/Pro or Gemini Advanced, the teammate runs on that subscription — no extra cost. Kimi's CLI handles auth locally.

## Orientation

Read `.carrel/environment.json` → `model_teammates`. Status values:

- `configured` — plugin installed + verified
- `interested` — said yes but deferred install
- `skipped` — declined; don't re-ask
- (absent) — not yet discussed

Also read `sensitivity` on the profile. All three teammates route prompts through external providers (OpenAI, Google, Moonshot) — including Kimi despite its local CLI auth. HIGH sensitivity → don't propose; record `skipped`. MEDIUM → surface but confirm consent. LOW → proceed.

## Install flow

For each teammate the researcher chooses:

1. Install the provider's CLI and log in (researcher runs the commands — interactive auth needs human hands).
2. Install the Claude Code plugin from the marketplace and reload.
3. Verify via the plugin's own setup command if it has one (`/codex:setup`, `/kimi:setup`; Gemini has no dedicated setup — run a small query).

Plugin install commands inside Claude Code:

```
/plugin marketplace add openai/codex-plugin-cc        && /plugin install codex@openai-codex        && /reload-plugins && /codex:setup
/plugin marketplace add thepushkarp/cc-gemini-plugin  && /plugin install cc-gemini-plugin@cc-gemini-plugin && /reload-plugins
/plugin marketplace add linxule/kimi-plugin-cc        && /plugin install kimi@kimi-marketplace     && /kimi:setup
```

CLI install commands (each upstream README is authoritative — Claude fetches on demand if anything has drifted):

- **Codex**: `npm install -g @openai/codex` → `codex login`
- **Gemini**: `npm install -g @google/gemini-cli` (or `brew install gemini-cli`) → `gemini auth`
- **Kimi**: `npm install -g kimi-cli` → `kimi login` (upstream: <https://github.com/MoonshotAI/kimi-cli>)

## State writeback

After each install / defer / decline / removal, update `model_teammates` in `.carrel/environment.json` and regenerate the dashboard:

```bash
carrel vault dashboard --vault <path> --force
```

## Removing a teammate

Uninstall the plugin (`/plugin uninstall ...`), optionally remove the CLI, delete the teammate's key from `model_teammates` in `environment.json` (or set to `skipped` if you want to remember "don't re-ask"), regenerate the dashboard.

## Related

- **Command**: `/carrel-teammates` (this skill's standalone entry)
- **Setup**: `/carrel-setup` Phase 5b invokes this skill during onboarding
- **Spec**: `planning/specs/013-model-teammates.md`
