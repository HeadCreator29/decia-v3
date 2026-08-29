# test_archive_search.py - ARCHIVE_SEARCH plugin contract test
# Verifies ARCHIVE_SEARCH plugin classification matches golden master

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, KEYWORD, PHRASE, REGEX, ARCHIVE_SEARCH
from brain.plugins.registry import PluginRegistry


def test_archive_search_plugin_creation():
    """Verify ARCHIVE_SEARCH plugin can be created with patterns from _init_patterns()."""
    plugin = IntentPlugin(
        name="ARCHIVE_SEARCH",
        category="DECA_ARCHIVE",
        patterns=[
            Pattern(KEYWORD, "significa", 35, {"deca": 10}),
            Pattern(KEYWORD, "significado", 35, {"deca": 10}),
            Pattern(PHRASE, "historia de deca", 85),
            Pattern(PHRASE, "eventos de deca", 85),
            Pattern(REGEX,
                    r"que\s+(?:eventos|"
                    r"acontecimientos|hechos|"
                    r"evento|acontecimiento|hecho)\s+"
                    r"(?:sucedio|acontecio|ocurrio|"
                    r"sucedieron|acontecieron|"
                    r"ocurrieron|pasaron|paso|hubo|"
                    r"hubieron|ha\s+pasado|"
                    r"han\s+pasado|ha\s+habido|"
                    r"han\s+habido)\s+"
                    r"(?:(?:con|sobre)\s+.+?\s+)?"
                    r"(?:hoy|ayer|anteayer|"
                    r"esta\s+semana|"
                    r"(?:la\s+)?semana\s+pasada|"
                    r"este\s+mes|(?:el\s+)?mes\s+"
                    r"pasado|el\s+(?:lunes|martes|"
                    r"miercoles|jueves|viernes|"
                    r"sabado|domingo)|"
                    r"hace\s+(?:una?|\d+)\s+"
                    r"(?:dia|dias|semana|semanas|"
                    r"mes|meses))\b",
                    75),
            Pattern(REGEX,
                    r"que\s+acontecio\s+"
                    r"(?:(?:con|sobre)\s+.+?\s+)?"
                    r"(?:hoy|ayer|anteayer|"
                    r"esta\s+semana|"
                    r"(?:la\s+)?semana\s+pasada|"
                    r"este\s+mes|(?:el\s+)?mes\s+"
                    r"pasado|el\s+(?:lunes|martes|"
                    r"miercoles|jueves|viernes|"
                    r"sabado|domingo)|"
                    r"hace\s+(?:una?|\d+)\s+"
                    r"(?:dia|dias|semana|semanas|"
                    r"mes|meses))\b",
                    75),
            Pattern(REGEX,
                    r"que\s+(?:eventos|"
                    r"acontecimientos|"
                    r"acontecimiento|evento|"
                    r"hechos|hecho)\s+"
                    r"(?:sucedio|acontecio|"
                    r"ocurrio|sucedieron|"
                    r"acontecieron|ocurrieron|"
                    r"pasaron|paso|hubo|hubieron|"
                    r"ha\s+pasado|han\s+pasado|"
                    r"ha\s+habido|han\s+habido)"
                    r"\s+(?:sobre|con)\s+\S+",
                    75),
            Pattern(REGEX,
                    r"cual(?:es)?\s+son\s+(?:los\s+)?(?:valores|principios)"
                    r"(?!\s+d(?:e|el)\s+(?!deca\b))",
                    60),
            Pattern(REGEX,
                    r"objetivos?\s+(?:de\s+|tiene\s+)?deca\b",
                    85),
            Pattern(KEYWORD, "recuerda", 35, {"deca": 15}),
            Pattern(KEYWORD, "recuerdo", 35, {"deca": 15}),
            Pattern(KEYWORD, "memorias", 35, {"deca": 15}),
            Pattern(PHRASE, "que hay registrado", 80),
            Pattern(PHRASE, "que tienes guardado", 80),
            Pattern(PHRASE, "que hay guardado", 80),
            Pattern(PHRASE, "que tienes registrado", 80),
            Pattern(PHRASE, "que hay en el archivo", 85),
            Pattern(PHRASE, "que hay en archivo", 85),
            Pattern(PHRASE, "que tengo guardado", 80),
            Pattern(PHRASE, "que tengo registrado", 80),
            Pattern(REGEX,
                    r"que\s+(hay|tienes|tengo)\s+(registrado|guardado|almacenado)",
                    80),
            Pattern(REGEX,
                    r"que\s+(hay|tienes)\s+en\s+(el\s+)?archivo",
                    85),
            Pattern(KEYWORD, "registrado", 45, {"hay": 15, "archivo": 15}),
            Pattern(KEYWORD, "guardado", 45, {"hay": 15, "archivo": 15}),
        ],
        priority=5,
        entity_group=None,
    )
    assert plugin.name == ARCHIVE_SEARCH
    assert len(plugin.patterns) == 24
    assert plugin.priority == 5
    assert plugin.entity_group is None


def test_archive_search_plugin_historia_de_deca():
    """Verify ARCHIVE_SEARCH plugin classification via IntentLayer golden master."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()
    r = il.classify("historia de deca")
    assert r.intent == ARCHIVE_SEARCH
    # Confidence may vary; intent must be ARCHIVE_SEARCH


def test_archive_search_plugin_eventos_de_deca():
    """Verify ARCHIVE_SEARCH plugin classification for 'eventos de deca'."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()
    r = il.classify("eventos de deca")
    assert r.intent == ARCHIVE_SEARCH
    # Confidence may vary; intent must be ARCHIVE_SEARCH