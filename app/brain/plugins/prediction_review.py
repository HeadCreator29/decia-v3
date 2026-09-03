# app/brain/plugins/prediction_review.py - PREDICTION_REVIEW Intent Plugin
# Patterns: "revisar predicción", "predicción revisión", "cómo fue mi predicción", "estado predicción"
# Intent: PREDICTION_REVIEW
# Priority: 5
# Entity group: prediction_id

import re
from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, EXACT, PHRASE, REGEX, PREDICTION_REVIEW

# PREDICTION_REVIEW intent patterns - priority 5 per design.mod
# NOTE: Patterns must match normalized text (no accents, no colons)
prediction_review_patterns = [
    # "revisar predicción" - review the prediction (normalized: "revisar prediccion")
    Pattern(
        PHRASE,
        "revisar prediccion",
        95,
        entity_group="prediction_id",
        boosts={"revisar": 10, "predic": 5},
    ),
    # "predicción revisión" - prediction review (normalized: "prediccion revision")
    Pattern(
        PHRASE,
        "prediccion revision",
        90,
        entity_group="prediction_id",
        boosts={"predic": 10, "revision": 5},
    ),
    # "cómo fue mi predicción" - how was my prediction (normalized: "como fue mi prediccion")
    Pattern(
        PHRASE,
        "como fue mi prediccion",
        92,
        entity_group="prediction_id",
    ),
    # "estado predicción" - prediction status (normalized: "estado prediccion")
    Pattern(
        PHRASE,
        "estado prediccion",
        93,
        entity_group="prediction_id",
    ),
    # "predicción" alone (standalone) (normalized: "prediccion")
    Pattern(
        EXACT,
        "prediccion",
        80,
        entity_group="prediction_id",
        word_boundary=True,
    ),
    # "predicción completa" - full prediction (normalized: "prediccion completa")
    Pattern(
        PHRASE,
        "prediccion completa",
        75,
        entity_group="prediction_id",
    ),
    # "ver predicción" - view prediction (normalized: "ver prediccion")
    Pattern(
        PHRASE,
        "ver prediccion",
        85,
        entity_group="prediction_id",
    ),
]

# Plugin instance - priority 5 per design.md
prediction_review_plugin = IntentPlugin(
    name=PREDICTION_REVIEW,
    category="PREDICTION",
    patterns=prediction_review_patterns,
    priority=5,
    entity_group="prediction_id",
)

# Alias for registry access (mod.plugin)
plugin = prediction_review_plugin