# test_memory_search.py - MEMORY_SEARCH plugin contract test
# Verifies MEMORY_SEARCH plugin classification matches golden master

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, KEYWORD, PHRASE, REGEX, MEMORY_SEARCH
from brain.plugins.registry import PluginRegistry


def test_memory_search_plugin_creation():
    """Verify MEMORY_SEARCH plugin can be created with patterns from _init_patterns()."""
    plugin = IntentPlugin(
        name="MEMORY_SEARCH",
        category="MEMORY",
        patterns=[
            Pattern(KEYWORD, "recuerdame", 70),
            Pattern(KEYWORD, "hoy", 30, {"recuerdas": 25, "hablado": 25}),
            Pattern(KEYWORD, "ayer", 30, {"recuerdas": 25}),
            Pattern(REGEX, r"me\s+gusta", 65, entity_group="memory"),
            Pattern(REGEX, r"quiero\s+terminar", 65, entity_group="memory"),
            Pattern(REGEX, r"como\s+se\s+llama\s+mi", 65, entity_group="memory"),
            Pattern(PHRASE, "que sabes de mi", 75),
            Pattern(PHRASE, "que recuerdas de mi", 75),
            Pattern(PHRASE, "que sabes sobre mi", 75),
            Pattern(REGEX, r"cual\s+es\s+mi\s+\w+", 70, entity_group="memory"),
            Pattern(REGEX, r"en\s+que\s+proyecto\s+(estoy|trabajo|trabajando)", 70, entity_group="memory"),
            Pattern(PHRASE, "que paso hoy", 75),
            Pattern(PHRASE, "que paso ayer", 75),
            Pattern(REGEX, r"^que\s+paso\b(?:$|\s+(?:con|sobre)\s+\S+)", 60),
            Pattern(REGEX, r"que\s+paso\s+(hoy|ayer|anteayer|\s+(?:semana|la\s+semana)\s+pasada)", 75),
            Pattern(REGEX, r"que\s+(hicimos|hice|habiamos\s+hecho)(?:\s+(hoy|ayer|anteayer|\s+(?:semana|la\s+semana)\s+pasada))?", 75),
            Pattern(REGEX, r"que\s+hizo\b", 60),
            Pattern(REGEX, r"(?:de\s+)?que\s+(?:hemos\s+)?habl(?:amos|ado)\b", 70),
            Pattern(REGEX, r"que\s+(?:(?:te\s+)?dije|(?:me\s+)?dijiste)(?:\s+(hoy|ayer|anteayer|\s+(?:semana|la\s+semana)\s+pasada))?", 70),
            Pattern(REGEX, r"(?:me\s+)?dijiste\s+algo\b", 70),
            Pattern(KEYWORD, "paso", 40, {"hoy": 20, "ayer": 20}),
            Pattern(REGEX, r"que\s+(?:cosas\s+)?recuerd[ao]s?\b", 75),
            Pattern(REGEX, r"que\s+recuerd[ao]s?\s+(?:sobre|de)\s+\S+", 80),
            Pattern(REGEX, r"recuerdas\s+(?:algo\s+)?(?:sobre|de)\s+\S+", 75),
            Pattern(REGEX, r"recuerd[ao]\s+lo\b", 70),
            Pattern(REGEX, r"tienes?\s+(?:algun[oa]\s+)?(?:en\s+|de\s+)?(?:la\s+)?memorias?", 70),
            Pattern(REGEX, r"que\s+memorias?\s+tienes", 70),
            Pattern(KEYWORD, "acuerdas", 65, {"de": 10}),
        ],
        priority=5,
        entity_group="memory",
    )
    assert plugin.name == MEMORY_SEARCH
    assert len(plugin.patterns) == 28
    assert plugin.priority == 5
    assert plugin.entity_group == "memory"


def test_memory_search_plugin_que_sabes_de_mi():
    """Verify MEMORY_SEARCH plugin classification via IntentLayer golden master."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()
    r = il.classify("que sabes de mi")
    assert r.intent == MEMORY_SEARCH
    # Confidence may vary; intent must be MEMORY_SEARCH


def test_memory_search_plugin_que_recuerdas_de_mi():
    """Verify MEMORY_SEARCH plugin classification for 'que recuerdas de mi'."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()
    r = il.classify("que recuerdas de mi")
    assert r.intent == MEMORY_SEARCH


def test_memory_search_plugin_que_sobre_mi():
    """Verify MEMORY_SEARCH plugin classification for 'que sabes sobre mi'."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()
    r = il.classify("que sabes sobre mi")
    assert r.intent == MEMORY_SEARCH