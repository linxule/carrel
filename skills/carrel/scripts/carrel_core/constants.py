from __future__ import annotations

# The portable skill pack's own version. Deliberately NOT written into
# environment.json's shared "version" field (that field belongs to the full
# Claude Code plugin's semver and is drift-checked there) — surfaced only via
# `env doctor` diagnostics as "skill_pack_version", so the two version
# concepts never collide on a vault touched by both engines.
VERSION = "0.1.0-skill"

SENSITIVITY = {"high", "medium", "low"}
TRUST_LEVELS = {"advisory", "consultative", "delegated", "partnership"}
AUTOMATION_MODELS = {"sonnet", "opus"}
AUTOMATION_SCHEDULES = {"daily", "weekdays", "weekly"}
AUTOMATION_REVIEW_CADENCES = {"monthly", "quarterly", "biannual"}
TRUST_HIERARCHY = ["advisory", "consultative", "delegated", "partnership"]
TRUST_ACTIONS = {
    "automation:propose": "consultative",
    "automation:execute": "delegated",
    "automation:write-prompt": "delegated",
    "wiki:propose": "consultative",
    "wiki:write": "delegated",
    "vault:move-file": "delegated",
    "vault:reorganize": "partnership",
}

LOCAL_TOOLS = {
    "convert": {"liteparse", "markdownify", "provided"},
    "transcribe": {"coli", "provided"},
}
CLOUD_TOOLS = {
    "convert": {"mineru", "mistral_ocr"},
    "transcribe": {"groq", "gemini"},
}

GOOGLE_WORKSPACE_EXPORTS: dict[str, dict[str, tuple[str, str]]] = {
    "document": {
        "docx": (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".docx",
        ),
        "pdf": ("application/pdf", ".pdf"),
        "txt": ("text/plain", ".txt"),
        "html": ("text/html", ".html"),
    },
    "spreadsheets": {
        "docx": (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xlsx",
        ),
        "pdf": ("application/pdf", ".pdf"),
        "txt": ("text/csv", ".csv"),
        "html": ("text/html", ".html"),
    },
    "presentation": {
        "docx": (
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".pptx",
        ),
        "pdf": ("application/pdf", ".pdf"),
        "txt": ("text/plain", ".txt"),
    },
}

DOC_EXTENSIONS = {".pdf", ".docx", ".doc", ".pptx", ".xlsx", ".txt", ".md"}
AUDIO_EXTENSIONS = {".m4a", ".mp3", ".wav", ".mp4", ".webm", ".mov", ".ogg", ".flac"}
URL_LIST_EXTENSION = ".txt"

DEFAULT_PROFILE = {
    "name": None,
    "field": None,
    "sensitivity": "medium",
    "cloud_consent": False,
    "comfort_level": "beginner",
    "wiki_enabled": False,
    "wiki_preference": None,
    "wiki_proposal_deferred_until": None,
    "tools_configured": {},
    "preferences": {},
    "claude_code_familiarity": None,
    "automation": {
        "enabled": False,
        "inbox_processing": True,
        "vault_health": True,
        "cross_linking_suggestions": True,
        "gap_analysis": False,
        "draft_feedback": False,
        "reflection_synthesis": True,
        "wiki_maintenance": False,
        "trust_level": "advisory",
        "model": "sonnet",
        "schedule": "daily",
        "review_cadence": "quarterly",
        "last_reviewed": None,
    },
    "collaborators": None,
    "team_context": None,
    "model_teammates": {},
    "_unknown_keys": {},
}

# Keys owned by another engine's schema (full Claude Code plugin's ResearcherProfile)
# that the portable runtime must tolerate without treating as unknown drift and
# without overwriting: it never writes them itself, but a vault previously
# scaffolded by the full plugin may already have them. `version` in particular
# tracks the full plugin's semver — deliberately NOT tracked in DEFAULT_PROFILE
# (see VERSION/skill_pack_version below) so the portable runtime never writes a
# value that could look like a plugin version mismatch to the full plugin's own
# drift/migration detection.
ADAPTER_PROFILE_KEYS: set[str] = {"version"}
