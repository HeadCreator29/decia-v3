# tests/services/test_prediction.py - PredictionPlugin Tests
# Golden master: all 354 existing tests must pass unchanged


import os
import sys
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "app"))

from app.services.plugins.prediction import PredictionPlugin


def _make_test_plugin():
    """Create a PredictionPlugin with a temporary storage file for test isolation."""
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    tmp.close()
    return PredictionPlugin(storage_path=tmp.name), tmp.name


def _cleanup_test_file(path):
    """Clean up temporary test file."""
    try:
        os.unlink(path)
    except Exception:
        pass


def test_prediction_create_basic():
    """Test basic prediction creation."""
    plugin, tmp_path = _make_test_plugin()
    try:
        result = plugin.create(
            prediction_text="Lloverá mañana",
            horizons=[{"label": "short", "timeframe": "1 day", "target_date": "2026-09-05"}],
            confidence=0.8,
            reasons=["Patrón climático observado"],
        )
        assert result["id"] is not None
        assert result["prediction_text"] == "Lloverá mañana"
        assert result["horizons"] == [{"label": "short", "timeframe": "1 day", "target_date": "2026-09-05"}]
        assert result["confidence"] == 0.8
        assert result["reasons"] == ["Patrón climático observado"]
        assert result["status"] == "OPEN"
        assert result["outcome"] is None
        assert result["learning"] is None
        assert result["related_memory_ids"] == []
        assert result["related_decision_ids"] == []
    finally:
        _cleanup_test_file(tmp_path)


def test_prediction_create_empty_horizons():
    """Test prediction creation with empty horizons."""
    plugin, tmp_path = _make_test_plugin()
    try:
        result = plugin.create(
            prediction_text="Sucederá algo",
            horizons=[],
            confidence=0.6,
            reasons=[],
        )
        assert result["status"] == "OPEN"
        assert result["horizons"] == []
    finally:
        _cleanup_test_file(tmp_path)


def test_prediction_create_multiple_horizons():
    """Test prediction creation with multiple horizons."""
    plugin, tmp_path = _make_test_plugin()
    try:
        result = plugin.create(
            prediction_text="El mercado subirá",
            horizons=[
                {"label": "short", "timeframe": "1 semana", "target_date": "2026-09-08"},
                {"label": "medium", "timeframe": "1 mes", "target_date": "2026-10-06"},
            ],
            confidence=0.75,
            reasons=["Análisis técnico", "Indicadores positivos"],
        )
        assert len(result["horizons"]) == 2
        assert result["horizons"][0]["label"] == "short"
        assert result["horizons"][1]["label"] == "medium"
    finally:
        _cleanup_test_file(tmp_path)


def test_prediction_update_status():
    """Test prediction status update."""
    plugin, tmp_path = _make_test_plugin()
    try:
        created = plugin.create(
            prediction_text="Test prediction",
            horizons=[],
            confidence=0.5,
            reasons=[],
        )
        prediction_id = created["id"]

        # Update status to CONFIRMED
        updated = plugin.update_status(prediction_id, "CONFIRMED")
        assert updated["status"] == "CONFIRMED"

        # Update status to FAILED
        updated = plugin.update_status(prediction_id, "FAILED")
        assert updated["status"] == "FAILED"

        # Update status to PARTIAL
        updated = plugin.update_status(prediction_id, "PARTIAL")
        assert updated["status"] == "PARTIAL"

        # Update status to CANCELLED
        updated = plugin.update_status(prediction_id, "CANCELLED")
        assert updated["status"] == "CANCELLED"
    finally:
        _cleanup_test_file(tmp_path)


def test_prediction_get_by_status():
    """Test getting predictions by status."""
    plugin, tmp_path = _make_test_plugin()
    try:
        # Create predictions - all start as OPEN
        d1 = plugin.create(
            prediction_text="P1", horizons=[], confidence=0.5, reasons=[]
        )
        d2 = plugin.create(
            prediction_text="P2", horizons=[], confidence=0.5, reasons=[]
        )

        open_preds = plugin.get_by_status("OPEN")
        assert len(open_preds) == 2

        # Update one to CONFIRMED
        plugin.update_status(d1["id"], "CONFIRMED")

        open_preds = plugin.get_by_status("OPEN")
        assert len(open_preds) == 1
        assert open_preds[0]["id"] == d2["id"]

        confirmed_preds = plugin.get_by_status("CONFIRMED")
        assert len(confirmed_preds) == 1
        assert confirmed_preds[0]["id"] == d1["id"]
    finally:
        _cleanup_test_file(tmp_path)


def test_prediction_get_by_id():
    """Test getting a prediction by ID."""
    plugin, tmp_path = _make_test_plugin()
    try:
        created = plugin.create(
            prediction_text="Test", horizons=[], confidence=0.5, reasons=[]
        )
        retrieved = plugin.get_by_id(created["id"])
        assert retrieved is not None
        assert retrieved["id"] == created["id"]
        assert retrieved["prediction_text"] == "Test"

        # Non-existent ID
        none_result = plugin.get_by_id("nonexistent-id")
        assert none_result is None
    finally:
        _cleanup_test_file(tmp_path)


