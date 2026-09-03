# app/services/plugins/context.py - ContextPlugin
# Enriches LLM prompts with relevant history using token budget and relevance ranking.

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.services.plugins.base import ServicePlugin
from app.services.plugins.memory import MemoryPlugin
from app.services.plugins.decision import DecisionPlugin
from app.services.plugins.prediction import PredictionPlugin
from app.services.plugins.learning import LearningPlugin
from app.services.plugins.reflection import ReflectionPlugin
from app.services.plugins.identity_core import IdentityCorePlugin

# Default token budget for context assembly
DEFAULT_TOKEN_BUDGET = 1000

# Type priority weights (higher = more important for context)
TYPE_PRIORITY = {
    "FACT": 1.0,
    "MEMORY": 0.8,
    "DECISION": 0.9,
    "GOAL": 0.7,
    "PREDICTION": 0.7,
    "LESSON": 0.9,
    "INTERPRETATION": 0.6,
    "UNKNOWN": 0.5,
    "identity": 0.9,
    "event": 0.7,
    "reflection": 0.6,
    "learning": 0.8,
    "prediction": 0.7,
    "decision": 0.8,
    "memory": 0.7,
}


class ContextPlugin(ServicePlugin):
    """ContextPlugin for enriching LLM prompts with relevant history.

    Assembles relevant memories into a structured context block for the LLM.
    Enforces token budget with relevance ranking.
    """

    def __init__(self, **kwargs):
        super().__init__(
            name="CONTEXT",
            category="ARCHIVE",
            description="Context assembly for LLM prompts with token budget enforcement",
            **kwargs,
        )
        self._memory_plugin = MemoryPlugin()
        self._decision_plugin = DecisionPlugin()
        self._prediction_plugin = PredictionPlugin()
        self._learning_plugin = LearningPlugin()
        self._reflection_plugin = ReflectionPlugin()
        self._identity_plugin = IdentityCorePlugin()

    def enrich_prompt(
        self,
        intent: str,
        entities: Dict,
        token_budget: int = DEFAULT_TOKEN_BUDGET
    ) -> str:
        """Enrich prompt with relevant history for the given intent.

        Args:
            intent: The classified intent (e.g., MEMORY_CREATE, DECISION_CREATE)
            entities: Extracted entities from the intent
            token_budget: Maximum tokens for the context block (default: 1000)

        Returns:
            Formatted context string within token_budget
        """
        # Collect candidate memories from all domains
        candidates = self._collect_candidates(intent, entities)

        if not candidates:
            return ""

        # Score and rank candidates
        scored = self._score_candidates(candidates, intent)

        # Select within token budget
        selected = self._select_within_budget(scored, token_budget)

        # Format context block
        return self._format_context_block(selected)

    def _collect_candidates(self, intent: str, entities: Dict) -> List[Dict]:
        """Collect candidate memories from all domains based on intent."""
        candidates = []

        # Search memories by query if available
        query = entities.get("memory", "") or entities.get("query", "") or ""
        if query:
            try:
                results = self._memory_plugin.search_by_content(
                    plugin=self._memory_plugin,
                    query=query,
                    filters=None
                )
                for item in results:
                    candidates.append({
                        "content": item.get("content", ""),
                        "type": item.get("type", "MEMORY"),
                        "date": item.get("date", ""),
                        "confidence": item.get("confidence", 0.7),
                        "domain": "memory",
                        "id": item.get("id", ""),
                        "relations": item.get("relations", []),
                    })
            except Exception:
                pass

        # Get recent decisions
        try:
            decisions = self._decision_plugin.get_by_status("OPEN")
            for d in decisions[-10:]:  # Last 10 open decisions
                candidates.append({
                    "content": f"Decisión pendiente: {d.get('decision', '')} — {d.get('rationale', '')}",
                    "type": "DECISION",
                    "date": d.get("date", ""),
                    "confidence": d.get("confidence", 0.7),
                    "domain": "decision",
                    "id": d.get("id", ""),
                    "relations": [],
                })
        except Exception:
            pass

        # Get recent predictions
        try:
            predictions = self._prediction_plugin.get_by_status("OPEN")
            for p in predictions[-10:]:  # Last 10 open predictions
                candidates.append({
                    "content": f"Predicción: {p.get('prediction_text', '')}",
                    "type": "PREDICTION",
                    "date": p.get("date", ""),
                    "confidence": p.get("confidence", 0.5),
                    "domain": "prediction",
                    "id": p.get("id", ""),
                    "relations": [],
                })
        except Exception:
            pass

        # Get recent learnings
        try:
            learnings = self._learning_plugin.list_all()
            for l in learnings[-10:]:
                candidates.append({
                    "content": f"Lección: {l.get('lesson', '')}",
                    "type": "LESSON",
                    "date": l.get("date", ""),
                    "confidence": l.get("confidence", 0.8),
                    "domain": "learning",
                    "id": l.get("id", ""),
                    "relations": [],
                })
        except Exception:
            pass

        # Get recent reflections
        try:
            reflections = self._reflection_plugin.get_by_status("APPROVED")
            for r in reflections[-5:]:
                content = r.get("approved_content", "")
                if content:
                    candidates.append({
                        "content": f"Reflexión: {content}",
                        "type": "INTERPRETATION",
                        "date": r.get("date", ""),
                        "confidence": 0.8,
                        "domain": "reflection",
                        "id": r.get("id", ""),
                        "relations": [],
                    })
        except Exception:
            pass

        # Get current identity (high priority)
        try:
            identity = self._identity_plugin.get_current()
            if identity:
                candidates.append({
                    "content": f"Identidad: {identity.get('name', 'DECA')} — {identity.get('mission', '')} — Valores: {', '.join(identity.get('values', []))}",
                    "type": "IDENTITY",
                    "date": identity.get("audit_log", [{}])[-1].get("date", "") if identity.get("audit_log") else "",
                    "confidence": 1.0,
                    "domain": "identity",
                    "id": "identity_current",
                    "relations": [],
                })
        except Exception:
            pass

        return candidates

    def _score_candidates(self, candidates: List[Dict], intent: str) -> List[Dict]:
        """Score candidates by relevance: recency*0.3 + confidence*0.3 + relation_density*0.2 + type_priority*0.2"""
        now = datetime.now()
        scored = []

        for c in candidates:
            # Recency score (0-1, newer = higher)
            recency = self._calculate_recency(c.get("date", ""), now)

            # Confidence (already 0-1)
            confidence = c.get("confidence", 0.5)

            # Relation density (0-1, more relations = higher)
            relations = c.get("relations", [])
            relation_density = min(len(relations) / 5.0, 1.0) if relations else 0.0

            # Type priority
            type_priority = TYPE_PRIORITY.get(c.get("type", "").upper(), 0.5)

            # Weighted score
            score = (
                recency * 0.3 +
                confidence * 0.3 +
                relation_density * 0.2 +
                type_priority * 0.2
            )

            # Boost for intent-specific relevance
            score = self._apply_intent_boost(score, c, intent)

            scored.append({**c, "relevance_score": score})

        # Sort by score descending
        scored.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored

    def _calculate_recency(self, date_str: str, now: datetime) -> float:
        """Calculate recency score (0-1, newer = higher)."""
        if not date_str:
            return 0.0
        try:
            item_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            if item_date.tzinfo is not None:
                item_date = item_date.replace(tzinfo=None)
            days_diff = (now - item_date).days
            # Exponential decay: 1.0 at 0 days, ~0.37 at 30 days, ~0.14 at 90 days
            return max(0.0, min(1.0, 1.0 - (days_diff / 365.0)))
        except Exception:
            return 0.0

    def _apply_intent_boost(self, score: float, candidate: Dict, intent: str) -> float:
        """Apply intent-specific relevance boost."""
        domain = candidate.get("domain", "")
        
        # Intent-specific domain boosts
        intent_boosts = {
            "MEMORY_CREATE": {"memory": 0.2, "decision": 0.1},
            "MEMORY_SEARCH": {"memory": 0.3, "decision": 0.1, "learning": 0.1},
            "DECISION_CREATE": {"decision": 0.3, "memory": 0.1, "learning": 0.1},
            "DECISION_CONFIRM": {"decision": 0.3, "learning": 0.2},
            "PREDICTION_CREATE": {"prediction": 0.3, "memory": 0.1, "learning": 0.1},
            "PREDICTION_REVIEW": {"prediction": 0.3, "learning": 0.1},
            "LEARNING_CREATE": {"learning": 0.3, "decision": 0.1, "prediction": 0.1},
            "REFLECTION_CREATE": {"reflection": 0.3, "learning": 0.1, "memory": 0.1},
            "REFLECTION_APPROVE": {"reflection": 0.3, "identity": 0.1},
            "IDENTITY_PROPOSE": {"identity": 0.3, "learning": 0.1},
            "IDENTITY_APPROVE": {"identity": 0.3, "learning": 0.1},
            "TEMPORAL_QUERY": {"memory": 0.1, "decision": 0.1, "prediction": 0.1, "event": 0.2},
        }
        
        boost_map = intent_boosts.get(intent, {})
        domain = candidate.get("domain", "")
        return score + boost_map.get(domain, 0.0)

    def _select_within_budget(self, scored_candidates: List[Dict], token_budget: int) -> List[Dict]:
        """Select candidates within token budget using rough token estimation."""
        selected = []
        used_tokens = 0
        
        # Rough estimation: 1 token ≈ 4 chars (Spanish)
        chars_per_token = 4
        
        for candidate in scored_candidates:
            content = candidate.get("content", "")
            # Rough token estimate: content + formatting overhead
            content_tokens = len(content) // chars_per_token
            overhead = 50  # formatting, labels, etc.
            estimated_tokens = content_tokens + overhead
            
            if used_tokens + estimated_tokens <= token_budget:
                selected.append(candidate)
                used_tokens += estimated_tokens
            else:
                # Try to include a truncated version if there's some space left
                remaining = token_budget - used_tokens
                if remaining > 100:
                    # Include truncated
                    truncated_content = content[:(remaining - overhead) * 4] + "..."
                    truncated_candidate = {**candidate, "content": truncated_content}
                    selected.append(truncated_candidate)
                break
        
        return selected

    def _format_context_block(self, selected: List[Dict]) -> str:
        """Format selected candidates into a context block for LLM."""
        if not selected:
            return ""

        lines = ["=== CONTEXTO RELEVANTE ==="]
        
        for c in selected:
            domain_label = {
                "memory": "MEMORIA",
                "decision": "DECISIÓN",
                "prediction": "PREDICCIÓN",
                "learning": "APRENDIZAJE",
                "reflection": "REFLEXIÓN",
                "identity": "IDENTIDAD",
                "event": "EVENTO",
            }.get(c.get("domain", ""), c.get("type", "OTRO"))
            
            date_str = c.get("date", "")
            if date_str:
                lines.append(f"[{domain_label}] {date_str[:10]} — {c['content']}")
            else:
                lines.append(f"[{domain_label}] {c['content']}")

        lines.append("=== FIN CONTEXTO ===")
        return "\n".join(lines)

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation for Spanish text."""
        return len(text) // 4


# Module-level instance for auto-registration
PLUGIN = ContextPlugin()

# Lowercase alias
plugin = PLUGIN