# tests/plugins/test_reflection_approve.py - REFLECTION_APPROVE Intent Plugin Tests
# Golden master: all 487 existing tests + new tests must pass

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from brain.plugins.reflection_approve import plugin


def test_reflection_approve_plugin_creation():
    """REFLECTION_APPROVE plugin must exist with correct name."""
    assert plugin.name == "REFLECTION_APPROVE"


def test_reflection_approve_plugin_category():
    """REFLECTION_APPROVE plugin must have REFLECTION category."""
    assert plugin.category == "REFLECTION"


def test_reflection_approve_plugin_patterns():
    """REFLECTION_APPROVE plugin must have patterns for reflection approval."""
    assert len(plugin.patterns) >= 3
    pattern_texts = [p.value for p in plugin.patterns]
    assert any("aprobar" in p.lower() for p in pattern_texts)
    assert any("confirmar" in p.lower() for p in pattern_texts)
    assert any("publicar" in p.lower() for p in pattern_texts)
    assert any("aceptar" in p.lower() for p in pattern_texts)


def test_reflection_approve_plugin_priority():
    """REFLECTION_APPROVE plugin must have priority 5."""
    assert plugin.priority == 5


def test_reflection_approve_plugin_entity_group():
    """REFLECTION_APPROVE plugin must have entity_group for reflection ID extraction."""
    assert plugin.entity_group == "reflection_id"


def test_reflection_approve_plugin_validate_default():
    """REFLECTION_APPROVE plugin default validate() must return True."""
    assert plugin.validate("aprobar reflexion", {}) is True


def test_reflection_approve_classification_aprobar_reflexion():
    """Test classification of 'aprobar reflexión' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import REFLECTION_APPROVE

    il = IntentLayer()
    result = il.classify("aprobar reflexión del proyecto")
    assert result.intent == REFLECTION_APPROVE
    assert result.confidence > 0


def test_reflection_approve_classification_confirmar_reflexion():
    """Test classification of 'confirmar reflexión' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import REFLECTION_APPROVE

    il = IntentLayer()
    result = il.classify("confirmar reflexión reciente")
    assert result.intent == REFLECTION_APPROVE
    assert result.confidence > 0


def test_reflection_approve_classification_publicar_reflexion():
    """Test classification of 'publicar reflexión' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import REFLECTION_APPROVE

    il = IntentLayer()
    result = il.classify("publicar reflexión final")
    assert result.intent == REFLECTION_APPROVE
    assert result.confidence > 0


def test_reflection_approve_classification_aceptar_borrador():
    """Test classification of 'aceptar borrador' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import REFLECTION_APPROVE

    il = IntentLayer()
    result = il.classify("aceptar borrador")
    assert result.intent == REFLECTION_APPROVE
    assert result.confidence > 0