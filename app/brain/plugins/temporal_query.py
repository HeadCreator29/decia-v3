# app/brain/plugins/temporal_query.py - TEMPORAL_QUERY Intent Plugin
# Handles: "historia 2024", "memorias enero", "qué pasó en marzo",
#          "eventos 2026", "cronología 2025", "timeline"
# Intent: TEMPORAL_QUERY
# Priority: 5
# Entity group: time_range

import re

from brain.intent_types import Pattern, PHRASE, REGEX, TEMPORAL_QUERY
from brain.plugins.base import IntentPlugin


# TEMPORAL_QUERY intent patterns - priority 5 per design.md
# NOTE: Patterns must match normalized text (no accents, no colons)
_temporal_query_patterns = [
    # "historia 2024" - history for a year (but NOT "cuentame la historia")
    Pattern(
        PHRASE,
        "historia",
        80,
        entity_group="time_range",
        boosts={"historia": 10, "2024": 5, "2025": 5, "2026": 5, "deca": -30, "cuentame": -90, "dime": -90, "hablame": -90},
    ),
    # "memorias enero" - memories for a month
    Pattern(
        PHRASE,
        "memorias",
        85,
        entity_group="time_range",
        boosts={"memorias": 10, "enero": 5, "febrero": 5, "marzo": 5, "deca": -30, "cuentame": -90, "dime": -90, "hablame": -90},
    ),
    # "que paso en" - what happened in
    Pattern(
        PHRASE,
        "que paso en",
        90,
        entity_group="time_range",
        boosts={"paso": 10, "deca": -30, "cuentame": -90, "dime": -90, "hablame": -90},
    ),
    # "eventos 2024" - events for a year
    Pattern(
        PHRASE,
        "eventos",
        85,
        entity_group="time_range",
        boosts={"eventos": 10, "2024": 5, "2025": 5, "2026": 5, "deca": -30, "cuentame": -90, "dime": -90, "hablame": -90},
    ),
    # "cronologia" - timeline/chronology
    Pattern(
        PHRASE,
        "cronologia",
        92,
        entity_group="time_range",
        boosts={"cronologia": 10, "timeline": 5},
    ),
    # "timeline" - English pattern
    Pattern(
        PHRASE,
        "timeline",
        85,
        entity_group="time_range",
        boosts={"timeline": 10},
    ),
    # "en 2024" - in 2024
    Pattern(
        PHRASE,
        "en 2024",
        95,
        entity_group="time_range",
    ),
    # "en 2025" - in 2025
    Pattern(
        PHRASE,
        "en 2025",
        95,
        entity_group="time_range",
    ),
    # "en 2026" - in 2026
    Pattern(
        PHRASE,
        "en 2026",
        95,
        entity_group="time_range",
    ),
]

# Plugin instance - priority 5 per design.md
temporal_query_plugin = IntentPlugin(
    name=TEMPORAL_QUERY,
    category="TEMPORAL",
    patterns=_temporal_query_patterns,
    priority=5,
    entity_group="time_range",
)

# Alias for registry access (mod.plugin)
plugin = temporal_query_plugin