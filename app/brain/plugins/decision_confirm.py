# app/brain/plugins/decision_confirm.py - DECISION_CONFIRM Intent Plugin
# Patterns: "confirmo decisión", "decisión confirmada", "resultado decisión", "apruebo decisión"
# Intent: DECISION_CONFIRM
# Priority: 5
# Entity group: decision_id

import re
from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, EXACT, PHRASE, REGEX, DECISION_CONFIRM

# DECISION_CONFIRM intent patterns - priority 5 per design.mod
# NOTE: Patterns must match normalized text (no accents, no colons)
decision_confirm_patterns = [
    # "confirmo decision" - I confirm the decision (normalized: "confirmo decision")
    Pattern(
        PHRASE,
        "confirmo decision",
        95,
        entity_group="decision_id",
        boosts={"confirmo": 10, "decision": 10},
    ),
    # "decision confirmada" - decision confirmed (normalized: "decision confirmada")
    Pattern(
        PHRASE,
        "decision confirmada",
        90,
        entity_group="decision_id",
    ),
    # "resultado decision" - decision result (normalized: "resultado decision")
    Pattern(
        PHRASE,
        "resultado decision",
        85,
        entity_group="decision_id",
    ),
    # "apruebo decision" - I approve the decision (normalized: "apruebo decision")
    Pattern(
        PHRASE,
        "apruebo decision",
        90,
        entity_group="decision_id",
        boosts={"apruebo": 10, "decision": 10},
    ),
    # "estoy de acuerdo" - I agree
    Pattern(
        PHRASE,
        "estoy de acuerdo",
        75,
        entity_group="decision_id",
    ),
    # "me parece bien" - seems fine to me
    Pattern(
        PHRASE,
        "me parece bien",
        70,
        entity_group="decision_id",
    ),
    # "esta bien" - it's okay (normalized: "esta bien")
    Pattern(
        PHRASE,
        "esta bien",
        65,
        entity_group="decision_id",
    ),
    # "confirmo" - just confirm (standalone)
    Pattern(
        EXACT,
        "confirmo",
        80,
        entity_group="decision_id",
        word_boundary=True,
    ),
]

# Plugin instance - priority 5 per design.md
decision_confirm_plugin = IntentPlugin(
    name=DECISION_CONFIRM,
    category="DECISION",
    patterns=decision_confirm_patterns,
    priority=5,
    entity_group="decision_id",
)

# Alias for registry access (mod.plugin)
plugin = decision_confirm_plugin