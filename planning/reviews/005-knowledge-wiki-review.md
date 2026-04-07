# Knowledge Wiki Review — 2026-04-07

Two rounds of review across 4 reviewer types. All findings resolved or documented as known limitations.

## Round 1 Reviewers

### Skill Reviewer
- **Critical**: log.md read-mode conflict — query mode said "lightweight" but protocol required logging every query. **Fixed**: trivial queries exempt from logging; only filed queries log.
- **Major**: 10 vs 15 paper threshold inconsistency. **Fixed**: harmonized to 15 everywhere.
- **Major**: No storage for researcher wiki preference/deferral. **Fixed**: added `wiki_preference` and `wiki_proposal_deferred_until` to ResearcherProfile model.
- **Major**: No tracking for consultative → delegated upgrade. **Fixed**: uses log-based heuristic (check recent entries for corrections) instead of counter.
- **Minor**: Missing trigger phrases in description. **Fixed**: added "literature review", "systematic review", "I keep losing track".

### Code Reviewer
- **Important**: Automation SKILL.md JSON example omitted wiki_maintenance. **Fixed**.
- **Important**: Test coverage gap for new fields. **Fixed**: added assertions to 3 test functions.

### Plugin Validator
- **Warning**: Version 0.4.0 vs CLAUDE.md "v0.5" label. **Fixed**: removed version label, defer bump to release.
- **Warning**: /carrel-automate command missing wiki_maintenance. **Fixed**: added to interview + JSON.
- **Warning**: Session-start hook missing wiki parsing. **Fixed**: added Field Map regex.
- **Warning**: capability-registry.md missing entry. **Fixed**: added absorbed capability + upstream watch.
- **Warning**: research-partner unaware of wiki/. **Fixed**: both skill and agent updated.

### Codex Adversarial (Round 1)
- **Critical**: inbox/ not scanned by overnight wiki maintenance. **Fixed**: added inbox/ to all scan lists.
- **Critical**: No per-action revert trail at delegated trust. **Partially fixed**: brief includes per-file actions; existing-page edits rely on git history (documented).
- **Design**: Trust gating is prompt text, not code. **Accepted**: consistent with all carrel skills.
- **Design**: log.md overloaded. **Accepted for v1**: sufficient at <100 pages, structured state can come later.
- **Overengineered**: Too much ceremony. **Noted**: thresholds are starting points, ceremony is optional.

## Round 2 Reviewers

### Internal Code Reviewer
- **Critical**: Wiki fallback unreachable inside checkAutomation() (early return on no briefs/). **Fixed**: moved to main().
- **Important**: hasBrief used weaker filter than brief parser. **Fixed**: strict date regex.
- **Important**: Shadowed briefsDir variable. **Fixed**: resolved by moving block.

### Codex Adversarial (Round 2)
- **High**: Contradictory filing instructions (SKILL.md vs wiki-protocol.md). **Fixed**: added trust gate to protocol.
- **High**: Advisory + wiki_enabled inconsistency. **Fixed**: added invariant — activation implies consultative.
- **High**: wiki_preference not operationalized. **Fixed**: added explicit check-before-proposing instructions with note that this is skill-read, not code-enforced.
- **High**: Incomplete revert for existing-page edits. **Fixed**: honest documentation — git history for edits, rm for new pages.
- **Medium**: Hook fallback incomplete (page count only). **Accepted**: reading wiki files too heavy for a hook.
- **Medium**: Callout system lacks authorship guards. **Accepted for v1**: only researcher edits in Obsidian.

## Ergonomics Analysis

Separate from code review, examined the AI-researcher interaction ergonomics. Found that all touchpoints were one-directional (agent → researcher). Added dialogue surface:

1. **Researcher callouts** (`> [!researcher]`): persistent annotations on wiki pages that the agent reads and respects. The researcher's voice talking to the agent's future self.
2. **Wiki insights in briefs**: one sentence of synthesis, not just counts. The agent's synthetic voice.
3. **"Field voice / my voice" framing**: wiki = what sources say, notes = what researcher thinks, gap = contribution. Explicit in proposal and vault CLAUDE.md.
4. **Citation transparency**: always cite wiki source when answering from it. Researcher can trace and verify.

## Known Limitations (documented, not bugs)

- Trust gating is prompt-based, not code-enforced (consistent with carrel design)
- log.md serves as precedent store, handoff, and watermark (sufficient at v1 scale)
- Contradiction detection is LLM judgment, not computable rules
- Hook wiki fallback shows page count only (reading wiki files too heavy)
- Callout system has no formal authorship verification (Obsidian UI is the natural boundary)
- Existing-page edit reverts rely on git history / session checkpoints
- wiki_preference fields are read by Claude, not enforced by hooks

## Commits

| Commit | Description |
|--------|-------------|
| `aa804dc` | Knowledge wiki feature: 3 new skill files + full integration across 12 files |
| `c51a40f` | Round 1 fixes + dialogue surface (callouts, insights, framing, transparency) |
| `baf476f` | Round 2 fixes (hook placement, trust invariants, filing consistency, revert story) |
