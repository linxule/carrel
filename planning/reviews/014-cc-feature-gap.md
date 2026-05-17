# 014 — Claude Code Feature Gap Audit (pre-v0.9.0)

**Scope**: what carrel's plugin manifest does NOT use that would meaningfully improve CC-user UX. Assumes spec 014 already covers whatever it covers; this is the residual.

**Surveyed**: `code.claude.com/docs/en/{plugins,plugins-reference,hooks,plugin-marketplaces,output-styles}` as of 2026-05-17.

---

## Top 3 highest-leverage adds for v0.9.0

1. **`UserPromptSubmit` hook** (HIGH) — `hooks/hooks.json`. Inject vault context (current sensitivity, trust level, active brief, last-used tool) once per turn, not just at session start. Today the session-start dump goes stale fast; researchers ask "convert this PDF" 40 turns in and Claude has lost the routing context. The hook output supports `additionalContext` and `decision: "block"` — same shape as the existing `check-environment.js`. Two-line addition to `hooks.json`, ~30-line Node script that reads `.carrel/environment.json` + `_meta/briefs/`.

2. **Marketplace metadata expansion** (HIGH) — `.claude-plugin/marketplace.json`. Current entry has 6 fields. Missing: `keywords` (research, obsidian, pdf, transcription, academic, vault, zotero), `category` ("productivity" or "research"), `tags`, `license` (SPDX), `repository`. The official marketplace submission form (`claude.ai/settings/plugins/submit`) and `/plugin` Discover tab use these for search ranking. Zero-risk, ~10-minute change with outsized discoverability impact for "perfect-for-CC-users" framing.

3. **`PreToolUse` matcher on Bash for `carrel` invocations** (MED-HIGH) — `hooks/hooks.json` with matcher `"Bash"`. When Claude is about to run `carrel paper convert <high-sensitivity-PDF> --tool mineru`, the hook can return `permissionDecision: "ask"` with a sensitivity warning, or `"deny"` with the actionable hint. Today the policy module enforces this at the CLI level (correct boundary), but the CC-side hook gives the researcher a visual confirmation step before the subprocess fires — a meaningful UX upgrade for the trust ladder. Reuses existing `carrel trust check` + `--explain` logic; the hook just shells out.

---

## Survey: features carrel doesn't use, judged

### Hook events not subscribed

| Event | Value | Verdict |
|---|---|---|
| `UserPromptSubmit` | HIGH — per-turn context injection (see #1) | Adopt |
| `PreToolUse` (Bash matcher) | MED-HIGH — sensitivity ask-gate (see #3) | Adopt |
| `PreCompact` | MED — flush brief/reflection state to `_meta/` before compact wipes it; today reflections live only in `session-reflect.js` at SessionEnd which can be skipped on hard exits | Adopt as 5-line addition to `hooks.json` |
| `SubagentStop` | MED — `@setup-interviewer` and `@research-partner` write `_meta/` artifacts; hook can verify the write happened and surface failures | Worth it once `bin/` is added (see below) |
| `PostToolUse` (Write/Edit on vault paths) | LOW — would duplicate what `safe_path` and `setup-state` CLI already enforce; redundant boundary | Skip — over-engineering for second-pair-of-eyes |
| `Setup` (init/maintenance) | MED — fires on `claude --init-only`; could trigger `carrel env validate`. Niche but cheap | Optional |
| `Notification`, `TaskCreated`, `CwdChanged`, `InstructionsLoaded` | LOW | Skip |

### Plugin components not used

- **`bin/`** (MED) — drops `carrel` onto the Bash tool's PATH while the plugin is enabled. Today every command needs `uv run carrel ...` and assumes the user has `uv` + did `uv tool install`. Shipping a thin `bin/carrel` shim (or symlink to the installed binary) removes a class of "command not found" failures and makes the plugin self-contained on first install. Caveat: the Python core still needs to be installed; `bin/` only solves PATH, not packaging. Worth it if paired with an install-check in `check-environment.js`.

- **`output-styles/`** (LOW-MED) — A "research-mode" style (longer-form, citation-aware, no software-engineering scaffolding) would matter IF researchers were running carrel in non-coding sessions. They are. The `keep-coding-instructions: false` + `force-for-plugin: true` combo would auto-apply when the plugin is enabled. But: collides with users' own preferred styles, and CC's existing `Default`/`Explanatory` styles are workable. Ship as opt-in (no `force-for-plugin`), or skip until a researcher complains.

- **`monitors/monitors.json`** (LOW) — watches a file/log and pipes stdout lines to Claude as notifications. Possible use: watch `_meta/briefs/` for new automation outputs. But automation already writes through CLI commands carrel controls — no external signal to surveil. Skip.

- **`settings.json` defaults** (LOW) — only `agent` and `subagentStatusLine` are honored. Setting `agent: "research-partner"` would force every carrel session into the research-partner system prompt, which is too aggressive (collides with coding work in the same vault). Skip.

- **`channels`** (N/A) — requires a bundled MCP. Carrel bundles zero. Skip.

- **`userConfig`** (LOW) — declarative prompts at enable-time. Carrel's interview-first onboarding is its whole identity; replacing it with a static form would gut the product. Skip.

- **`.lsp.json`** (N/A) — Skip.

- **`dependencies`** (N/A — would point to other plugins. Carrel is the one-plugin policy) — Skip.

### MCP bundling

Carrel deliberately bundles zero MCPs (one-plugin policy, `revise` is bundled inside `scholarly` because it's plumbing). No change. The `model-teammates` skill correctly delegates to community plugins (`openai/codex-plugin-cc` etc.) rather than vendoring — keep this stance.

### Skill best-practices

Looked at `skills/convert/SKILL.md` and `skills/environment-setup/SKILL.md`:

- **Description triggers** are good — both lead with "This skill should be used when..." matching CC's recommended pattern.
- **`references/` directory pattern** is used by `environment-setup` and `self-improve` (good). Missing from `convert`, `transcribe`, `web-capture` — these are short enough to not need it, but if a `references/sensitivity-routing.md` were extracted from `convert/SKILL.md`'s inline rules, the SKILL.md would shrink.
- **`scripts/`** subdirectory is allowed but unused. Carrel deliberately routes scripts through the `carrel` CLI rather than per-skill scripts. Correct call — don't change.
- **`disable-model-invocation`** frontmatter — none of carrel's skills should be invocation-disabled. They're all model-invoked. Skip.

### Recent CC additions (last ~6 months) carrel could adopt

- **`experimental.monitors`** inline in plugin.json (v2.1.105+) — see above, skip.
- **`Setup` hook** — covered above, optional.
- **`StopFailure`, `PostToolUseFailure`, `PermissionDenied`** matchers — observational; could log to a `.carrel/cc-events.log` for the friction-log/capability-log skills to mine. LOW unless self-improve grows a "what tools failed this week" report.
- **`TeammateIdle`** — only relevant if carrel becomes an Agent Teams orchestrator, which is `agent-teams` skill territory, not carrel's.
- **`.zip` and `--plugin-url` distribution** (v2.1.128+) — irrelevant for marketplace-installed plugins.

---

## Recommendation for v0.9.0 scope

Adopt #1, #2, #3 from the top list. Add `bin/carrel` shim if Python packaging story holds. Defer output styles, `PreCompact`, and `SubagentStop` to v0.9.1 unless they fall out of the work naturally. Everything else: skip with prejudice.

Total estimated effort for the top 3: half a day. Marketplace metadata alone is 10 minutes and ships discoverability you can't buy back.
