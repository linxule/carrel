from __future__ import annotations

VERSION = "0.1.0-skill"

SENSITIVITY = {"high", "medium", "low"}
TRUST_LEVELS = {"advisory", "consultative", "delegated", "partnership"}
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
    "transcribe": {"coli", "youtube_captions", "provided"},
}
CLOUD_TOOLS = {
    "convert": {"mineru"},
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
    "version": VERSION,
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

ADAPTER_PROFILE_KEYS: set[str] = set()
