# app/services/plugins/prediction.py - PredictionPlugin
# Implements the PredictionPlugin for structured prediction logging.
# Schema: id, date, prediction_text, horizons[{label, timeframe, target_date}],
#         confidence (0.0-1.0), reasons[], status (OPEN|CONFIRMED|FAILED|PARTIAL|CANCELLED),
#         review_date, outcome, learning, related_memory_ids[], related_decision_ids[]
# Encryption: Optional (per policy: PREDICTION=optional)
# Storage: data/archive/predictions.json

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from app.services.plugins.base import ServicePlugin
from app.services.plugins.registry import ServiceRegistry

# Storage file path
_PREDICTIONS_FILE = "data/archive/predictions.json"


class PredictionPlugin(ServicePlugin):
    """PredictionPlugin for structured prediction logging with multi-horizon support.

    Schema fields:
        id: UUID string
        date: ISO8601 date string
        prediction_text: The prediction statement
        horizons: List of horizon dicts with {label, timeframe, target_date}
        confidence: Initial confidence score (0.0-1.0)
        reasons: List of reason strings
        status: OPEN | CONFIRMED | FAILED | PARTIAL | CANCELLED
        review_date: ISO8601 date string for review scheduling
        outcome: Result outcome (filled on resolution)
        learning: Learning from the outcome
        related_memory_ids: List of memory IDs linked to this prediction
        related_decision_ids: List of decision IDs linked to this prediction
    """

    def __init__(self, storage_path: str = None, **kwargs):
        super().__init__(
            name="PREDICTION",
            category="ARCHIVE",
            description="Structured prediction logging with status lifecycle",
            **kwargs,
        )
        self._storage_path = storage_path or _PREDICTIONS_FILE
        self._predictions: Dict[str, dict] = {}
        self._load_predictions()

    def _load_predictions(self) -> None:
        """Load predictions from the JSON storage file."""
        try:
            if os.path.exists(self._storage_path):
                with open(self._storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data:
                    item["_loaded"] = True
                    self._predictions[item["id"]] = item
        except Exception:
            self._predictions = {}

    def _save_predictions(self) -> None:
        """Persist predictions to the JSON storage file."""
        os.makedirs(os.path.dirname(self._storage_path), exist_ok=True)
        with open(self._storage_path, "w", encoding="utf-8") as f:
            json.dump(list(self._predictions.values()), f, ensure_ascii=False, indent=2)

    # --- Core CRUD Methods ---

    def create(
        self,
        prediction_text: str,
        horizons: List[dict],
        confidence: float,
        reasons: List[str],
    ) -> dict:
        """Create a new prediction with status OPEN.

        Args:
            prediction_text: The prediction statement
            horizons: List of horizon dicts with {label, timeframe, target_date}
            confidence: Initial confidence score (0.0-1.0)
            reasons: List of reason strings

        Returns:
            The created prediction dict
        """
        prediction_id = str(uuid.uuid4())
        now = datetime.now().astimezone()
        prediction_record = {
            "id": prediction_id,
            "date": now.isoformat(),
            "prediction_text": prediction_text,
            "horizons": horizons or [],
            "confidence": confidence,
            "reasons": reasons or [],
            "status": "OPEN",
            "review_date": None,
            "outcome": None,
            "learning": None,
            "related_memory_ids": [],
            "related_decision_ids": [],
        }
        self._predictions[prediction_id] = prediction_record
        self._save_predictions()
        return prediction_record

    def update_status(
        self, prediction_id: str, status: str
    ) -> Optional[dict]:
        """Update the status of a prediction.

        Args:
            prediction_id: The prediction UUID string
            status: New status (OPEN|CONFIRMED|FAILED|PARTIAL|CANCELLED)

        Returns:
            The updated prediction dict, or None if not found
        """
        prediction = self._predictions.get(prediction_id)
        if prediction is None:
            return None
        prediction["status"] = status
        self._save_predictions()
        return prediction

    def schedule_review(
        self, prediction_id: str, review_date: str
    ) -> Optional[dict]:
        """Schedule a review date for a prediction.

        Args:
            prediction_id: The prediction UUID string
            review_date: ISO8601 date string for the review

        Returns:
            The updated prediction dict, or None if not found
        """
        prediction = self._predictions.get(prediction_id)
        if prediction is None:
            return None
        prediction["review_date"] = review_date
        self._save_predictions()
        return prediction

    def get_due_reviews(self) -> List[dict]:
        """Get predictions due for review.

        Returns predictions where review_date <= now and status=OPEN
        for background scheduler.

        Returns:
            List of prediction dicts due for review
        """
        from datetime import datetime as _dt

        now = _dt.now()
        due = []
        for pred in self._predictions.values():
            if (
                pred.get("status") == "OPEN"
                and pred.get("review_date")
            ):
                try:
                    review_date = _dt.fromisoformat(pred["review_date"])
                    # Compare naive datetimes (both without timezone)
                    if review_date <= now:
                        due.append(pred)
                except Exception:
                    pass
        return due

    def get_by_status(self, status: str) -> List[dict]:
        """Get all predictions with the given status.

        Args:
            status: Filter status (OPEN, CONFIRMED, FAILED, PARTIAL, CANCELLED)

        Returns:
            List of prediction dicts matching the status
        """
        return [
            p
            for p in self._predictions.values()
            if p.get("status") == status
        ]

    def get_by_id(self, prediction_id: str) -> Optional[dict]:
        """Get a prediction by its ID.

        Args:
            prediction_id: The prediction UUID string

        Returns:
            The prediction dict, or None if not found
        """
        return self._predictions.get(prediction_id)

    def list_all(self) -> List[dict]:
        """List all predictions.

        Returns:
            List of all prediction dicts
        """
        return list(self._predictions.values())

    # --- Resolution ---

    def resolve(
        self, prediction_id: str, outcome: str, learning: str
    ) -> Optional[dict]:
        """Resolve a prediction with outcome and learning.

        Transitions status: OPEN → CONFIRMED/FAILED/PARTIAL/CANCELLED

        Args:
            prediction_id: The prediction UUID string
            outcome: The result outcome
            learning: Learning from the outcome

        Returns:
            The updated prediction dict, or None if not found
        """
        prediction = self._predictions.get(prediction_id)
        if prediction is None:
            return None

        prediction["outcome"] = outcome
        prediction["learning"] = learning

        status = prediction["status"]
        if status == "OPEN":
            # Determine status based on outcome nature
            if outcome and outcome.lower().startswith("failed"):
                prediction["status"] = "FAILED"
            elif outcome and outcome.lower().startswith("cancel"):
                prediction["status"] = "CANCELLED"
            else:
                prediction["status"] = "CONFIRMED"
        self._save_predictions()
        return prediction

    # --- Memory/Decision Linking ---

    def link_memory(
        self, prediction_id: str, memory_id: str, relation_type: str
    ) -> None:
        """Link a memory to a prediction with a relation type.

        Args:
            prediction_id: The prediction UUID string
            memory_id: The memory UUID string
            relation_type: Relation type (relates-to | supports | contradicts | supersedes)
        """
        prediction = self._predictions.get(prediction_id)
        if prediction is None:
            return
        memory_ids = prediction.setdefault("related_memory_ids", [])
        if memory_id not in memory_ids:
            memory_ids.append(memory_id)
        self._save_predictions()

    def link_decision(
        self, prediction_id: str, decision_id: str, relation_type: str
    ) -> None:
        """Link a decision to a prediction with a relation type.

        Args:
            prediction_id: The prediction UUID string
            decision_id: The decision UUID string
            relation_type: Relation type (relates-to | supports | contradicts | supersedes)
        """
        prediction = self._predictions.get(prediction_id)
        if prediction is None:
            return
        decision_ids = prediction.setdefault("related_decision_ids", [])
        if decision_id not in decision_ids:
            decision_ids.append(decision_id)
        self._save_predictions()

    # --- Confidence Update ---

    def update_confidence(
        self, prediction_id: str, confidence: float
    ) -> Optional[dict]:
        """Update the confidence score of a prediction.

        Args:
            prediction_id: The prediction UUID string
            confidence: New confidence score (0.0-1.0)

        Returns:
            The updated prediction dict, or None if not found
        """
        prediction = self._predictions.get(prediction_id)
        if prediction is None:
            return None
        prediction["confidence"] = max(0.0, min(1.0, confidence))
        self._save_predictions()
        return prediction


# Module-level instance for auto-registration (registry expects `plugin` alias)
plugin = PredictionPlugin()