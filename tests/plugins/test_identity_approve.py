# tests/plugins/test_identity_approve.py - IDENTITY_APPROVE Intent Plugin Tests
# Golden master: all 518 existing tests must pass unchanged

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from brain.plugins.identity_approve import plugin


def test_identity_approve_plugin_creation():
    """IDENTITY_APPROVE plugin must exist with correct name."""
    assert plugin.name == "IDENTITY_APPROVE"


def test_identity_approve_plugin_category():
    """IDENTITY_APPROVE plugin must have IDENTITY category."""
    assert plugin.category == "IDENTITY"


def test_identity_approve_plugin_patterns():
    """IDENTITY_APPROVE plugin must have patterns for identity approval."""
    assert len(plugin.patterns) >= 3
    pattern_texts = [p.value for p in plugin.patterns]
    assert any("aprobar" in p.lower() for p in pattern_texts)
    assert any("confirmar" in p.lower() for p in pattern_texts)


def test_identity_approve_plugin_priority():
    """IDENTITY_APPROVE plugin must have priority 5."""
    assert plugin.priority == 5


def test_identity_approve_plugin_entity_group():
    """IDENTITY_APPROVE plugin must have entity_group for proposal_id."""
    assert plugin.entity_group == "proposal_id"


def test_identity_approve_plugin_validate_default():
    """IDENTITY_APPROVE plugin default validate() must return True."""
    assert plugin.validate("aprobar identidad", {}) is True


def test_identity_approve_classification_aprobar():
    """Test classification of 'aprobar identidad' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import IDENTITY_APPROVE

    il = IntentLayer()
    result = il.classify("aprobar identidad")
    assert result.intent == IDENTITY_APPROVE
    assert result.confidence > 0


def test_identity_approve_classification_confirmar():
    """Test classification of 'confirmar cambios identidad' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import IDENTITY_APPROVE

    il = IntentLayer()
    result = il.classify("confirmar cambios identidad")
    assert result.intent == IDENTITY_APPROVE
    assert result.confidence > 0


def test_identity_approve_classification_aceptar():
    """Test classification of 'aceptar propuesta identidad' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import IDENTITY_APPROVE

    il = IntentLayer()
    result = il.classify("aceptar propuesta identidad")
    assert result.intent == IDENTITY_APPROVE
    assert result.confidence > 0