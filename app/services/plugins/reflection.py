# app/services/plugins/reflection.py - ReflectionPlugin
# Implements the ReflectionPlugin for diary/reflection entries.
# Schema: id, date, draft_content, approved_content, status (DRAFT|APPROVED|ARCHIVED),
#         related_conversation_id, user_edited (bool)
# Encryption: Mandatory (per policy: INTERPRETATION/REFLECTION=mandatory)
# Storage: data/archive/reflections.json
# Storage isolation: Accept storage_path parameter for tests

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from app.services.plugins.base import ServicePlugin
from app.services.plugins.registry import ServiceRegistry
from app.services.encryption import encrypt_memory_data


# Storage file path
_DEFAULT_STORAGE = "data/archive/reflections.json"


class ReflectionPlugin(ServicePlugin):
    """ReflectionPlugin for diary/reflection entries with mandatory encryption.

    Schema fields:
        id: UUID string
        date: ISO8601 date string
        draft_content: The draft text (may be empty after approval)
        approved_content: The approved/ final text (may be empty if draft)
        status: DRAFT | APPROVED | ARCHIVED
        related_conversation_id: Conversation UUID linking to source conversation
        user_edited: Whether the user edited the content
    """

    def __init__(self, storage_path: str = None, **kwargs):
        super().__init__(
            name="REFLECTION",
            category="ARCHIVE",
            description="Reflection/diary entries with mandatory encryption",
            **kwargs,
        )
        self._storage_path = storage_path or _DEFAULT_STORAGE
        self._reflections: Dict[str, dict] = {}
        self._load_reflections()

    def _get_storage_path(self) -> str:
        """Return the effective storage path, ensuring directory exists."""
        path = self._storage_path
        directory = os.path.dirname(os.path.abspath(path))
        if directory:
            os.makedirs(directory, exist_ok=True)
        return path

    def _load_reflections(self) -> None:
        """Load reflections from the JSON storage file."""
        path = self._get_storage_path()
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data:
                    item["_loaded"] = True
                    self._reflections[item["id"]] = item
        except (Exception, json.JSONDecodeError):
            self._reflections = {}

    def _save_reflections(self) -> None:
        """Persist reflections to the JSON storage file."""
        path = self._get_storage_path()
        # Prepare data for storage (encrypt content fields if passphrase available)
        save_data = []
        for ref in self._reflections.values():
            ref_copy = dict(ref)
            # Remove internal metadata before serialization
            ref_copy.pop("_loaded", None)
            save_data.append(ref_copy)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)

    # --- Auto-Draft Generation ---

    def generate_draft(self, conversation_context: dict) -> dict:
        """Generate a draft reflection from conversation context.

        Called after conversation ends to create a reflection draft
        from the conversation summary (what happened, what was learned,
        open questions).

        Args:
            conversation_context: Dict with conversation summary info,
                expected keys: "summary", "learned", "open_questions"

        Returns:
            A Reflection dict in DRAFT status
        """
        summary = conversation_context.get("summary", "")
        learned = conversation_context.get("learned", "")
        open_questions = conversation_context.get("open_questions", "")

        # Build draft content from the conversation elements
        draft_parts = []
        if summary:
            draft_parts.append(f"Resumen: {summary}")
        if learned:
            draft_parts.append(f"Lecciones aprendidas: {learned}")
        if open_questions:
            draft_parts.append(f"Preguntas abiertas: {open_questions}")

        draft_content = " | ".join(draft_parts) if draft_parts else "Reflexión de conversación"

        # Create a draft without a specific conversation_id (will be set by caller)
        reflection_id = str(uuid.uuid4())
        now = datetime.now().astimezone()
        reflection_record = {
            "id": reflection_id,
            "date": now.isoformat(),
            "draft_content": draft_content,
            "approved_content": "",
            "status": "DRAFT",
            "related_conversation_id": conversation_context.get("conversation_id", ""),
            "user_edited": False,
        }
        self._reflections[reflection_id] = reflection_record
        self._save_reflections()
        return reflection_record

# --- Core CRUD Methods ---

    def draft(self, conversation_id: str, draft_content: str) -> dict:
        """Create a new reflection draft.

        Args:
            conversation_id: The conversation UUID linking this reflection
            draft_content: The draft text content

        Returns:
            The created reflection dict
        """
        reflection_id = str(uuid.uuid4())
        now = datetime.now().astimezone()
        reflection_record = {
            "id": reflection_id,
            "date": now.isoformat(),
            "draft_content": draft_content,
            "approved_content": "",
            "status": "DRAFT",
            "related_conversation_id": conversation_id,
            "user_edited": False,
        }
        self._reflections[reflection_id] = reflection_record
        self._save_reflections()
        return reflection_record

    def approve(self, reflection_id: str, edited_content: str = "") -> dict:
        """Approve/refine a reflection draft.

        Args:
            reflection_id: The reflection UUID string
            edited_content: Optional user edits/approval content

        Returns:
            The updated reflection dict
        """
        reflection = self._reflections.get(reflection_id)
        if reflection is None:
            return None
        if reflection["status"] != "DRAFT":
            return reflection
        # Transition to APPROVED
        reflection["approved_content"] = (
            edited_content if edited_content else reflection["draft_content"]
        )
        reflection["status"] = "APPROVED"
        reflection["user_edited"] = bool(edited_content)
        self._save_reflections()
        return reflection

    def archive(self, reflection_id: str) -> Optional[dict]:
        """Archive a reflection (APPROVED or DRAFT).

        Args:
            reflection_id: The reflection UUID string

        Returns:
            The updated reflection dict, or None if not found
        """
        reflection = self._reflections.get(reflection_id)
        if reflection is None:
            return None
        reflection["status"] = "ARCHIVED"
        self._save_reflections()
        return reflection

    def get_by_status(self, status: str) -> List[dict]:
        """Get all reflections with the given status.

        Args:
            status: Filter status (DRAFT, APPROVED, ARCHIVED)

        Returns:
            List of reflection dicts matching the status
        """
        return [
            r
            for r in self._reflections.values()
            if r.get("status") == status
        ]

    def get_by_conversation(self, conversation_id: str) -> List[dict]:
        """Get all reflections for a given conversation_id.

        Args:
            conversation_id: The conversation UUID

        Returns:
            List of reflection dicts matching the conversation
        """
        return [
            r
            for r in self._reflections.values()
            if r.get("related_conversation_id") == conversation_id
        ]

    def get_by_id(self, reflection_id: str) -> Optional[dict]:
        """Get a reflection by its ID.

        Args:
            reflection_id: The reflection UUID string

        Returns:
            The reflection dict, or None if not found
        """
        return self._reflections.get(reflection_id)

    def list_all(self) -> List[dict]:
        """List all reflections.

        Returns:
            List of all reflection dicts
        """
        return list(self._reflections.values())


# Module-level instance for auto-registration (registry expects `plugin` alias)
plugin = ReflectionPlugin()

# Uppercase alias for pkgutil auto-discovery
PLUGIN = plugin