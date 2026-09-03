# app/brain/plugins/reflection_create.py - REFLECTION_CREATE Intent Plugin
# Patterns: "reflexión:", "mi reflexión", "hoy reflexioné", "pensando en", "diario:"
# Intent: REFLECTION_CREATE
# Priority: 5
# Entity group: reflection_text
# Normalized patterns: "reflexion:", "mi reflexion", "hoy reflexione", "pensando en", "diario:"

import re
from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, EXACT, PHRASE, REGEX, KEYWORD, REFLECTION_CREATE

# REFLECTION_CREATE intent patterns - priority 5 per design.md
# Weights are set higher than LEARNING_CREATE effective weights to avoid conflicts
# after normalization (colons removed, accents stripped).
_reflection_create_patterns = [
    # "reflexión:" - reflection prefix (normalized: "reflexion:")
    # Weight 95: highest priority pattern; colon stripped by normalize_strict,
    # but standalone "reflexion" pattern also exists with weight 80
    Pattern(
        PHRASE,
        "reflexion:",
        95,
        entity_group="reflection_text",
    ),
    # "mi reflexión" - my reflection (normalized: "mi reflexion")
    Pattern(
        PHRASE,
        "mi reflexion",
        90,
        entity_group="reflection_text",
        boosts={"mi": 5, "reflexion": 5},
    ),
    # "hoy reflexioné" - I reflected today (normalized: "hoy reflexione")
    Pattern(
        PHRASE,
        "hoy reflexione",
        85,
        entity_group="reflection_text",
        boosts={"hoy": 5, "reflexione": 5},
    ),
    # "pensando en" - thinking about (normalized: "pensando en")
    Pattern(
        PHRASE,
        "pensando en",
        80,
        entity_group="reflection_text",
        boosts={"pensando": 5, "en": 5},
    ),
    # "diario:" - diary prefix (normalized: "diario:")
    # Weight 92: high priority; colon stripped by normalize_strict,
    # standalone "diario" handling via the lowercase match
    Pattern(
        PHRASE,
        "diario:",
        92,
        entity_group="reflection_text",
    ),
    # "reflexion" - reflection word standalone (normalized: "reflexion")
    # Weight 80: higher than LEARNING_CREATE "aprendi" effective weight (75)
    # to avoid classification conflicts after normalization
    Pattern(
        PHRASE,
        "reflexion",
        80,
        entity_group="reflection_text",
        boosts={"reflexion": 5},
    ),
    # "diario" - diary word standalone (normalized: "diario")
    Pattern(
        PHRASE,
        "diario",
        78,
        entity_group="reflection_text",
        boosts={"diario": 5},
    ),
    # "aprendí que" - I learned that (normalized: "aprendi que")
    # Lower weight to avoid overtaking reflection patterns
    Pattern(
        PHRASE,
        "aprendi que",
        72,
        entity_group="reflection_text",
        boosts={"aprendi": 5, "que": 2},
    ),
]

# Plugin instance - priority 5 per design.md
reflection_create_plugin = IntentPlugin(
    name=REFLECTION_CREATE,
    category="REFLECTION",
    patterns=_reflection_create_patterns,
    priority=5,
    entity_group="reflection_text",
)

# Alias for registry access (mod.plugin)
plugin = reflection_create_plugin