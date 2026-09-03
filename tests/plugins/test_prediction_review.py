# tests/plugins/test_prediction_review.py - PREDICTION_REVIEW Intent Plugin Tests
# Golden master: all 354 existing tests must pass unchanged


import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from brain.plugins.prediction_review import plugin


def test_prediction_review_plugin_creation():
    """PREDICTION_REVIEW plugin must exist with correct name."""
    assert plugin.name == "PREDICTION_REVIEW"


def test_prediction_review_plugin_category():
    """PREDICTION_REVIEW plugin must have PREDICTION category."""
    assert plugin.category == "PREDICTION"


def test_prediction_review_plugin_patterns():
    """PREDICTION_REVIEW plugin must have patterns for prediction review."""
    assert len(plugin.patterns) >= 3
    pattern_texts = [p.value for p in plugin.patterns]
    # Should match common prediction review phrases (normalized, no accents)
    assert any("revisar" in p.lower() for p in pattern_texts)
    assert any("predic" in p.lower() for p in pattern_texts)
    assert any("estado" in p.lower() for p in pattern_texts)


def test_prediction_review_plugin_priority():
    """PREDICTION_REVIEW plugin must have priority 5."""
    assert plugin.priority == 5


def test_prediction_review_plugin_entity_group():
    """PREDICTION_REVIEW plugin must have entity_group for prediction ID extraction."""
    assert plugin.entity_group == "prediction_id"


def test_prediction_review_plugin_validate_default():
    """PREDICTION_REVIEW plugin default validate() must return True."""
    assert plugin.validate("revisar prediccion", {}) is True


def test_prediction_review_classification_revisar_prediccion():
    """Test classification of 'revisar prediccion' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import PREDICTION_REVIEW

    il = IntentLayer()
    result = il.classify("revisar prediccion")
    assert result.intent == PREDICTION_REVIEW
    assert result.confidence > 0


def test_prediction_review_classification_prediccion_revision():
    """Test classification of 'prediccion revision' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import PREDICTION_REVIEW

    il = IntentLayer()
    result = il.classify("prediccion revision")
    assert result.intent == PREDICTION_REVIEW
    assert result.confidence > 0


def test_prediction_review_classification_como_fue():
    """Test classification of 'como fue mi prediccion' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import PREDICTION_REVIEW

    il = IntentLayer()
    result = il.classify("como fue mi prediccion")
    assert result.intent == PREDICTION_REVIEW
    assert result.confidence > 0


def test_prediction_review_classification_estado_prediccion():
    """Test classification of 'estado prediccion' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import PREDICTION_REVIEW

    il = IntentLayer()
    result = il.classify("estado prediccion")
    assert result.intent == PREDICTION_REVIEW
    assert result.confidence > 0


def test_prediction_review_classification_prediccion():
    """Test classification of 'prediccion' standalone pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import PREDICTION_REVIEW

    il = IntentLayer()
    result = il.classify("prediccion")
    assert result.intent == PREDICTION_REVIEW
    assert result.confidence > 0


def test_prediction_review_classification_prediccion_completa():
    """Test classification of 'prediccion completa' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import PREDICTION_REVIEW

    il = IntentLayer()
    result = il.classify("prediccion completa")
    assert result.intent == PREDICTION_REVIEW
    assert result.confidence > 0


def test_prediction_review_classification_ver_prediccion():
    """Test classification of 'ver prediccion' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import PREDICTION_REVIEW

    il = IntentLayer()
    result = il.classify("ver prediccion")
    assert result.intent == PREDICTION_REVIEW
    assert result.confidence > 0