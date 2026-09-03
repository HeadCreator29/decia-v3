# tests/plugins/test_identity_propose.py - IDENTITY_PROPOSE Intent Plugin Tests
# Golden master: all 518 existing tests must pass unchanged

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from brain.plugins.identity_propose import plugin


def test_identity_propose_plugin_creation():
    """IDENTITY_PROPOSE plugin must exist with correct name."""
    assert plugin.name == "IDENTITY_PROPOSE"


def test_identity_propose_plugin_category():
    """IDENTITY_PROPOSE plugin must have IDENTITY category."""
    assert plugin.category == "IDENTITY"


def test_identity_propose_plugin_patterns():
    """IDENTITY_PROPOSE plugin must have patterns for identity proposals."""
    assert len(plugin.patterns) >= 3
    pattern_texts = [p.value for p in plugin.patterns]
    assert any("cambiar identidad" in p.lower() for p in pattern_texts)
    assert any("propuesta" in p.lower() for p in pattern_texts)


def test_identity_propose_plugin_priority():
    """IDENTITY_PROPOSE plugin must have priority 5."""
    assert plugin.priority == 5


def test_identity_propose_plugin_entity_group():
    """IDENTITY_PROPOSE plugin must have entity_group for changes."""
    assert plugin.entity_group == "identity_changes"


def test_identity_propose_plugin_validate_default():
    """IDENTITY_PROPOSE plugin default validate() must return True."""
    assert plugin.validate("propongo cambiar identidad", {}) is True


def test_identity_propose_classification_cambiar():
    """Test classification of 'cambiar mi identidad' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import IDENTITY_PROPOSE

    il = IntentLayer()
    result = il.classify("cambiar mi identidad")
    assert result.intent == IDENTITY_PROPOSE
    assert result.confidence > 0


def test_identity_propose_classification_propuesta():
    """Test classification of 'propuesta identidad' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import IDENTITY_PROPOSE

    il = IntentLayer()
    result = il.classify("propuesta identidad")
    assert result.intent == IDENTITY_PROPOSE
    assert result.confidence > 0


def test_identity_propose_classification_modificar():
    """Test classification of 'modificar valores' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import IDENTITY_PROPOSE

    il = IntentLayer()
    result = il.classify("modificar valores")
    assert result.intent == IDENTITY_PROPOSE
    assert result.confidence > 0