from __future__ import annotations

import pytest

from carrel.errors import CarrelError
from carrel.models import TrustLevel
from carrel.trust import ACTIONS, TRUST_HIERARCHY, is_allowed, list_actions, required_trust


@pytest.mark.parametrize("action,required", ACTIONS.items())
@pytest.mark.parametrize("trust_level", TRUST_HIERARCHY)
def test_is_allowed_matrix(action: str, required: TrustLevel, trust_level: TrustLevel) -> None:
    assert is_allowed(action, trust_level) is (
        TRUST_HIERARCHY.index(trust_level) >= TRUST_HIERARCHY.index(required)
    )


def test_required_trust_rejects_unknown_action() -> None:
    with pytest.raises(CarrelError) as exc:
        required_trust("wiki:delete")

    assert exc.value.message == "Unknown trust action: wiki:delete"
    assert exc.value.hint == f"Valid actions: {', '.join(ACTIONS)}"


def test_trust_hierarchy_is_ordered() -> None:
    assert TRUST_HIERARCHY.index(TrustLevel.ADVISORY) < TRUST_HIERARCHY.index(TrustLevel.CONSULTATIVE)
    assert TRUST_HIERARCHY.index(TrustLevel.CONSULTATIVE) < TRUST_HIERARCHY.index(TrustLevel.DELEGATED)
    assert TRUST_HIERARCHY.index(TrustLevel.DELEGATED) < TRUST_HIERARCHY.index(TrustLevel.PARTNERSHIP)


def test_list_actions_for_delegated_trust() -> None:
    result = list_actions(TrustLevel.DELEGATED)

    assert result == {
        "automation:propose": (TrustLevel.CONSULTATIVE, True),
        "automation:execute": (TrustLevel.DELEGATED, True),
        "automation:write-prompt": (TrustLevel.DELEGATED, True),
        "wiki:propose": (TrustLevel.CONSULTATIVE, True),
        "wiki:write": (TrustLevel.DELEGATED, True),
        "vault:move-file": (TrustLevel.DELEGATED, True),
        "vault:reorganize": (TrustLevel.PARTNERSHIP, False),
    }