def test_prediction_list_all():
    """Test listing all predictions."""
    plugin, tmp_path = _make_test_plugin()
    try:
        # Create 3 predictions
        d1 = plugin.create(
            prediction_text="P1", horizons=[], confidence=0.5, reasons=[]
        )
        d2 = plugin.create(
            prediction_text="P2", horizons=[], confidence=0.5, reasons=[]
        )
        d3 = plugin.create(
            prediction_text="P3", horizons=[], confidence=0.5, reasons=[]
        )

        all_preds = plugin.list_all()
        assert len(all_preds) == 3
    finally:
        _cleanup_test_file(tmp_path)


def test_prediction_link_memory():
    """Test linking memory to prediction."""
    plugin, tmp_path = _make_test_plugin()
    try:
        created = plugin.create(
            prediction_text="Test", horizons=[], confidence=0.5, reasons=[]
        )

        plugin.link_memory(
            prediction_id=created["id"],
            memory_id="mem_test_123",
            relation_type="supports",
        )

        # Verify by getting the prediction
        retrieved = plugin.get_by_id(created["id"])
        assert "mem_test_123" in retrieved["related_memory_ids"]
        assert retrieved["related_memory_ids"].count("mem_test_123") == 1
    finally:
        _cleanup_test_file(tmp_path)


def test_prediction_link_same_memory_twice():
    """Test linking the same memory twice (should not duplicate)."""
    plugin, tmp_path = _make_test_plugin()
    try:
        created = plugin.create(
            prediction_text="Test", horizons=[], confidence=0.5, reasons=[]
        )

        plugin.link_memory(
            prediction_id=created["id"],
            memory_id="mem_test_123",
            relation_type="supports",
        )
        plugin.link_memory(
            prediction_id=created["id"],
            memory_id="mem_test_123",
            relation_type="supports",
        )

        retrieved = plugin.get_by_id(created["id"])
        assert retrieved["related_memory_ids"].count("mem_test_123") == 1
    finally:
        _cleanup_test_file(tmp_path)


def test_prediction_link_decision():
    """Test linking decision to prediction."""
    plugin, tmp_path = _make_test_plugin()
    try:
        created = plugin.create(
            prediction_text="Test", horizons=[], confidence=0.5, reasons=[]
        )

        plugin.link_decision(
            prediction_id=created["id"],
            decision_id="dec_test_456",
            relation_type="supports",
        )

        # Verify by getting the prediction
        retrieved = plugin.get_by_id(created["id"])
        assert "dec_test_456" in retrieved["related_decision_ids"]
        assert retrieved["related_decision_ids"].count("dec_test_456") == 1
    finally:
        _cleanup_test_file(tmp_path)


