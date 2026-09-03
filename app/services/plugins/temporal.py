# app/services/plugins/temporal.py - TemporalPlugin
# Cross-domain temporal queries across all memory types.
# Provides query_by_timerange(domains[], start, end) → fused sorted results.

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

from app.services.plugins.base import ServicePlugin
from app.services.plugins.memory import MemoryPlugin
from app.services.plugins.decision import DecisionPlugin
from app.services.plugins.prediction import PredictionPlugin
from app.services.plugins.learning import LearningPlugin
from app.services.plugins.reflection import ReflectionPlugin
from app.services.plugins.identity_core import IdentityCorePlugin
from app.services.archive import get_history

# Supported domains for temporal queries
TEMPORAL_DOMAINS = [
    "memory",
    "decision",
    "prediction",
    "learning",
    "reflection",
    "identity",
    "event",
]


class TemporalPlugin(ServicePlugin):
    """TemporalPlugin for cross-domain temporal queries.

    Fuses results from multiple memory domains (memory, decision, prediction,
    learning, reflection, identity, event) within a given time range.
    Returns chronologically sorted fused results.
    """

    def __init__(self, **kwargs):
        super().__init__(
            name="TEMPORAL",
            category="ARCHIVE",
            description="Cross-domain temporal queries with fused chronological results",
            **kwargs,
        )
        # Initialize domain plugins
        self._memory_plugin = MemoryPlugin()
        self._decision_plugin = DecisionPlugin()
        self._prediction_plugin = PredictionPlugin()
        self._learning_plugin = LearningPlugin()
        self._reflection_plugin = ReflectionPlugin()
        self._identity_plugin = IdentityCorePlugin()

    def query_by_timerange(
        self,
        domains: List[str],
        start: str,
        end: str,
        limit: int = 50
    ) -> List[Dict]:
        """Query memories across domains within a time range.

        Args:
            domains: List of domain names (memory, decision, prediction, learning, reflection, identity, event)
            start: Start date ISO8601 (inclusive)
            end: End date ISO8601 (inclusive)
            limit: Maximum total results to return

        Returns:
            Fused list of results sorted chronologically (oldest first)
        """
        # Validate domains
        valid_domains = [d for d in domains if d in TEMPORAL_DOMAINS]
        if not valid_domains:
            valid_domains = TEMPORAL_DOMAINS

        fused_results = []

        # Query each domain
        if "memory" in valid_domains:
            fused_results.extend(self._query_memories(start, end))

        if "decision" in valid_domains:
            fused_results.extend(self._query_decisions(start, end))

        if "prediction" in valid_domains:
            fused_results.extend(self._query_predictions(start, end))

        if "learning" in valid_domains:
            fused_results.extend(self._query_learnings(start, end))

        if "reflection" in valid_domains:
            fused_results.extend(self._query_reflections(start, end))

        if "identity" in valid_domains:
            fused_results.extend(self._query_identity(start, end))

        if "event" in valid_domains:
            fused_results.extend(self._query_events(start, end))

        # Sort chronologically
        fused_results.sort(key=lambda x: x.get("date", ""))

        # Apply limit
        return fused_results[:limit]

    def _query_memories(self, start: str, end: str) -> List[Dict]:
        """Query memories within time range."""
        try:
            result = self._memory_plugin.search_by_content(
                plugin=self._memory_plugin,
                query="",
                filters={"date_from": start, "date_to": end}
            )
            return [
                {
                    "date": item.get("date", ""),
                    "type": "memory",
                    "content": item.get("content", ""),
                    "domain": "memory",
                    "id": item.get("id", ""),
                    "confidence": item.get("confidence", 0.7),
                }
                for item in result
            ]
        except Exception:
            return []

    def _query_decisions(self, start: str, end: str) -> List[Dict]:
        """Query decisions within time range."""
        try:
            all_decisions = self._decision_plugin.list_all()
            results = []
            for d in all_decisions:
                d_date = d.get("date", "")
                if start <= d_date <= end:
                    results.append({
                        "date": d_date,
                        "type": "decision",
                        "content": f"Decisión: {d.get('decision', '')} — {d.get('rationale', '')}",
                        "domain": "decision",
                        "id": d.get("id", ""),
                        "status": d.get("status", "OPEN"),
                    })
            return results
        except Exception:
            return []

    def _query_predictions(self, start: str, end: str) -> List[Dict]:
        """Query predictions within time range."""
        try:
            all_predictions = self._prediction_plugin.list_all()
            results = []
            for p in all_predictions:
                p_date = p.get("date", "")
                if start <= p_date <= end:
                    results.append({
                        "date": p_date,
                        "type": "prediction",
                        "content": f"Predicción: {p.get('prediction_text', '')}",
                        "domain": "prediction",
                        "id": p.get("id", ""),
                        "status": p.get("status", "OPEN"),
                        "horizons": p.get("horizons", []),
                    })
            return results
        except Exception:
            return []

    def _query_learnings(self, start: str, end: str) -> List[Dict]:
        """Query learnings within time range."""
        try:
            all_learnings = self._learning_plugin.list_all()
            results = []
            for l in all_learnings:
                l_date = l.get("date", "")
                if start <= l_date <= end:
                    results.append({
                        "date": l_date,
                        "type": "learning",
                        "content": f"Lección: {l.get('lesson', '')}",
                        "domain": "learning",
                        "id": l.get("id", ""),
                        "trigger_id": l.get("trigger_id", ""),
                        "trigger_type": l.get("trigger_type", ""),
                    })
            return results
        except Exception:
            return []

    def _query_reflections(self, start: str, end: str) -> List[Dict]:
        """Query reflections within time range."""
        try:
            all_reflections = self._reflection_plugin.list_all()
            results = []
            for r in all_reflections:
                r_date = r.get("date", "")
                if start <= r_date <= end:
                    content = r.get("approved_content") or r.get("draft_content", "")
                    results.append({
                        "date": r_date,
                        "type": "reflection",
                        "content": f"Reflexión: {content}",
                        "domain": "reflection",
                        "id": r.get("id", ""),
                        "status": r.get("status", "DRAFT"),
                    })
            return results
        except Exception:
            return []

    def _query_identity(self, start: str, end: str) -> List[Dict]:
        """Query identity changes within time range."""
        try:
            identity = self._identity_plugin.get_current()
            audit_log = identity.get("audit_log", [])
            results = []
            for entry in audit_log:
                entry_date = entry.get("date", "")
                if start <= entry_date <= end:
                    results.append({
                        "date": entry_date,
                        "type": "identity",
                        "content": f"Cambio identidad v{entry.get('version', '')}: {entry.get('changes', {})}",
                        "domain": "identity",
                        "id": f"identity_v{entry.get('version', '')}",
                        "approved_by": entry.get("approved_by", ""),
                    })
            return results
        except Exception:
            return []

    def _query_events(self, start: str, end: str) -> List[Dict]:
        """Query history events within time range."""
        try:
            history = get_history()
            events = history.get("events", [])
            results = []
            for e in events:
                e_date = e.get("date", "")
                if start <= e_date <= end:
                    results.append({
                        "date": e_date,
                        "type": "event",
                        "content": f"Evento: {e.get('title', '')} — {e.get('description', '')}",
                        "domain": "event",
                        "id": e.get("id", ""),
                    })
            return results
        except Exception:
            return []

    def get_year_tabs_data(self, years: List[int] = None) -> Dict:
        """Get data for year tabs UI (2026-2035).

        Returns:
            Dict with year as key and count of items per domain as value.
        """
        if years is None:
            years = list(range(2026, 2036))

        year_data = {}
        for year in years:
            start = f"{year}-01-01"
            end = f"{year}-12-31"
            results = self.query_by_timerange(TEMPORAL_DOMAINS, start, end, limit=1000)

            # Count by domain
            counts = {}
            for item in results:
                domain = item.get("domain", "unknown")
                counts[domain] = counts.get(domain, 0) + 1

            year_data[str(year)] = {
                "total": len(results),
                "by_domain": counts,
            }

        return year_data


# Module-level instance for auto-registration
PLUGIN = TemporalPlugin()

# Lowercase alias
plugin = PLUGIN