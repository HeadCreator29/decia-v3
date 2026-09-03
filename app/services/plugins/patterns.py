# app/services/plugins/patterns.py - PatternsPlugin
# Cross-domain pattern detection across memory types.
# Detects recurring themes and suggests planner tasks.

import json
import os
from collections import Counter
from datetime import datetime
from typing import Dict, List, Optional, Any

from app.services.plugins.base import ServicePlugin
from app.services.plugins.memory import MemoryPlugin
from app.services.plugins.decision import DecisionPlugin
from app.services.plugins.prediction import PredictionPlugin
from app.services.plugins.learning import LearningPlugin
from app.services.plugins.reflection import ReflectionPlugin

# Supported domains for pattern detection
PATTERN_DOMAINS = [
    "memory",
    "decision",
    "prediction",
    "learning",
    "reflection",
]

# Minimum occurrences to consider a pattern
MIN_PATTERN_OCCURRENCES = 2


class PatternsPlugin(ServicePlugin):
    """PatternsPlugin for detecting recurring patterns across domains.

    Analyzes memories, decisions, predictions, learnings, and reflections
    to identify recurring themes, topics, and behavioral patterns.
    Suggests planner tasks based on detected patterns.
    """

    def __init__(self, **kwargs):
        super().__init__(
            name="PATTERNS",
            category="ARCHIVE",
            description="Cross-domain pattern detection with planner task suggestions",
            **kwargs,
        )
        self._memory_plugin = MemoryPlugin()
        self._decision_plugin = DecisionPlugin()
        self._prediction_plugin = PredictionPlugin()
        self._learning_plugin = LearningPlugin()
        self._reflection_plugin = ReflectionPlugin()

    def detect_recurring_patterns(
        self,
        domains: List[str] = None,
        min_occurrences: int = MIN_PATTERN_OCCURRENCES
    ) -> List[Dict]:
        """Detect recurring patterns across specified domains.

        Args:
            domains: List of domains to analyze (default: all PATTERN_DOMAINS)
            min_occurrences: Minimum occurrences to consider a pattern

        Returns:
            List of pattern dicts with theme, occurrences, domains, and suggested tasks
        """
        if domains is None:
            domains = PATTERN_DOMAINS

        # Collect all text content from specified domains
        all_texts = []

        if "memory" in domains:
            all_texts.extend(self._get_memory_texts())
        if "decision" in domains:
            all_texts.extend(self._get_decision_texts())
        if "prediction" in domains:
            all_texts.extend(self._get_prediction_texts())
        if "learning" in domains:
            all_texts.extend(self._get_learning_texts())
        if "reflection" in domains:
            all_texts.extend(self._get_reflection_texts())

        if not all_texts:
            return []

        # Extract keywords/topics using simple frequency analysis
        # In production, this could use embeddings or LLM
        patterns = self._extract_patterns(all_texts, min_occurrences)

        # Generate suggested planner tasks for each pattern
        for pattern in patterns:
            pattern["suggested_tasks"] = self._generate_tasks_for_pattern(pattern)

        return patterns

    def _get_memory_texts(self) -> List[str]:
        """Get all memory content texts."""
        try:
            all_memories = self._memory_plugin.execute({"action": "list"})
            texts = []
            for entry in all_memories.values():
                content = entry.get("content", "")
                if content:
                    texts.append(content)
            return texts
        except Exception:
            return []

    def _get_decision_texts(self) -> List[str]:
        """Get all decision texts."""
        try:
            decisions = self._decision_plugin.list_all()
            texts = []
            for d in decisions:
                texts.append(d.get("problem", ""))
                texts.append(d.get("decision", ""))
                texts.append(d.get("rationale", ""))
            return [t for t in texts if t]
        except Exception:
            return []

    def _get_prediction_texts(self) -> List[str]:
        """Get all prediction texts."""
        try:
            predictions = self._prediction_plugin.list_all()
            texts = []
            for p in predictions:
                texts.append(p.get("prediction_text", ""))
                for reason in p.get("reasons", []):
                    texts.append(reason)
            return [t for t in texts if t]
        except Exception:
            return []

    def _get_learning_texts(self) -> List[str]:
        """Get all learning texts."""
        try:
            learnings = self._learning_plugin.list_all()
            texts = []
            for l in learnings:
                texts.append(l.get("lesson", ""))
                texts.append(l.get("future_considerations", ""))
            return [t for t in texts if t]
        except Exception:
            return []

    def _get_reflection_texts(self) -> List[str]:
        """Get all reflection texts."""
        try:
            reflections = self._reflection_plugin.list_all()
            texts = []
            for r in reflections:
                content = r.get("approved_content") or r.get("draft_content", "")
                texts.append(content)
            return [t for t in texts if t]
        except Exception:
            return []

    def _extract_patterns(self, texts: List[str], min_occurrences: int) -> List[Dict]:
        """Extract recurring patterns from texts using keyword frequency.

        In production, this could use TF-IDF, embeddings, or LLM-based clustering.
        """
        # Common stop words to filter out
        stop_words = {
            "que", "de", "el", "la", "los", "las", "un", "una", "unos", "unas",
            "del", "al", "en", "y", "o", "a", "e", "u", "no", "si", "se", "le",
            "lo", "me", "te", "nos", "les", "este", "esta", "esto", "ese", "esa",
            "eso", "hay", "son", "es", "fue", "ser", "estar", "haber", "tener",
            "hacer", "poder", "querer", "saber", "mi", "tu", "su", "mis", "tus",
            "sus", "con", "por", "para", "sin", "sobre", "entre", "hasta", "desde",
            "muy", "más", "menos", "como", "cuando", "donde", "quien", "cual",
            "todo", "todos", "toda", "todas", "mucho", "poca", "poco", "otro",
            "otros", "otra", "otras", "mismo", "misma", "mismos", "mismas",
        }

        # Domain-specific important keywords (topics to track)
        topic_keywords = {
            "trabajo": ["trabajo", "proyecto", "tarea", "reunión", "cliente", "empresa", "jefe", "equipo"],
            "salud": ["salud", "médico", "hospital", "enfermedad", "medicina", "dolor", "síntoma"],
            "estudio": ["estudio", "curso", "clase", "examen", "aprender", "leer", "libro", "universidad"],
            "familia": ["familia", "hijo", "hija", "pareja", "padre", "madre", "hermano", "abuelo"],
            "finanzas": ["dinero", "gasto", "ingreso", "ahorro", "inversión", "presupuesto", "deuda"],
            "ejercicio": ["ejercicio", "gimnasio", "correr", "deporte", "entreno", "físico", "salud"],
            "viaje": ["viaje", "vacaciones", "hotel", "vuelo", "destino", "turismo", "playa", "montaña"],
            "tecnología": ["código", "programar", "software", "bug", "deploy", "servidor", "base de datos", "api"],
            "decisión": ["decisión", "elegir", "opción", "alternativa", "decidí", "elegí"],
            "predicción": ["predigo", "creo que", "pasará", "futuro", "pronostico"],
            "aprendizaje": ["aprendí", "lección", "enseñanza", "experiencia", "me di cuenta"],
        }

        # Count topic occurrences
        topic_counts = Counter()
        word_counts = Counter()

        for text in texts:
            text_lower = text.lower()
            words = text_lower.split()
            
            # Count individual words (filtered)
            for word in words:
                if len(word) > 3 and word not in stop_words:
                    word_counts[word] += 1

            # Count topic keywords
            for topic, keywords in topic_keywords.items():
                for kw in keywords:
                    if kw in text_lower:
                        topic_counts[topic] += 1

        patterns = []

        # Add topic patterns
        for topic, count in topic_counts.items():
            if count >= min_occurrences:
                patterns.append({
                    "type": "topic",
                    "theme": topic,
                    "occurrences": count,
                    "domains": ["cross-domain"],
                    "keywords": topic_keywords[topic][:5],
                })

        # Add high-frequency word patterns
        for word, count in word_counts.most_common(20):
            if count >= min_occurrences and word not in topic_keywords.values():
                patterns.append({
                    "type": "keyword",
                    "theme": word,
                    "occurrences": count,
                    "domains": ["cross-domain"],
                    "keywords": [word],
                })

        return patterns

    def _generate_tasks_for_pattern(self, pattern: Dict) -> List[Dict]:
        """Generate suggested planner tasks based on a detected pattern."""
        tasks = []
        theme = pattern.get("theme", "")
        pattern_type = pattern.get("type", "")

        if pattern_type == "topic":
            # Topic-based task suggestions
            if theme == "trabajo":
                tasks.append({
                    "title": "Revisar avances del proyecto semanal",
                    "type": "recurring",
                    "frequency": "weekly",
                    "reason": "Pattern: trabajo recurrente detectado",
                })
            elif theme == "salud":
                tasks.append({
                    "title": "Programar chequeo médico anual",
                    "type": "once",
                    "frequency": "yearly",
                    "reason": "Pattern: temas de salud recurrentes",
                })
            elif theme == "estudio":
                tasks.append({
                    "title": "Dedicar 30 min diarios a estudio",
                    "type": "recurring",
                    "frequency": "daily",
                    "reason": "Pattern: estudio recurrente detectado",
                })
            elif theme == "finanzas":
                tasks.append({
                    "title": "Revisar presupuesto mensual",
                    "type": "recurring",
                    "frequency": "monthly",
                    "reason": "Pattern: finanzas recurrentes",
                })
            elif theme == "ejercicio":
                tasks.append({
                    "title": "Sesión de ejercicio 3x/semana",
                    "type": "recurring",
                    "frequency": "weekly",
                    "reason": "Pattern: ejercicio recurrente",
                })
            elif theme == "tecnología":
                tasks.append({
                    "title": "Actualizar dependencias y revisar seguridad",
                    "type": "recurring",
                    "frequency": "monthly",
                    "reason": "Pattern: tecnología recurrente",
                })

        elif pattern_type == "keyword":
            # Keyword-based generic task
            if pattern.get("occurrences", 0) >= 5:
                tasks.append({
                    "title": f"Profundizar en: {theme}",
                    "type": "once",
                    "reason": f"Palabra '{theme}' aparece {pattern['occurrences']} veces",
                })

        return tasks


# Module-level instance for auto-registration
PLUGIN = PatternsPlugin()

# Lowercase alias
plugin = PLUGIN