# app/brain/plugins/identity_approve.py - IDENTITY_APPROVE Intent Plugin
# Handles: "aprobar identidad", "confirmar cambios identidad",
#          "aceptar propuesta identidad", "ceremonia identidad"
#
# Intent: IDENTITY_APPROVE
# Priority: 5
# Entity group: proposal_id
# Normalized patterns: "aprobar identidad", "confirmar cambios identidad",
#                     "aceptar propuesta identidad", "ceremonia identidad"

import re

from brain.intent_types import Pattern, EXACT, PHRASE, REGEX, CONFIDENCE_SEGURO, CONFIDENCE_PROBABLE
from brain.plugins.base import IntentPlugin


# ── Normalized patterns (phrase type for entity extraction) ──

_APPROVE_PATTERNS = [
    # "aprobar identidad" - approve identity
    Pattern(
        type=PHRASE,
        value="aprobar identidad",
        weight=85,
        entity_group="proposal_id",
        boosts={"aprobar": 10, "identidad": 5},
    ),
    # "confirmar cambios identidad" - confirm identity changes
    Pattern(
        type=PHRASE,
        value="confirmar cambios identidad",
        weight=78,
        entity_group="proposal_id",
        boosts={"confirmar": 10, "cambios": 5, "identidad": 5},
    ),
    # "aceptar propuesta identidad" - accept identity proposal
    Pattern(
        type=PHRASE,
        value="aceptar propuesta identidad",
        weight=75,
        entity_group="proposal_id",
        boosts={"aceptar": 10, "propuesta": 10, "identidad": 5},
    ),
    # "ceremonia identidad" - identity ceremony
    Pattern(
        type=PHRASE,
        value="ceremonia identidad",
        weight=80,
        entity_group="proposal_id",
        boosts={"ceremonia": 10, "identidad": 5},
    ),
]


# ── Plugin instance ────────────────────────────────────────────────

def _make_plugin() -> IntentPlugin:
    """Create the IDENTITY_APPROVE plugin instance."""
    return IntentPlugin(
        name="IDENTITY_APPROVE",
        category="IDENTITY",
        patterns=_APPROVE_PATTERNS,
        entity_group="proposal_id",
        priority=5,
    )


# Module-level PLUGIN for auto-discovery
PLUGIN = _make_plugin()

# Lowercase alias for backward compatibility with tests
plugin = PLUGIN