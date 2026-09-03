# tests/services/test_decision.py - DecisionPlugin Tests
# Golden master: all 354 existing tests must pass unchanged


import os
import sys
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "app"))

from app.services.plugins.decision import DecisionPlugin


def _make_test_plugin():
    """Create a DecisionPlugin with a temporary storage file for test isolation."""
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    tmp.close()
    return DecisionPlugin(storage_path=tmp.name), tmp.name


def _cleanup_test_file(path):
    """Clean up temporary test file."""
    try:
        os.unlink(path)
    except Exception:
        pass


def test_decision_create_basic():
    """Test basic decision creation."""
    plugin, tmp_path = _make_test_plugin()
    try:
        result = plugin.create(
            problem="Should we migrate to SQLite?",
            arguments=["Yes, for FTS5 search", "No, keep JSON only"],
            decision="Yes, migrate to SQLite",
            rationale="FTS5 search requires SQLite backend for performance",
            confidence=0.85,
        )
        assert result["id"] is not None
        assert result["problem"] == "Should we migrate to SQLite?"
        assert result["arguments"] == ["Yes, for FTS5 search", "No, keep JSON only"]
        assert result["decision"] == "Yes, migrate to SQLite"
        assert result["rationale"] == "FTS5 search requires SQLite backend for performance"
        assert result["status"] == "OPEN"
        assert result["confidence"] == 0.85
        assert result["related_memory_ids"] == []
        assert result["outcome"] is None
        assert result["learning"] is None
    finally:
        _cleanup_test_file(tmp_path)


def test_decision_create_with_empty_args():
    """Test decision creation with empty arguments."""
    plugin, tmp_path = _make_test_plugin()
    try:
        result = plugin.create(
            problem="Choose a color",
            arguments=[],
            decision="Blue",
            rationale="Blue is the best color",
        )
        assert result["status"] == "OPEN"
        assert len(result["arguments"]) == 0
    finally:
        _cleanup_test_file(tmp_path)


def test_decision_confirm():
    """Test decision confirmation."""
    plugin, tmp_path = _make_test_plugin()
    try:
        # Create first
        created = plugin.create(
            problem="Test problem",
            arguments=["A", "B"],
            decision="A",
            rationale="Choose A",
        )
        decision_id = created["id"]

        # Confirm it
        confirmed = plugin.confirm(
            decision_id=decision_id,
            outcome="Migrated successfully",
            learning="Migration was smoother than expected",
        )
        assert confirmed is not None
        assert confirmed["status"] == "CONFIRMED"
        assert confirmed["outcome"] == "Migrated successfully"
        assert confirmed["learning"] == "Migration was smoother than expected"
    finally:
        _cleanup_test_file(tmp_path)


def test_decision_confirm_already_confirmed():
    """Test confirming an already confirmed decision."""
    plugin, tmp_path = _make_test_plugin()
    try:
        created = plugin.create(
            problem="Test", arguments=["A"], decision="A", rationale="R",
        )
        confirmed1 = plugin.confirm(
            decision_id=created["id"],
            outcome="Outcome 1",
            learning="Learning 1",
        )
        assert confirmed1["status"] == "CONFIRMED"

        # Confirm again - should stay CONFIRMED
        confirmed2 = plugin.confirm(
            decision_id=created["id"],
            outcome="Outcome 2",
            learning="Learning 2",
        )
        assert confirmed2["status"] == "CONFIRMED"
    finally:
        _cleanup_test_file(tmp_path)


def test_decision_get_by_status():
    """Test getting decisions by status."""
    plugin, tmp_path = _make_test_plugin()
    try:
        # Create decisions with different statuses
        # All start as OPEN
        d1 = plugin.create(problem="P1", arguments=["A"], decision="A", rationale="R1")
        d2 = plugin.create(problem="P2", arguments=["B"], decision="B", rationale="R2")

        open_decisions = plugin.get_by_status("OPEN")
        assert len(open_decisions) == 2

        # Confirm one
        plugin.confirm(
            decision_id=d1["id"],
            outcome="Outcome",
            learning="Learning",
        )

        open_decisions = plugin.get_by_status("OPEN")
        assert len(open_decisions) == 1
        assert open_decisions[0]["id"] == d2["id"]

        confirmed_decisions = plugin.get_by_status("CONFIRMED")
        assert len(confirmed_decisions) == 1
        assert confirmed_decisions[0]["id"] == d1["id"]
    finally:
        _cleanup_test_file(tmp_path)


def test_decision_get_by_id():
    """Test getting a decision by ID."""
    plugin, tmp_path = _make_test_plugin()
    try:
        created = plugin.create(
            problem="Test", arguments=["A"], decision="A", rationale="R",
        )
        retrieved = plugin.get_by_id(created["id"])
        assert retrieved is not None
        assert retrieved["id"] == created["id"]
        assert retrieved["problem"] == "Test"

        # Non-existent ID
        none_result = plugin.get_by_id("nonexistent-id")
        assert none_result is None
    finally:
        _cleanup_test_file(tmp_path)


