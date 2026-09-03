# tests/plugins/test_learning_create.py - LEARNING_CREATE Intent Plugin Tests
# Golden master: all 465 existing tests must pass unchanged

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from brain.plugins.learning_create import plugin


def test_learning_create_plugin_creation():
    """LEARNING_CREATE plugin must exist with correct name."""
    assert plugin.name == "LEARNING_CREATE"


def test_learning_create_plugin_category():
    """LEARNING_CREATE plugin must have LEARNING category."""
    assert plugin.category == "LEARNING"


def test_learning_create_plugin_patterns():
    """LEARNING_CREATE plugin must have patterns for learning creation."""
    assert len(plugin.patterns) >= 3
    pattern_texts = [p.value for p in plugin.patterns]
    assert any("aprendi" in p.lower() for p in pattern_texts)
    assert any("leccion" in p.lower() for p in pattern_texts)


def test_learning_create_plugin_priority():
    """LEARNING_CREATE plugin must have priority 5."""
    assert plugin.priority == 5


def test_learning_create_plugin_entity_group():
    """LEARNING_CREATE plugin must have entity_group for lesson extraction."""
    assert plugin.entity_group == "lesson_text"


def test_learning_create_plugin_validate_default():
    """LEARNING_CREATE plugin default validate() must return True."""
    assert plugin.validate("aprendi que no debo confiar", {}) is True


def test_learning_create_classification_aprendi():
    """Test classification of 'aprendi que' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import LEARNING_CREATE

    il = IntentLayer()
    result = il.classify("aprendi que no debo confiar")
    assert result.intent == LEARNING_CREATE
    assert result.confidence > 0


def test_learning_create_classification_leccion():
    """Test classification of 'la leccion es' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import LEARNING_CREATE

    il = IntentLayer()
    result = il.classify("la leccion es ser paciente")
    assert result.intent == LEARNING_CREATE
    assert result.confidence > 0


def test_learning_create_classification_que_aprendi():
    """Test classification of 'que aprendi' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import LEARNING_CREATE

    il = IntentLayer()
    result = il.classify("que aprendi hoy")
    assert result.intent == LEARNING_CREATE
    assert result.confidence > 0


def test_learning_create_classification_aprendizaje():
    """Test classification of 'aprendizaje:' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import LEARNING_CREATE

    il = IntentLayer()
    result = il.classify("aprendizaje: ser mas cuidadoso")
    assert result.intent == LEARNING_CREATE
    assert result.confidence > 0


def test_learning_create_classification_leccion_aprendida():
    """Test classification of 'leccion aprendida' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import LEARNING_CREATE

    il = IntentLayer()
    result = il.classify("leccion aprendida: verificar todo")
    assert result.intent == LEARNING_CREATE
    assert result.confidence > 0