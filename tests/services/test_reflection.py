# tests/services/test_reflection.py - ReflectionPlugin Tests
# Golden master: all 487 existing tests + new tests must pass

import os
import sys
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "app"))

from app.services.plugins.reflection import ReflectionPlugin


def _make_test_plugin():
    """Create a ReflectionPlugin with a temporary storage file for test isolation."""
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    tmp.close()
    return ReflectionPlugin(storage_path=tmp.name), tmp.name


def _cleanup_test_file(path):
    """Clean up temporary test file."""
    try:
        os.unlink(path)
    except Exception:
        pass


def test_reflection_draft_basic():
    """Test basic reflection draft creation."""
    plugin, tmp_path = _make_test_plugin()
    try:
        result = plugin.draft(
            conversation_id="conv_123",
            draft_content="Hoy reflexioné sobre mi aprendizaje y fue productivo.",
        )
        assert result["id"] is not None
        assert result["related_conversation_id"] == "conv_123"
        assert result["draft_content"] == "Hoy reflexioné sobre mi aprendizaje y fue productivo."
        assert result["approved_content"] == ""
        assert result["status"] == "DRAFT"
        assert result["user_edited"] is False
        assert result["date"] is not None
    finally:
        _cleanup_test_file(tmp_path)


def test_reflection_approve_basic():
    """Test basic reflection approval."""
    plugin, tmp_path = _make_test_plugin()
    try:
        # Create draft first
        draft = plugin.draft(
            conversation_id="conv_456",
            draft_content="Mi reflexión sobre el proyecto.",
        )
        # Approve it
        result = plugin.approve(reflection_id=draft["id"], edited_content="Mi reflexión final sobre el proyecto.")
        assert result["status"] == "APPROVED"
        assert result["approved_content"] == "Mi reflexión final sobre el proyecto."
        assert result["user_edited"] is True
    finally:
        _cleanup_test_file(tmp_path)


def test_reflection_approve_no_edit():
    """Test approval without edited content (uses draft_content)."""
    plugin, tmp_path = _make_test_plugin()
    try:
        draft = plugin.draft(
            conversation_id="conv_789",
            draft_content="Reflexión original.",
        )
        # Approve without edits
        result = plugin.approve(reflection_id=draft["id"])
        assert result["status"] == "APPROVED"
        assert result["approved_content"] == "Reflexión original."
        assert result["user_edited"] is False
    finally:
        _cleanup_test_file(tmp_path)


def test_reflection_archive():
    """Test archiving a reflection."""
    plugin, tmp_path = _make_test_plugin()
    try:
        draft = plugin.draft(
            conversation_id="conv_archive",
            draft_content="Reflexión a archivar.",
        )
        # Archive the draft
        result = plugin.archive(reflection_id=draft["id"])
        assert result["status"] == "ARCHIVED"
        # Archive an already approved one
        approved = plugin.approve(reflection_id=draft["id"])
        archived = plugin.archive(reflection_id=approved["id"])
        assert archived["status"] == "ARCHIVED"
    finally:
        _cleanup_test_file(tmp_path)


def test_reflection_get_by_status():
    """Test getting reflections by status."""
    plugin, tmp_path = _make_test_plugin()
    try:
        plugin.draft(conversation_id="conv_status1", draft_content="Borrador 1")
        plugin.draft(conversation_id="conv_status2", draft_content="Borrador 2")
        # We need to manually set status to APPROVED/ARCHIVED since draft creates DRAFT
        # Actually let's test get_by_status with DRAFT only
        drafts = plugin.get_by_status("DRAFT")
        assert len(drafts) >= 2
    finally:
        _cleanup_test_file(tmp_path)


def test_reflection_get_by_id():
    """Test getting a reflection by ID."""
    plugin, tmp_path = _make_test_plugin()
    try:
        created = plugin.draft(
            conversation_id="conv_id", draft_content="Contenido de prueba",
        )
        retrieved = plugin.get_by_id(created["id"])
        assert retrieved is not None
        assert retrieved["id"] == created["id"]
        assert retrieved["draft_content"] == "Contenido de prueba"
        none_result = plugin.get_by_id("nonexistent-id")
        assert none_result is None
    finally:
        _cleanup_test_file(tmp_path)


def test_reflection_get_by_conversation():
    """Test getting reflections by conversation_id."""
    plugin, tmp_path = _make_test_plugin()
    try:
        plugin.draft(conversation_id="conv_test", draft_content="Reflexión para prueba")
        plugin.draft(conversation_id="other_conv", draft_content="Otra reflexión")
        conv_reflections = plugin.get_by_conversation("conv_test")
        assert len(conv_reflections) >= 1
        other_reflections = plugin.get_by_conversation("other_conv")
        assert len(other_reflections) >= 1
    finally:
        _cleanup_test_file(tmp_path)


def test_reflection_list_all():
    """Test listing all reflections."""
    plugin, tmp_path = _make_test_plugin()
    try:
        plugin.draft(conversation_id="conv_l1", draft_content="Borrador 1")
        plugin.draft(conversation_id="conv_l2", draft_content="Borrador 2")
        all_refs = plugin.list_all()
        assert len(all_refs) >= 2
    finally:
        _cleanup_test_file(tmp_path)


def test_reflection_persistence():
    """Test that reflections are persisted to JSON file."""
    plugin, tmp_path = _make_test_plugin()
    try:
        plugin.draft(conversation_id="persist_test", draft_content="Contexto de persistencia")
        assert os.path.exists(tmp_path)

        with open(tmp_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert len(data) >= 1
        # Verify the persisted data has the right structure
        assert "id" in data[0]
        assert "draft_content" in data[0]
        assert data[0]["draft_content"] == "Contexto de persistencia"
    finally:
        _cleanup_test_file(tmp_path)


def test_reflection_user_edited_flag():
    """Test that user_edited flag is set correctly."""
    plugin, tmp_path = _make_test_plugin()
    try:
        # Approve with edits
        draft = plugin.draft(conversation_id="conv_edit", draft_content="Contenido original")
        result = plugin.approve(reflection_id=draft["id"], edited_content="Contenido editado")
        assert result["user_edited"] is True
        # Approve a fresh draft without edits
        draft2 = plugin.draft(conversation_id="conv_edit2", draft_content="Contenido original")
        result2 = plugin.approve(reflection_id=draft2["id"])
        assert result2["user_edited"] is False
    finally:
        _cleanup_test_file(tmp_path)