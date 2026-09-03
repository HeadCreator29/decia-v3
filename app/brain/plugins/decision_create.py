# app/brain/plugins/decision_create.py - DECISION_CREATE Intent Plugin
# Patterns: "decido que", "mi decisión es", "he decidido", "decidimos", "resolución:"
# Intent: DECISION_CREATE
# Priority: 5
# Entity group: decision_problem

import re
from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, EXACT, PHRASE, REGEX, CALCULATE, DECISION_CREATE

# DECISION_CREATE intent patterns - priority 5 per design.mod
# NOTE: Patterns must match normalized text (no accents, no colons)
_decision_create_patterns = [
    # "decido que..." - decision statement
    Pattern(
        PHRASE,
        "decido que",
        80,
        entity_group="decision_problem",
        boosts={"decido": 10},
    ),
    # "mi decision es..." - my decision is... (normalized: "mi decision es")
    Pattern(
        PHRASE,
        "mi decision es",
        90,
        entity_group="decision_problem",
        boosts={"decision": 10},
    ),
    # "he decidido" - I have decided
    Pattern(
        PHRASE,
        "he decidido",
        85,
        entity_group="decision_problem",
        boosts={"decidi": 5, "decida": 5},
    ),
    # "decidimos" - we decided (plural)
    Pattern(
        PHRASE,
        "decidimos",
        80,
        entity_group="decision_problem",
    ),
    # "resolucion" - resolution prefix (normalized: "resolucion")
    Pattern(
        PHRASE,
        "resolucion",
        95,
        entity_group="decision_problem",
    ),
    # "elijo" - I choose
    Pattern(
        PHRASE,
        "elijo",
        75,
        entity_group="decision_problem",
    ),
    # "opte por" - I opted for (normalized: "opte por")
    Pattern(
        PHRASE,
        "opte por",
        70,
        entity_group="decision_problem",
    ),
    # "decidire" - I will decide (future) (normalized: "decidire")
    Pattern(
        PHRASE,
        "decidire",
        65,
        entity_group="decision_problem",
    ),
]

# Plugin instance - priority 5 per design.md
decision_create_plugin = IntentPlugin(
    name=DECISION_CREATE,
    category="DECISION",
    patterns=_decision_create_patterns,
    priority=5,
    entity_group="decision_problem",
)

# Alias for registry access (mod.plugin)
plugin = decision_create_plugin