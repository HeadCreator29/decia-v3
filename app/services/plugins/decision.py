# app/services/plugins/decision.py - DecisionPlugin
# Implements the DecisionPlugin for structured decision logging.
# Schema: id, date, problem, arguments[], decision, rationale, outcome, learning, status (OPEN|CONFIRMED|FAILED|PARTIAL|CANCELLED),
#         related_memory_ids[], confidence (0.0-1.0)
# Encryption: Optional (per policy: DECISION=optional)

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from app.services.plugins.base import ServicePlugin
from app.services.plugins.registry import ServiceRegistry

# Storage file path
_DECISIONS_FILE = "data/archive/decisions.json"


class DecisionPlugin(ServicePlugin):
    """DecisionPlugin for structured decision logging.

    Schema fields:
        id: UUID string
        date: ISO8601 date string
        problem: The decision problem statement
        arguments: List of alternative arguments/options
        decision: The chosen decision
        rationale: Rationale for the choice
        outcome: Result outcome (filled on confirmation)
        learning: Learning from the outcome
        status: OPEN | CONFIRMED | FAILED | PARTIAL | CANCELLED
        related_memory_ids: List of memory IDs linked to this decision
        confidence: Confidence score (0.0-1.0)
    """

    def __init__(self, storage_path: str = None, **kwargs):
        super().__init__(
            name="DECISION",
            category="ARCHIVE",
            description="Structured decision logging with status lifecycle",
            **kwargs,
        )
        self._storage_path = storage_path or _DECISIONS_FILE
        self._decisions: Dict[str, dict] = {}
        self._load_decisions()

    def _load_decisions(self) -> None:
        """Load decisions from the JSON storage file."""
        try:
            if os.path.exists(self._storage_path):
                with open(self._storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data:
                    item["_loaded"] = True
                    self._decisions[item["id"]] = item
        except Exception:
            self._decisions = {}

    def _save_decisions(self) -> None:
        """Persist decisions to the JSON storage file."""
        os.makedirs(os.path.dirname(self._storage_path), exist_ok=True)
        with open(self._storage_path, "w", encoding="utf-8") as f:
            json.dump(list(self._decisions.values()), f, ensure_ascii=False, indent=2)

    # --- Core CRUD Methods ---

    def create(
        self,
        problem: str,
        arguments: List[str],
        decision: str,
        rationale: str,
        confidence: float = 0.7,
    ) -> dict:
        """Create a new decision with status OPEN.

        Args:
            problem: The decision problem statement
            arguments: List of alternative arguments/options
            decision: The chosen decision
            rationale: Rationale for the choice
            confidence: Initial confidence score (0.0-1.0), default 0.7

        Returns:
            The created decision dict
        """
        decision_id = str(uuid.uuid4())
        now = datetime.now().astimezone()
        decision_record = {
            "id": decision_id,
            "date": now.isoformat(),
            "problem": problem,
            "arguments": arguments,
            "decision": decision,
            "rationale": rationale,
            "outcome": None,
            "learning": None,
            "status": "OPEN",
            "related_memory_ids": [],
            "confidence": confidence,
        }
        self._decisions[decision_id] = decision_record
        self._save_decisions()
        return decision_record

    def confirm(
        self, decision_id: str, outcome: str, learning: str
    ) -> Optional[dict]:
        """Confirm a decision, transitioning status.

        Args:
            decision_id: The decision UUID string
            outcome: The result outcome
            learning: Learning from the outcome

        Returns:
            The updated decision dict, or None if not found
        """
        decision = self._decisions.get(decision_id)
        if decision is None:
            return None
        decision["outcome"] = outcome
        decision["learning"] = learning
        # Transition from OPEN to CONFIRMED (or keep as-is if already confirmed)
        if decision["status"] == "OPEN":
            decision["status"] = "CONFIRMED"
        self._save_decisions()
        return decision

    def get_by_status(self, status: str) -> List[dict]:
        """Get all decisions with the given status.

        Args:
            status: Filter status (OPEN, CONFIRMED, FAILED, PARTIAL, CANCELLED)

        Returns:
            List of decision dicts matching the status
        """
        return [
            d
            for d in self._decisions.values()
            if d.get("status") == status
        ]

    def get_by_id(self, decision_id: str) -> Optional[dict]:
        """Get a decision by its ID.

        Args:
            decision_id: The decision UUID string

        Returns:
            The decision dict, or None if not found
        """
        return self._decisions.get(decision_id)

    def list_all(self) -> List[dict]:
        """List all decisions.

        Returns:
            List of all decision dicts
        """
        return list(self._decisions.values())

    # --- Memory Linking ---

    def link_memory(
        self, decision_id: str, memory_id: str, relation_type: str
    ) -> None:
        """Link a memory to a decision with a relation type.

        Args:
            decision_id: The decision UUID string
            memory_id: The memory UUID string
            relation_type: Relation type (relates-to | supports | contradicts | supersedes)
        """
        decision = self._decisions.get(decision_id)
        if decision is None:
            return
        if memory_id not in decision.get("related_memory_ids", []):
            decision.setdefault("related_memory_ids", []).append(memory_id)
        self._save_decisions()

    # --- Confidence Update ---

    def update_confidence(self, decision_id: str, confidence: float) -> Optional[dict]:
        """Update the confidence score of a decision.

        Args:
            decision_id: The decision UUID string
            confidence: New confidence score (0.0-1.0)

        Returns:
            The updated decision dict, or None if not found
        """
        decision = self._decisions.get(decision_id)
        if decision is None:
            return None
        decision["confidence"] = max(0.0, min(1.0, confidence))
        self._save_decisions()
        return decision


# Module-level instance for auto-registration (registry expects `plugin` alias)
plugin = DecisionPlugin()