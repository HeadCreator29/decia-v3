# tests/plugins/test_decision_create.py - DECISION_CREATE Intent Plugin Tests
# Golden master: all 354 existing tests must pass unchanged

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from brain.plugins.decision_create import plugin


def test_decision_create_plugin_creation():
    """DECISION_CREATE plugin must exist with correct name."""
    assert plugin.name == "DECISION_CREATE"


def test_decision_create_plugin_category():
    """DECISION_CREATE plugin must have DECISION category."""
    assert plugin.category == "DECISION"


def test_decision_create_plugin_patterns():
    """DECISION_CREATE plugin must have patterns for decision creation."""
    assert len(plugin.patterns) >= 3
    pattern_texts = [p.value for p in plugin.patterns]
    # Should match common decision creation phrases (normalized, no accents)
    assert any("decido" in p.lower() for p in pattern_texts)
    assert any("decision" in p.lower() for p in pattern_texts)


def test_decision_create_plugin_priority():
    """DECISION_CREATE plugin must have priority 5."""
    assert plugin.priority == 5


def test_decision_create_plugin_entity_group():
    """DECISION_CREATE plugin must have entity_group for problem extraction."""
    assert plugin.entity_group == "decision_problem"


def test_decision_create_plugin_validate_default():
    """DECISION_CREATE plugin default validate() must return True."""
    assert plugin.validate("decido migrar a SQLite", {}) is True


def test_decision_create_classification_decido_que():
    """Test classification of 'decido que' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import DECISION_CREATE

    il = IntentLayer()
    result = il.classify("decido que migrar a SQLite")
    assert result.intent == DECISION_CREATE
    assert result.confidence > 0


def test_decision_create_classification_mi_decision():
    """Test classification of 'mi decisión es' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import DECISION_CREATE

    il = IntentLayer()
    result = il.classify("mi decisión es usar SQLite")
    assert result.intent == DECISION_CREATE
    assert result.confidence > 0


def test_decision_create_classification_he_decidido():
    """Test classification of 'he decidido' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import DECISION_CREATE

    il = IntentLayer()
    result = il.classify("he decidido migrar la base de datos")
    assert result.intent == DECISION_CREATE
    assert result.confidence > 0


def test_decision_create_classification_resolucion():
    """Test classification of 'resolución:' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import DECISION_CREATE

    il = IntentLayer()
    result = il.classify("resolución: usar SQLite para FTS5")
    assert result.intent == DECISION_CREATE
    assert result.confidence > 0