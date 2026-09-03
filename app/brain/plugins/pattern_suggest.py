# app/brain/plugins/pattern_suggest.py - PATTERN_SUGGEST Intent Plugin
# Handles: "patrones", "qué patrones", "patrones detectados", "sugerencias patrones",
#          "patrones recurrentes", "tendencias"
# Intent: PATTERN_SUGGEST
# Priority: 5
# Entity group: pattern_query

import re

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, PHRASE, KEYWORD, PATTERN_SUGGEST


# PATTERN_SUGGEST intent patterns - priority 5 per design.md
# NOTE: Patterns must match normalized text (no accents, no colons)
_pattern_suggest_patterns = [
    # "patrones" - patterns (standalone)
    Pattern(
        PHRASE,
        "patrones",
        85,
        entity_group="pattern_query",
        boosts={"patrones": 10},
    ),
    # "que patrones" - what patterns
    Pattern(
        PHRASE,
        "que patrones",
        90,
        entity_group="pattern_query",
        boosts={"patrones": 10, "que": 5},
    ),
    # "patrones detectados" - detected patterns
    Pattern(
        PHRASE,
        "patrones detectados",
        92,
        entity_group="pattern_query",
        boosts={"patrones": 10, "detectados": 5},
    ),
    # "sugerencias patrones" - pattern suggestions
    Pattern(
        PHRASE,
        "sugerencias patrones",
        90,
        entity_group="pattern_query",
        boosts={"patrones": 10, "sugerencias": 5},
    ),
    # "patrones recurrentes" - recurring patterns
    Pattern(
        PHRASE,
        "patrones recurrentes",
        95,
        entity_group="pattern_query",
        boosts={"patrones": 10, "recurrentes": 5},
    ),
    # "tendencias" - trends
    Pattern(
        PHRASE,
        "tendencias",
        88,
        entity_group="pattern_query",
        boosts={"tendencias": 10},
    ),
    # "que tendencias" - what trends
    Pattern(
        PHRASE,
        "que tendencias",
        85,
        entity_group="pattern_query",
        boosts={"tendencias": 10, "que": 5},
    ),
    # "patrones de" - patterns of
    Pattern(
        PHRASE,
        "patrones de",
        80,
        entity_group="pattern_query",
        boosts={"patrones": 10, "de": 2},
    ),
    # "analisis de patrones" - pattern analysis
    Pattern(
        PHRASE,
        "analisis de patrones",
        93,
        entity_group="pattern_query",
        boosts={"analisis": 5, "patrones": 10},
    ),
    # "patrones en mis" - patterns in my
    Pattern(
        PHRASE,
        "patrones en mis",
        85,
        entity_group="pattern_query",
        boosts={"patrones": 10, "mis": 5},
    ),
]

# Plugin instance - priority 5 per design.md
pattern_suggest_plugin = IntentPlugin(
    name=PATTERN_SUGGEST,
    category="PATTERNS",
    patterns=_pattern_suggest_patterns,
    priority=5,
    entity_group="pattern_query",
)

# Alias for registry access (mod.plugin)
plugin = pattern_suggest_plugin