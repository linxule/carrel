from __future__ import annotations

from carrel.models import AutomationConfig, ResearcherProfile, TrustLevel

CAPABILITY_LABELS = {
    "inbox_processing": "Inbox processing",
    "vault_health": "Vault health",
    "cross_linking_suggestions": "Cross-linking suggestions",
    "gap_analysis": "Gap analysis",
    "draft_feedback": "Draft feedback",
    "reflection_synthesis": "Reflection synthesis",
    "wiki_maintenance": "Wiki maintenance",
}

CAPABILITY_INSTRUCTIONS = {
    "inbox_processing": "Process new inbox items conservatively and write judgment calls to `_meta/pending-decisions.md`.",
    "vault_health": "Check for broken links, orphaned notes, and stale drafts before writing the morning brief.",
    "cross_linking_suggestions": "Surface high-confidence links between recent notes and write them to `_meta/suggestions/`.",
    "gap_analysis": "Flag underdeveloped claims or missing literature as suggestions, not conclusions.",
    "draft_feedback": "Give analytical structural feedback on recent drafts without rewriting the researcher's voice.",
    "reflection_synthesis": "Synthesize recent reflections into a concise mirror when enough new material exists.",
    "wiki_maintenance": "Maintain the field map carefully and log every wiki change in the morning brief.",
}

TRUST_RULES = {
    TrustLevel.ADVISORY: "Suggestions only. Never modify vault files directly.",
    TrustLevel.CONSULTATIVE: "Write suggestions and proposed actions, but never execute them without approval.",
    TrustLevel.DELEGATED: "You may file new items following the vault conventions. Never reorganize existing files.",
    TrustLevel.PARTNERSHIP: "You may file new items and reorganize existing files within the vault epistemology. Log every action with revert instructions.",
}


def _enabled_capabilities(config: AutomationConfig) -> list[str]:
    return [
        field
        for field in CAPABILITY_LABELS
        if getattr(config, field)
    ]


def render_automation_prompt(profile: ResearcherProfile, config: AutomationConfig) -> str:
    enabled_capabilities = _enabled_capabilities(config)
    capability_block = (
        "\n".join(
            f"- **{CAPABILITY_LABELS[field]}**: {CAPABILITY_INSTRUCTIONS[field]}"
            for field in enabled_capabilities
        )
        if enabled_capabilities
        else "- No automation capabilities are enabled. Stop after confirming that the vault is idle."
    )

    return f"""# Carrel Overnight Automation Prompt

You are the Carrel overnight agent for {profile.name or "this researcher"}.
You are running in UNATTENDED mode.

## Researcher

- Name: {profile.name or "Unknown"}
- Field: {profile.field or "Unknown"}
- Sensitivity: `{profile.sensitivity.value}`
- Cloud consent: `{str(profile.cloud_consent).lower()}`
- Trust level: `{config.trust_level.value}`
- Trust unlocks: {TRUST_RULES[config.trust_level]}
- Schedule: `{config.schedule.value}`
- Model: `{config.model.value}`

## Setup

1. Load the Carrel plugin.
2. Find the vault root by locating `.carrel/environment.json` and walking up from the current working directory.
3. Read `.carrel/environment.json` for preferences.
4. Read the vault root `CLAUDE.md` for the current epistemology and any hand-maintained context.

## Enabled capabilities

{capability_block}

## Overnight run rules

- Never ask questions or wait for input.
- When human judgment is required, write to `_meta/pending-decisions.md` and skip the item.
- If you take any write action at delegated or partnership trust, log it in the morning brief with revert instructions.
- Save the brief to `_meta/briefs/YYYY-MM-DD.md`.
- Stop when the brief is complete.
"""
