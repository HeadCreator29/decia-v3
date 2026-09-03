# tests/plugins/test_reflection_create.py - REFLECTION_CREATE Intent Plugin Tests
# Golden master: all 487 existing tests + new tests must pass

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from brain.plugins.reflection_create import plugin


def test_reflection_create_plugin_creation():
    """REFLECTION_CREATE plugin must exist with correct name."""
    assert plugin.name == "REFLECTION_CREATE"


def test_reflection_create_plugin_category():
    """REFLECTION_CREATE plugin must have REFLECTION category."""
    assert plugin.category == "REFLECTION"


def test_reflection_create_plugin_patterns():
    """REFLECTION_CREATE plugin must have patterns for reflection creation."""
    assert len(plugin.patterns) >= 3
    pattern_texts = [p.value for p in plugin.patterns]
    assert any("reflexion" in p.lower() for p in pattern_texts)
    assert any("diario" in p.lower() for p in pattern_texts)
    assert any("pensando" in p.lower() for p in pattern_texts)


def test_reflection_create_plugin_priority():
    """REFLECTION_CREATE plugin must have priority 5."""
    assert plugin.priority == 5


def test_reflection_create_plugin_entity_group():
    """REFLECTION_CREATE plugin must have entity_group for reflection extraction."""
    assert plugin.entity_group == "reflection_text"


def test_reflection_create_plugin_validate_default():
    """REFLECTION_CREATE plugin default validate() must return True."""
    assert plugin.validate("aprendi que no debo confiar", {}) is True


def test_reflection_create_classification_reflexion():
    """Test classification of 'reflexion:' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import REFLECTION_CREATE

    il = IntentLayer()
    result = il.classify("reflexion: hoy aprendí algo nuevo")
    assert result.intent == REFLECTION_CREATE
    assert result.confidence > 0


def test_reflection_create_classification_mi_reflexion():
    """Test classification of 'mi reflexión' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import REFLECTION_CREATE

    il = IntentLayer()
    result = il.classify("mi reflexión sobre el proyecto actual")
    assert result.intent == REFLECTION_CREATE
    assert result.confidence > 0


def test_reflection_create_classification_hoy_reflexione():
    """Test classification of 'hoy reflexioné' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import REFLECTION_CREATE

    il = IntentLayer()
    result = il.classify("hoy reflexioné sobre mis errores")
    assert result.intent == REFLECTION_CREATE
    assert result.confidence > 0


def test_reflection_create_classification_pensando_en():
    """Test classification of 'pensando en' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import REFLECTION_CREATE

    il = IntentLayer()
    result = il.classify("pensando en el futuro")
    assert result.intent == REFLECTION_CREATE
    assert result.confidence > 0


def test_reflection_create_classification_diario():
    """Test classification of 'diario:' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import REFLECTION_CREATE

    il = IntentLayer()
    result = il.classify("diario: aprendí a ser más paciente")
    assert result.intent == REFLECTION_CREATE
    assert result.confidence > 0