def test_decision_list_all():
    """Test listing all decisions."""
    plugin, tmp_path = _make_test_plugin()
    try:
        # Create 3 decisions
        d1 = plugin.create(problem="P1", arguments=["A"], decision="A", rationale="R1")
        d2 = plugin.create(problem="P2", arguments=["B"], decision="B", rationale="R2")
        d3 = plugin.create(problem="P3", arguments=["C"], decision="C", rationale="R3")

        all_decisions = plugin.list_all()
        assert len(all_decisions) == 3
    finally:
        _cleanup_test_file(tmp_path)


def test_decision_link_memory():
    """Test linking memory to decision."""
    plugin, tmp_path = _make_test_plugin()
    try:
        created = plugin.create(
            problem="Test", arguments=["A"], decision="A", rationale="R",
        )

        plugin.link_memory(
            decision_id=created["id"],
            memory_id="mem_test_123",
            relation_type="supports",
        )

        # Verify by getting the decision
        retrieved = plugin.get_by_id(created["id"])
        assert "mem_test_123" in retrieved["related_memory_ids"]
        assert retrieved["related_memory_ids"].count("mem_test_123") == 1
    finally:
        _cleanup_test_file(tmp_path)


def test_decision_link_same_memory_twice():
    """Test linking the same memory twice (should not duplicate)."""
    plugin, tmp_path = _make_test_plugin()
    try:
        created = plugin.create(
            problem="Test", arguments=["A"], decision="A", rationale="R",
        )

        plugin.link_memory(
            decision_id=created["id"],
            memory_id="mem_test_123",
            relation_type="supports",
        )
        plugin.link_memory(
            decision_id=created["id"],
            memory_id="mem_test_123",
            relation_type="supports",
        )

        retrieved = plugin.get_by_id(created["id"])
        assert retrieved["related_memory_ids"].count("mem_test_123") == 1
    finally:
        _cleanup_test_file(tmp_path)


def test_decision_update_confidence():
    """Test updating decision confidence."""
    plugin, tmp_path = _make_test_plugin()
    try:
        created = plugin.create(
            problem="Test", arguments=["A"], decision="A", rationale="R",
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


def test_decision_nonexistent_operations():
    """Test operations on non-existent decisions."""
    plugin, tmp_path = _make_test_plugin()
    try:
        # Confirm non-existent
        confirmed = plugin.confirm(
            decision_id="nonexistent",
            outcome="Outcome",
            learning="Learning",
        )
        assert confirmed is None

        # Get by id non-existent
        retrieved = plugin.get_by_id("nonexistent")
        assert retrieved is None

        # Get by status with no matches
        results = plugin.get_by_status("OPEN")
        assert len(results) == 0
    finally:
        _cleanup_test_file(tmp_path)


def test_decision_persistence():
    """Test that decisions are persisted to JSON file."""
    plugin, tmp_path = _make_test_plugin()
    try:
        created = plugin.create(
            problem="Persistence test", arguments=["A"], decision="A", rationale="R",
        )

        # Check file exists
        assert os.path.exists(tmp_path)

        # Read the file and verify
        with open(tmp_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert len(data) >= 1
        # Find our created decision
        created_ids = [d["id"] for d in data]
        assert created["id"] in created_ids
    finally:
        _cleanup_test_file(tmp_path)


def test_decision_status_lifecycle():
    """Test the full status lifecycle: OPEN -> CONFIRMED."""
    plugin, tmp_path = _make_test_plugin()
    try:
        created = plugin.create(
            problem="Test lifecycle", arguments=["A"], decision="A", rationale="R",
        )

        # Initially OPEN
        assert created["status"] == "OPEN"

        # Confirm
        confirmed = plugin.confirm(
            decision_id=created["id"],
            outcome="Success",
            learning="Learned something",
        )
        assert confirmed["status"] == "CONFIRMED"

        # Get by status
        open_results = plugin.get_by_status("OPEN")
        confirmed_results = plugin.get_by_status("CONFIRMED")
        assert len(open_results) == 0
        assert len(confirmed_results) == 1
    finally:
        _cleanup_test_file(tmp_path)


def test_decision_default_confidence():
    """Test that default confidence is 0.7."""
    plugin, tmp_path = _make_test_plugin()
    try:
        created = plugin.create(
            problem="Test default", arguments=["A"], decision="A", rationale="R",
            # Not specifying confidence - should default to 0.7
        )
        # The create method default is 0.7, but if not passed, Python uses the default
        # Actually, since we're not passing it, let's check
        assert created["confidence"] == 0.7
    finally:
        _cleanup_test_file(tmp_path)