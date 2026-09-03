# app/brain/plugins/learning_create.py - LEARNING_CREATE Intent Plugin
# Patterns: "aprendí que", "la lección es", "qué aprendí", "aprendizaje:", "lección aprendida"
# Intent: LEARNING_CREATE
# Priority: 5
# Entity group: lesson_text

import re
from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, EXACT, PHRASE, REGEX, KEYWORD, LEARNING_CREATE

# LEARNING_CREATE intent patterns - priority 5 per design.md
_learning_create_patterns = [
    # "aprendí que..." - I learned that... (normalized: "aprendi que")
    Pattern(
        PHRASE,
        "aprendi que",
        90,
        entity_group="lesson_text",
        boosts={"aprendi": 10, "que": 5},
    ),
    # "la lección es" - the lesson is (normalized: "la leccion es")
    Pattern(
        PHRASE,
        "la leccion es",
        85,
        entity_group="lesson_text",
        boosts={"leccion": 10, "es": 5},
    ),
    # "que aprendi" - that I learned (normalized: "que aprendi")
    Pattern(
        PHRASE,
        "que aprendi",
        80,
        entity_group="lesson_text",
        boosts={"aprendi": 10},
    ),
    # "aprendizaje:" - learning prefix (normalized: "aprendizaje:")
    Pattern(
        PHRASE,
        "aprendizaje:",
        95,
        entity_group="lesson_text",
    ),
    # "lección aprendida" - learned lesson (normalized: "leccion aprendida")
    Pattern(
        PHRASE,
        "leccion aprendida",
        88,
        entity_group="lesson_text",
        boosts={"leccion": 10, "aprendida": 5},
    ),
    # "aprendi" - I learned (standalone, lower weight)
    Pattern(
        PHRASE,
        "aprendi",
        70,
        entity_group="lesson_text",
        boosts={"aprendi": 5},
    ),
]

# Plugin instance - priority 5 per design.md
learning_create_plugin = IntentPlugin(
    name=LEARNING_CREATE,
    category="LEARNING",
    patterns=_learning_create_patterns,
    priority=5,
    entity_group="lesson_text",
)

# Alias for registry access (mod.plugin)
plugin = learning_create_plugin