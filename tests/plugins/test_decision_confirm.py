# tests/plugins/test_decision_confirm.py - DECISION_CONFIRM Intent Plugin Tests
# Golden master: all 354 existing tests must pass unchanged

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from brain.plugins.decision_confirm import plugin


def test_decision_confirm_plugin_creation():
    """DECISION_CONFIRM plugin must exist with correct name."""
    assert plugin.name == "DECISION_CONFIRM"


def test_decision_confirm_plugin_category():
    """DECISION_CONFIRM plugin must have DECISION category."""
    assert plugin.category == "DECISION"


def test_decision_confirm_plugin_patterns():
    """DECISION_CONFIRM plugin must have patterns for decision confirmation."""
    assert len(plugin.patterns) >= 3
    pattern_texts = [p.value for p in plugin.patterns]
    assert any("confirmo" in p.lower() for p in pattern_texts)
    assert any("confirmada" in p.lower() for p in pattern_texts)


def test_decision_confirm_plugin_priority():
    """DECISION_CONFIRM plugin must have priority 5."""
    assert plugin.priority == 5


def test_decision_confirm_plugin_entity_group():
    """DECISION_CONFIRM plugin must have entity_group for decision_id extraction."""
    assert plugin.entity_group == "decision_id"


def test_decision_confirm_plugin_validate_default():
    """DECISION_CONFIRM plugin default validate() must return True."""
    assert plugin.validate("confirmo decisión", {}) is True


def test_decision_confirm_classification_confirmo():
    """Test classification of 'confirmo decisión' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import DECISION_CONFIRM

    il = IntentLayer()
    result = il.classify("confirmo decisión")
    assert result.intent == DECISION_CONFIRM
    assert result.confidence > 0


def test_decision_confirm_classification_confirmada():
    """Test classification of 'decisión confirmada' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import DECISION_CONFIRM

    il = IntentLayer()
    result = il.classify("decisión confirmada")
    assert result.intent == DECISION_CONFIRM
    assert result.confidence > 0


def test_decision_confirm_classification_resultado():
    """Test classification of 'resultado decisión' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import DECISION_CONFIRM

    il = IntentLayer()
    result = il.classify("resultado decisión")
    assert result.intent == DECISION_CONFIRM
    assert result.confidence > 0


def test_decision_confirm_classification_apruebo():
    """Test classification of 'apruebo decisión' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import DECISION_CONFIRM

    il = IntentLayer()
    result = il.classify("apruebo decisión")
    assert result.intent == DECISION_CONFIRM
    assert result.confidence > 0