# tests/services/test_learning.py - LearningPlugin Tests
# Golden master: all 465 existing tests must pass unchanged

import os
import sys
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "app"))

from app.services.plugins.learning import LearningPlugin


def _make_test_plugin():
    """Create a LearningPlugin with a temporary storage file for test isolation."""
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    tmp.close()
    return LearningPlugin(storage_path=tmp.name), tmp.name


def _cleanup_test_file(path):
    """Clean up temporary test file."""
    try:
        os.unlink(path)
    except Exception:
        pass


def test_learning_capture_basic():
    """Test basic learning capture."""
    plugin, tmp_path = _make_test_plugin()
    try:
        result = plugin.capture(
            trigger_id="dec_123",
            trigger_type="DECISION",
            expected="Migration successful",
            actual="Migration completed with minor issues",
            confidence=0.8,
        )
        assert result["id"] is not None
        assert result["trigger_id"] == "dec_123"
        assert result["trigger_type"] == "DECISION"
        assert result["expected"] == "Migration successful"
        assert result["actual"] == "Migration completed with minor issues"
        assert "delta" in result
        assert "lesson" in result
        assert "future_considerations" in result
        assert result["confidence"] == 0.8
    finally:
        _cleanup_test_file(tmp_path)


def test_learning_capture_exact_match():
    """Test learning capture when expected matches actual."""
    plugin, tmp_path = _make_test_plugin()
    try:
        result = plugin.capture(
            trigger_id="pred_456",
            trigger_type="PREDICTION",
            expected="Same outcome",
            actual="Same outcome",
            confidence=1.0,
        )
        assert result["delta"] == ""
        assert "matched" in result["lesson"].lower() or "no deviation" in result["lesson"].lower()
    finally:
        _cleanup_test_file(tmp_path)


def test_learning_synthesize_lesson():
    """Test synthesizing lesson from existing learning."""
    plugin, tmp_path = _make_test_plugin()
    try:
        created = plugin.capture(
            trigger_id="dec_123",
            trigger_type="DECISION",
            expected="Success",
            actual="Failure",
            confidence=0.9,
        )
        learning_id = created["id"]

        updated = plugin.synthesize_lesson(learning_id)
        assert updated is not None
        assert updated["id"] == learning_id
        assert "lesson" in updated
    finally:
        _cleanup_test_file(tmp_path)


def test_learning_get_by_trigger():
    """Test getting learnings by trigger."""
    plugin, tmp_path = _make_test_plugin()
    try:
        plugin.capture(
            trigger_id="dec_123",
            trigger_type="DECISION",
            expected="A", actual="B", confidence=0.8,
        )
        plugin.capture(
            trigger_id="dec_123",
            trigger_type="DECISION",
            expected="C", actual="D", confidence=0.7,
        )
        plugin.capture(
            trigger_id="pred_456",
            trigger_type="PREDICTION",
            expected="X", actual="Y", confidence=0.6,
        )

        dec_learnings = plugin.get_by_trigger("dec_123", "DECISION")
        assert len(dec_learnings) == 2

        pred_learnings = plugin.get_by_trigger("pred_456", "PREDICTION")
        assert len(pred_learnings) == 1

        empty = plugin.get_by_trigger("nonexistent", "DECISION")
        assert len(empty) == 0
    finally:
        _cleanup_test_file(tmp_path)


def test_learning_get_by_id():
    """Test getting a learning by ID."""
    plugin, tmp_path = _make_test_plugin()
    try:
        created = plugin.capture(
            trigger_id="test", trigger_type="DECISION",
            expected="A", actual="B", confidence=0.5,
        )
        retrieved = plugin.get_by_id(created["id"])
        assert retrieved is not None
        assert retrieved["id"] == created["id"]

        none_result = plugin.get_by_id("nonexistent-id")
        assert none_result is None
    finally:
        _cleanup_test_file(tmp_path)


def test_learning_list_all():
    """Test listing all learnings."""
    plugin, tmp_path = _make_test_plugin()
    try:
        plugin.capture(trigger_id="t1", trigger_type="DECISION", expected="A", actual="B")
        plugin.capture(trigger_id="t2", trigger_type="DECISION", expected="C", actual="D")
        plugin.capture(trigger_id="t3", trigger_type="PREDICTION", expected="X", actual="Y")

        all_learnings = plugin.list_all()
        assert len(all_learnings) == 3
    finally:
        _cleanup_test_file(tmp_path)


def test_learning_update_confidence():
    """Test updating learning confidence."""
    plugin, tmp_path = _make_test_plugin()
    try:
        created = plugin.capture(
            trigger_id="test", trigger_type="DECISION",
            expected="A", actual="B", confidence=0.5,
        )
        updated = plugin.update_confidence(created["id"], 0.95)
        assert updated is not None
        assert updated["confidence"] == 0.95

        # Out of bounds should be clamped
        updated_low = plugin.update_confidence(created["id"], -0.1)
        assert updated_low["confidence"] == 0.0

        updated_high = plugin.update_confidence(created["id"], 1.5)
        assert updated_high["confidence"] == 1.0
    finally:
        _cleanup_test_file(tmp_path)


def test_learning_auto_capture_from_decision():
    """Test auto-capturing learning from decision confirmation."""
    plugin, tmp_path = _make_test_plugin()
    try:
        result = plugin.auto_capture_from_decision_confirm(
            decision_id="dec_123",
            outcome="Success",
            learning="Migration was smooth",
        )
        assert result is not None
        assert result["trigger_id"] == "dec_123"
        assert result["trigger_type"] == "DECISION"
        assert "expected" in result
        assert "actual" in result
    finally:
        _cleanup_test_file(tmp_path)


def test_learning_auto_capture_from_prediction():
    """Test auto-capturing learning from prediction resolution."""
    plugin, tmp_path = _make_test_plugin()
    try:
        result = plugin.auto_capture_from_prediction_resolve(
            prediction_id="pred_456",
            outcome="Confirmed",
            learning="Model was accurate",
        )
        assert result is not None
        assert result["trigger_id"] == "pred_456"
        assert result["trigger_type"] == "PREDICTION"
    finally:
        _cleanup_test_file(tmp_path)


def test_learning_persistence():
    """Test that learnings are persisted to JSON file."""
    plugin, tmp_path = _make_test_plugin()
    try:
        created = plugin.capture(
            trigger_id="Persistence test", trigger_type="DECISION",
            expected="A", actual="B",
        )
        assert os.path.exists(tmp_path)

        with open(tmp_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert len(data) >= 1
        created_ids = [d["id"] for d in data]
        assert created["id"] in created_ids
    finally:
        _cleanup_test_file(tmp_path)


def test_learning_default_confidence():
    """Test that default confidence is 1.0."""
    plugin, tmp_path = _make_test_plugin()
    try:
        created = plugin.capture(
            trigger_id="Test default", trigger_type="DECISION",
            expected="A", actual="B",
        )
        assert created["confidence"] == 1.0
    finally:
        _cleanup_test_file(tmp_path)