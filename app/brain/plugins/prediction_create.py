# app/brain/plugins/prediction_create.py - PREDICTION_CREATE Intent Plugin
# Patterns: "predigo que", "mi predicción es", "creo que pasará", "en el futuro", "pronostico"
# Intent: PREDICTION_CREATE
# Priority: 5
# Entity group: prediction_text

import re
from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, EXACT, PHRASE, REGEX, PREDICTION_CREATE

# PREDICTION_CREATE intent patterns - priority 5 per design.mod
# NOTE: Patterns must match normalized text (no accents, no colons)
_prediction_create_patterns = [
    # "predigo que..." - I predict that... (normalized: "predigo que")
    Pattern(
        PHRASE,
        "predigo que",
        90,
        entity_group="prediction_text",
        boosts={"predigo": 10, "predic": 5},
    ),
    # "mi predicción es..." - my prediction is... (normalized: "mi prediccion es")
    Pattern(
        PHRASE,
        "mi prediccion es",
        95,
        entity_group="prediction_text",
        boosts={"predic": 10},
    ),
    # "creo que pasará" - I think it will happen (normalized: "creo que pasara")
    Pattern(
        PHRASE,
        "creo que pasara",
        85,
        entity_group="prediction_text",
        boosts={"creo": 5, "pasara": 5},
    ),
    # "en el futuro" - in the future (normalized: "en el futuro")
    Pattern(
        PHRASE,
        "en el futuro",
        70,
        entity_group="prediction_text",
    ),
    # "pronostico" - I forecast (normalized: "pronostico")
    Pattern(
        PHRASE,
        "pronostico",
        80,
        entity_group="prediction_text",
        boosts={"pronost": 5},
    ),
    # "pronostico que" - I forecast that (normalized: "pronostico que")
    Pattern(
        PHRASE,
        "pronostico que",
        85,
        entity_group="prediction_text",
        boosts={"pronost": 5, "predic": 5},
    ),
    # "prediction" - English pattern (normalized: "prediction")
    Pattern(
        EXACT,
        "prediction",
        75,
        entity_group="prediction_text",
        word_boundary=True,
    ),
]

# Plugin instance - priority 5 per design.md
prediction_create_plugin = IntentPlugin(
    name=PREDICTION_CREATE,
    category="PREDICTION",
    patterns=_prediction_create_patterns,
    priority=5,
    entity_group="prediction_text",
)

# Alias for registry access (mod.plugin)
plugin = prediction_create_plugin