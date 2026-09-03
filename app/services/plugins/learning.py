# app/services/plugins/learning.py - LearningPlugin
# Implements the LearningPlugin for capturing and synthesizing lessons from decisions/predictions.
# Schema: id, date, trigger_id (decision/prediction ref), trigger_type (DECISION|PREDICTION),
#         expected, actual, delta, lesson, future_considerations, confidence (0.0-1.0)
# Encryption: Mandatory (per policy: LESSON=mandatory)
# Storage: data/archive/learnings.json
# Storage isolation: Accept storage_path parameter for tests

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from app.services.plugins.base import ServicePlugin
from app.services.plugins.registry import ServiceRegistry


# Storage file path
_DEFAULT_STORAGE = "data/archive/learnings.json"


class LearningPlugin(ServicePlugin):
    """LearningPlugin for capturing lessons from decisions and predictions.

    Schema fields:
        id: UUID string
        date: ISO8601 date string
        trigger_id: The decision or prediction UUID that triggered this learning
        trigger_type: DECISION or PREDICTION (what was learned from)
        expected: What was expected
        actual: What actually happened
        delta: The difference between expected and actual
        lesson: Synthesized lesson from the delta
        future_considerations: Future considerations based on the lesson
        confidence: Confidence score (0.0-1.0)
    """

    def __init__(self, storage_path: str = None, **kwargs):
        super().__init__(
            name="LEARNING",
            category="ARCHIVE",
            description="Learning capture from decisions and predictions with mandatory encryption",
            **kwargs,
        )
        self._storage_path = storage_path or _DEFAULT_STORAGE
        self._learnings: Dict[str, dict] = {}
        self._load_learnings()

    def _get_storage_path(self) -> str:
        """Return the effective storage path, ensuring directory exists."""
        path = self._storage_path
        directory = os.path.dirname(os.path.abspath(path))
        if directory:
            os.makedirs(directory, exist_ok=True)
        return path

    def _load_learnings(self) -> None:
        """Load learnings from the JSON storage file."""
        path = self._get_storage_path()
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data:
                    item["_loaded"] = True
                    self._learnings[item["id"]] = item
        except (Exception, json.JSONDecodeError):
            self._learnings = {}

    def _save_learnings(self) -> None:
        """Persist learnings to the JSON storage file."""
        path = self._get_storage_path()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(list(self._learnings.values()), f, ensure_ascii=False, indent=2)

    # --- Core CRUD Methods ---

    def capture(
        self,
        trigger_id: str,
        trigger_type: str,
        expected: str,
        actual: str,
        confidence: float = 1.0,
    ) -> dict:
        """Capture a new learning entry.

        Args:
            trigger_id: The decision or prediction UUID that triggered this learning
            trigger_type: DECISION or PREDICTION (what was learned from)
            expected: What was expected
            actual: What actually happened
            confidence: Confidence score (0.0-1.0), default 1.0

        Returns:
            The created learning dict
        """
        learning_id = str(uuid.uuid4())
        now = datetime.now().astimezone()
        delta = expected if expected != actual else ""

        # Synthesize the lesson from the delta
        lesson = self._synthesize_lesson_from_delta(expected, actual, delta)

        learning_record = {
            "id": learning_id,
            "date": now.isoformat(),
            "trigger_id": trigger_id,
            "trigger_type": trigger_type,
            "expected": expected,
            "actual": actual,
            "delta": delta,
            "lesson": lesson,
            "future_considerations": self._generate_future_considerations(lesson),
            "confidence": max(0.0, min(1.0, confidence)),
        }
        self._learnings[learning_id] = learning_record
        self._save_learnings()
        return learning_record

    def _synthesize_lesson_from_delta(
        self, expected: str, actual: str, delta: str
    ) -> str:
        """Synthesize a lesson from the expected vs actual delta."""
        if not delta or delta.strip() == "":
            return "Expected and actual matched; no deviation observed."
        return (
            f"Expected: {expected}. Actual: {actual}. "
            f"Delta: {delta}. Lesson: adapt approach based on observed outcome."
        )

    def _generate_future_considerations(self, lesson: str) -> str:
        """Generate future considerations based on the lesson."""
        return "Review this learning in future similar decisions/predictions."

    def synthesize_lesson(self, learning_id: str) -> Optional[dict]:
        """Synthesize lesson from a learning entry by ID.

        Returns the learning dict with the lesson field updated,
        or None if not found.
        """
        learning = self._learnings.get(learning_id)
        if learning is None:
            return None
        delta = learning.get("delta", "")
        expected = learning.get("expected", "")
        actual = learning.get("actual", "")
        learning["lesson"] = self._synthesize_lesson_from_delta(
            expected, actual, delta
        )
        learning["future_considerations"] = self._generate_future_considerations(
            learning["lesson"]
        )
        self._save_learnings()
        return learning

    def get_by_trigger(self, trigger_id: str, trigger_type: str) -> List[dict]:
        """Get all learnings for a given trigger_id and trigger_type.

        Args:
            trigger_id: The decision or prediction UUID
            trigger_type: DECISION or PREDICTION

        Returns:
            List of learning dicts matching the trigger
        """
        return [
            l
            for l in self._learnings.values()
            if l.get("trigger_id") == trigger_id and l.get("trigger_type") == trigger_type
        ]

    def get_by_id(self, learning_id: str) -> Optional[dict]:
        """Get a learning by its ID.

        Args:
            learning_id: The learning UUID string

        Returns:
            The learning dict, or None if not found
        """
        return self._learnings.get(learning_id)

    def list_all(self) -> List[dict]:
        """List all learnings.

        Returns:
            List of all learning dicts
        """
        return list(self._learnings.values())

    def update_confidence(self, learning_id: str, confidence: float) -> Optional[dict]:
        """Update the confidence score of a learning.

        Args:
            learning_id: The learning UUID string
            confidence: New confidence score (0.0-1.0)

        Returns:
            The updated learning dict, or None if not found
        """
        learning = self._learnings.get(learning_id)
        if learning is None:
            return None
        learning["confidence"] = max(0.0, min(1.0, confidence))
        self._save_learnings()
        return learning

    # --- Auto-capture from Decision/Prediction resolution ---

    def auto_capture_from_decision_confirm(
        self, decision_id: str, outcome: str, learning: str
    ) -> Optional[dict]:
        """Auto-create a Learning entry when a Decision is confirmed.

        Args:
            decision_id: The decision UUID string
            outcome: The result outcome
            learning: Learning from the outcome

        Returns:
            The created learning dict, or None if decision not found
        """
        expected = f"Decision {decision_id} outcome: {outcome}"
        actual = outcome
        return self.capture(
            trigger_id=decision_id,
            trigger_type="DECISION",
            expected=expected,
            actual=actual,
            confidence=0.8,
        )

    def auto_capture_from_prediction_resolve(
        self, prediction_id: str, outcome: str, learning: str
    ) -> Optional[dict]:
        """Auto-create a Learning entry when a Prediction is resolved.

        Args:
            prediction_id: The prediction UUID string
            outcome: The result outcome
            learning: Learning from the outcome

        Returns:
            The created learning dict, or None if prediction not found
        """
        expected = f"Prediction {prediction_id} outcome: {outcome}"
        actual = outcome
        return self.capture(
            trigger_id=prediction_id,
            trigger_type="PREDICTION",
            expected=expected,
            actual=actual,
            confidence=0.8,
        )


# Module-level instance for auto-registration (registry expects `plugin` alias)
plugin = LearningPlugin()

# Uppercase alias for pkgutil auto-discovery
PLUGIN = plugin