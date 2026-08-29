# test_archive_direct.py - ARCHIVE_DIRECT plugin contract test
# Verifies ARCHIVE_DIRECT plugin classification matches golden master

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, PHRASE, REGEX, ARCHIVE_DIRECT
from brain.plugins.registry import PluginRegistry


def test_archive_direct_plugin_creation():
    """Verify ARCHIVE_DIRECT plugin can be created with patterns from _init_patterns()."""
    plugin = IntentPlugin(
        name="ARCHIVE_DIRECT",
        category="DECA_ARCHIVE",
        patterns=[
            Pattern(PHRASE, "cuando comenzo deca", 90),
            Pattern(PHRASE, "cuando empezo deca", 90),
            Pattern(PHRASE, "que significa deca", 90),
            Pattern(PHRASE, "significado de deca", 90),
            Pattern(PHRASE, "valores de deca", 90),
            Pattern(PHRASE, "cuales son los valores de deca", 90),
            Pattern(PHRASE, "vision de deca", 90),
            Pattern(PHRASE, "cual es la vision de deca", 90),
            Pattern(PHRASE, "quien creo deca", 90),
            Pattern(PHRASE, "quien es el creador de deca", 90),
            Pattern(PHRASE, "origen de deca", 90),
            Pattern(PHRASE, "quien fundo deca", 90),
            Pattern(PHRASE, "hablame de deca", 90),
            Pattern(PHRASE, "cuentame de deca", 90),
            Pattern(PHRASE, "cuentame un poco sobre deca", 90),
            Pattern(PHRASE, "que es deca", 90),
            Pattern(PHRASE, "cuentame sobre deca", 90),
            Pattern(PHRASE, "hablame sobre deca", 90),
            Pattern(PHRASE, "fundador de deca", 90),
            Pattern(PHRASE, "quien es el fundador de deca", 90),
            Pattern(PHRASE, "principios de deca", 90),
            Pattern(REGEX, r"inicio\s+(?:de\s+)?deca\b", 90),
            Pattern(REGEX, r"nacio\s+deca\b", 90),
        ],
        priority=5,
        entity_group=None,
    )
    assert plugin.name == ARCHIVE_DIRECT
    assert len(plugin.patterns) == 23
    assert plugin.priority == 5
    assert plugin.entity_group is None


def test_archive_direct_plugin_cuando_comenzo():
    """Verify ARCHIVE_DIRECT plugin classification via IntentLayer golden master."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()
    r = il.classify("cuando comenzo deca")
    assert r.intent == ARCHIVE_DIRECT
    assert r.confidence >= 0.90


def test_archive_direct_plugin_cuando_empezo():
    """Verify ARCHIVE_DIRECT plugin classification for 'cuando empezo deca'."""
    from brain.intent_layer import IntentLayer
    il = IntentLayer()
    r = il.classify("cuando empezo deca")
    assert r.intent == ARCHIVE_DIRECT
    assert r.confidence >= 0.90