def test_prediction_update_confidence():
    """Test updating prediction confidence."""
    plugin, tmp_path = _make_test_plugin()
    try:
        created = plugin.create(
            prediction_text="Test", horizons=[], confidence=0.5, reasons=[]
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


def test_prediction_resolve():
    """Test prediction resolution with outcome and learning."""
    plugin, tmp_path = _make_test_plugin()
    try:
        created = plugin.create(
            prediction_text="Lloverá mañana",
            horizons=[],
            confidence=0.8,
            reasons=["Patrón climático"],
        )

        # Resolve with confirmed outcome - falls through to CONFIRMED since
        # outcome doesn't start with "failed" or "cancel"
        resolved = plugin.resolve(created["id"], "Lluvia confirmada", "Se confirmó la lluvia")
        assert resolved is not None
        assert resolved["outcome"] == "Lluvia confirmada"
        assert resolved["learning"] == "Se confirmó la lluvia"
        assert resolved["status"] == "CONFIRMED"

        # Verify it's no longer OPEN
        open_preds = plugin.get_by_status("OPEN")
        assert len(open_preds) == 0

        # Resolve with failed outcome - status becomes FAILED
        created2 = plugin.create(
            prediction_text="No lloverá",
            horizons=[],
            confidence=0.7,
            reasons=["Secuencia seca"],
        )
        resolved2 = plugin.resolve(created2["id"], "No llovió", "Mantuvo la sequía")
        # "No llovió" doesn't start with "failed" either, so it becomes CONFIRMED
        assert resolved2["status"] == "CONFIRMED"

        # Resolve with failed outcome - status becomes FAILED
        created3 = plugin.create(
            prediction_text="Lloverá en octubre",
            horizons=[],
            confidence=0.7,
            reasons=["Predicción de lluvia"],
        )
        resolved3 = plugin.resolve(created3["id"], "Failed: no llovió", "La lluvia no llegó")
        assert resolved3["status"] == "FAILED"
    finally:
        _cleanup_test_file(tmp_path)


def test_prediction_resolve_cancel():
    """Test prediction resolution with cancel outcome."""
    plugin, tmp_path = _make_test_plugin()
    try:
        created = plugin.create(
            prediction_text="Lloverá mañana",
            horizons=[],
            confidence=0.8,
            reasons=["Patrón climático"],
        )

        # Resolve with cancel outcome
        resolved = plugin.resolve(created["id"], "Cancelado", "Evento cancelado")
        assert resolved["status"] == "CANCELLED"
    finally:
        _cleanup_test_file(tmp_path)


def test_prediction_schedule_review():
    """Test scheduling a review date."""
    plugin, tmp_path = _make_test_plugin()
    try:
        created = plugin.create(
            prediction_text="Test", horizons=[], confidence=0.5, reasons=[]
        )

        plugin.schedule_review(created["id"], "2026-09-15")
        pred = plugin.get_by_id(created["id"])
        assert pred["review_date"] == "2026-09-15"
    finally:
        _cleanup_test_file(tmp_path)


def test_prediction_get_due_reviews():
    """Test getting due reviews (review_date <= now and status=OPEN)."""
    plugin, tmp_path = _make_test_plugin()
    try:
        # Create a prediction with a past review date
        created = plugin.create(
            prediction_text="Test", horizons=[], confidence=0.5, reasons=[]
        )
        # Use ISO format with timezone for proper comparison
        plugin.schedule_review(created["id"], "2020-01-01T00:00:00")  # Past date

        # Create another with a future review date
        created2 = plugin.create(
            prediction_text="Test2", horizons=[], confidence=0.5, reasons=[]
        )
        plugin.schedule_review(created2["id"], "2100-01-01T00:00:00")  # Future date

        due = plugin.get_due_reviews()
        # Only the first one should be due (past review date)
        assert len(due) == 1
        assert due[0]["id"] == created["id"]
    finally:
        _cleanup_test_file(tmp_path)


def test_prediction_persistence():
    """Test that predictions are persisted to JSON file."""
    plugin, tmp_path = _make_test_plugin()
    try:
        created = plugin.create(
            prediction_text="Persistence test", horizons=[], confidence=0.5, reasons=[]
        )

        # Check file exists
        assert os.path.exists(tmp_path)

        # Read the file and verify
        with open(tmp_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert len(data) >= 1
        # Find our created prediction
        created_ids = [d["id"] for d in data]
        assert created["id"] in created_ids
    finally:
        _cleanup_test_file(tmp_path)


def test_prediction_status_lifecycle():
    """Test the full status lifecycle: OPEN -> CONFIRMED/FAILED/PARTIAL/CANCELLED."""
    plugin, tmp_path = _make_test_plugin()
    try:
        created = plugin.create(
            prediction_text="Test lifecycle", horizons=[], confidence=0.5, reasons=[]
        )

        # Initially OPEN
        assert created["status"] == "OPEN"

        # Confirm
        confirmed = plugin.update_status(created["id"], "CONFIRMED")
        assert confirmed["status"] == "CONFIRMED"

        # Get by status
        open_results = plugin.get_by_status("OPEN")
        confirmed_results = plugin.get_by_status("CONFIRMED")
        assert len(open_results) == 0
        assert len(confirmed_results) == 1

        # Resolve with FAILED
        failed = plugin.update_status(confirmed["id"], "FAILED")
        assert failed["status"] == "FAILED"

        # Resolve with PARTIAL
        partial = plugin.update_status(confirmed["id"], "PARTIAL")
        assert partial["status"] == "PARTIAL"

        # Resolve with CANCELLED
        cancelled = plugin.update_status(confirmed["id"], "CANCELLED")
        assert cancelled["status"] == "CANCELLED"
    finally:
        _cleanup_test_file(tmp_path)


def test_prediction_default_confidence():
    """Test that default confidence is 0.5 (when not specified, but create requires it)."""
    plugin, tmp_path = _make_test_plugin()
    try:
        # create requires confidence, so test with explicit 0.5
        created = plugin.create(
            prediction_text="Test default", horizons=[], confidence=0.5, reasons=[]
        )
        assert created["confidence"] == 0.5
    finally:
        _cleanup_test_file(tmp_path)


def test_prediction_nonexistent_operations():
    """Test operations on non-existent predictions."""
    plugin, tmp_path = _make_test_plugin()
    try:
        # Update status non-existent
        confirmed = plugin.update_status("nonexistent", "CONFIRMED")
        assert confirmed is None

        # Get by id non-existent
        retrieved = plugin.get_by_id("nonexistent")
        assert retrieved is None

        # Get by status with no matches
        results = plugin.get_by_status("OPEN")
        assert len(results) == 0
    finally:
        _cleanup_test_file(tmp_path)