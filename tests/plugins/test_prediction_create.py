# tests/plugins/test_prediction_create.py - PREDICTION_CREATE Intent Plugin Tests
# Golden master: all 354 existing tests must pass unchanged


import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from brain.plugins.prediction_create import plugin


def test_prediction_create_plugin_creation():
    """PREDICTION_CREATE plugin must exist with correct name."""
    assert plugin.name == "PREDICTION_CREATE"


def test_prediction_create_plugin_category():
    """PREDICTION_CREATE plugin must have PREDICTION category."""
    assert plugin.category == "PREDICTION"


def test_prediction_create_plugin_patterns():
    """PREDICTION_CREATE plugin must have patterns for prediction creation."""
    assert len(plugin.patterns) >= 3
    pattern_texts = [p.value for p in plugin.patterns]
    # Should match common prediction creation phrases (normalized, no accents)
    assert any("predigo" in p.lower() for p in pattern_texts)
    assert any("predic" in p.lower() for p in pattern_texts)
    assert any("creo" in p.lower() for p in pattern_texts)


def test_prediction_create_plugin_priority():
    """PREDICTION_CREATE plugin must have priority 5."""
    assert plugin.priority == 5


def test_prediction_create_plugin_entity_group():
    """PREDICTION_CREATE plugin must have entity_group for text extraction."""
    assert plugin.entity_group == "prediction_text"


def test_prediction_create_plugin_validate_default():
    """PREDICTION_CREATE plugin default validate() must return True."""
    assert plugin.validate("predigo que lloverá", {}) is True


def test_prediction_create_classification_predigo_que():
    """Test classification of 'predigo que' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import PREDICTION_CREATE

    il = IntentLayer()
    result = il.classify("predigo que lloverá mañana")
    assert result.intent == PREDICTION_CREATE
    assert result.confidence > 0


def test_prediction_create_classification_mi_prediction():
    """Test classification of 'mi prediccion es' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import PREDICTION_CREATE

    il = IntentLayer()
    result = il.classify("mi prediccion es que vendrá un cambio")
    assert result.intent == PREDICTION_CREATE
    assert result.confidence > 0


def test_prediction_create_classification_creo_que():
    """Test classification of 'creo que pasará' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import PREDICTION_CREATE

    il = IntentLayer()
    result = il.classify("creo que pasará algo importante")
    assert result.intent == PREDICTION_CREATE
    assert result.confidence > 0


def test_prediction_create_classification_en_el_futuro():
    """Test classification of 'en el futuro' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import PREDICTION_CREATE

    il = IntentLayer()
    result = il.classify("en el futuro veremos")
    assert result.intent == PREDICTION_CREATE
    assert result.confidence > 0


def test_prediction_create_classification_pronostico():
    """Test classification of 'pronostico' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import PREDICTION_CREATE

    il = IntentLayer()
    result = il.classify("pronostico lluvia")
    assert result.intent == PREDICTION_CREATE
    assert result.confidence > 0


def test_prediction_create_classification_pronostico_que():
    """Test classification of 'pronostico que' pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import PREDICTION_CREATE

    il = IntentLayer()
    result = il.classify("pronostico que lloverá")
    assert result.intent == PREDICTION_CREATE
    assert result.confidence > 0


def test_prediction_create_classification_prediction():
    """Test classification of 'prediction' (English) pattern."""
    from brain.intent_layer import IntentLayer
    from brain.intent_types import PREDICTION_CREATE

    il = IntentLayer()
    result = il.classify("prediction rain tomorrow")
    assert result.intent == PREDICTION_CREATE
    assert result.confidence > 0