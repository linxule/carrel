from __future__ import annotations

from carrel.errors import CarrelError
from carrel.models import TrustLevel

ACTIONS: dict[str, TrustLevel] = {
    "automation:propose": TrustLevel.CONSULTATIVE,
    "automation:execute": TrustLevel.DELEGATED,
    "automation:write-prompt": TrustLevel.DELEGATED,
    "wiki:propose": TrustLevel.CONSULTATIVE,
    "wiki:write": TrustLevel.DELEGATED,
    "vault:move-file": TrustLevel.DELEGATED,
    "vault:reorganize": TrustLevel.PARTNERSHIP,
}

TRUST_HIERARCHY = [
    TrustLevel.ADVISORY,
    TrustLevel.CONSULTATIVE,
    TrustLevel.DELEGATED,
    TrustLevel.PARTNERSHIP,
]


def required_trust(action: str) -> TrustLevel:
    try:
        return ACTIONS[action]
    except KeyError as error:
        valid_actions = ", ".join(ACTIONS)
        raise CarrelError(
            f"Unknown trust action: {action}",
            hint=f"Valid actions: {valid_actions}",
        ) from error


def is_allowed(action: str, trust_level: TrustLevel) -> bool:
    required = required_trust(action)
    return TRUST_HIERARCHY.index(trust_level) >= TRUST_HIERARCHY.index(required)


def list_actions(trust_level: TrustLevel) -> dict[str, tuple[TrustLevel, bool]]:
    return {
        action: (required, TRUST_HIERARCHY.index(trust_level) >= TRUST_HIERARCHY.index(required))
        for action, required in ACTIONS.items()
    }
