# app/brain/plugins/identity_propose.py - IDENTITY_PROPOSE Intent Plugin
# Handles: "propongo cambiar identidad", "cambiar mi identidad",
#          "propuesta identidad", "modificar valores", "actualizar principios"
#
# Intent: IDENTITY_PROPOSE
# Priority: 5
# Entity group: identity_changes
# Normalized patterns: "propongo cambiar identidad", "cambiar mi identidad",
#                     "propuesta identidad", "modificar valores", "actualizar principios"

import re

from brain.intent_types import Pattern, EXACT, PHRASE, REGEX, CONFIDENCE_PROBABLE, CONFIDENCE_AMBIGUO
from brain.plugins.base import IntentPlugin


# ── Normalized patterns (phrase type for entity extraction) ──

_PROPOSE_PATTERNS = [
    # "propongo cambiar identidad"
    Pattern(
        type=PHRASE,
        value="propongo cambiar identidad",
        weight=80,
        entity_group="identity_changes",
    ),
    # "cambiar mi identidad"
    Pattern(
        type=PHRASE,
        value="cambiar mi identidad",
        weight=75,
        entity_group="identity_changes",
    ),
    # "propuesta identidad"
    Pattern(
        type=PHRASE,
        value="propuesta identidad",
        weight=70,
        entity_group="identity_changes",
    ),
    # "modificar valores" — with boost for "valores" context
    Pattern(
        type=PHRASE,
        value="modificar valores",
        weight=60,
        entity_group="identity_changes",
        boosts={"valores": 20, "principios": 10},
    ),
    # "actualizar principios" — with boost for "principios" context
    Pattern(
        type=PHRASE,
        value="actualizar principios",
        weight=60,
        entity_group="identity_changes",
        boosts={"principios": 20, "valores": 10},
    ),
]


# ── Plugin instance ────────────────────────────────────────────────

def _make_plugin() -> IntentPlugin:
    """Create the IDENTITY_PROPOSE plugin instance."""
    return IntentPlugin(
        name="IDENTITY_PROPOSE",
        category="IDENTITY",
        patterns=_PROPOSE_PATTERNS,
        entity_group="identity_changes",
        priority=5,
    )


# Module-level PLUGIN for auto-discovery
PLUGIN = _make_plugin()

# Lowercase alias for backward compatibility with tests
plugin = PLUGIN