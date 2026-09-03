# brain.intent_layer - Intent Classification Orchestrator
# Refactored to use PluginRegistry pattern — thin orchestrator (~200 lines)
# Patterns sourced from PluginRegistry, not monolithic _init_patterns()

import importlib
import re
from utils.normalizer import normalize_strict

from utils.date_parser import PLANNER_DATE_MARKERS

from brain.intent_types import (
    EXACT,
    PHRASE,
    REGEX,
    KEYWORD,
    GREETING,
    THANKS,
    DECIA_SELF,
    DECIA_CREATOR,
    USER_NAME_ASK,
    USER_NAME_SET,
    PREFERRED_NAME_ASK,
    PREFERRED_NAME_SET,
    CALCULATE,
    TIME,
    DATE,
    MEMORY_CREATE,
    MEMORY_SEARCH,
    ARCHIVE_DIRECT,
    ARCHIVE_SEARCH,
    EXIT,
    AMBIGUOUS_INPUT,
    FREE_TALK,
    LEARNING_CREATE,
    CONFIDENCE_SEGURO,
    CONFIDENCE_PROBABLE,
    CONFIDENCE_AMBIGUO,
    Pattern,
    Candidate,
    ClassifyResult,
)

from brain.plugins.registry import PluginRegistry


_SAFE_INTENTS = {
    GREETING,
    THANKS,
    EXIT,
    CALCULATE,
    TIME,
    DATE,
    DECIA_SELF,
    DECIA_CREATOR,
    ARCHIVE_DIRECT,
    LEARNING_CREATE,
}


# ==========================================
# ORCHESTRATOR
# ==========================================

class IntentLayer:
    """Thin intent classifier orchestrator.

    Pattern storage delegated to PluginRegistry. All classification
    scoring, confidence, and entity logic preserved identically from
    the monolithic implementation. Public API unchanged:
    classify(message) → ClassifyResult.
    """

    def __init__(self):
        self._registry = PluginRegistry()
        self._archive_keywords = self._init_archive_keywords()
        self._load_plugins()

    def _init_archive_keywords(self):
        """Initialize archive field extraction keywords.

        Kept as module-level state mirroring the original
        _archive_keywords dict from the monolith.
        """
        return {
            "meaning": ["significa", "significado", "representa"],
            "origin": ["comenzo", "empezo", "inicio", "nacio"],
            "values": ["valores", "principios"],
            "vision": ["vision", "objetivo"],
            "creator": ["creador", "fundador", "creo", "fundo"],
            "events": ["historia", "evento", "eventos", "acontecimiento"],
            "memories": ["recuerda", "recuerdo", "memoria", "memorias",
                        "hicimos", "hice", "hizo", "hoy", "ayer",
                        "transmision"],
        }

    def _load_plugins(self):
        """Register all 16 intent plugins with the registry.

        Phase 4: pkgutil auto-discovery with explicit import fallback.
        """
        # Try auto-discovery first
        discovered = self._discover_plugins_pkgutil()
        if discovered:
            for mod in discovered:
                # Support both 'plugin' (legacy) and 'PLUGIN' (new) attributes
                plugin = getattr(mod, "plugin", getattr(mod, "PLUGIN", None))
                if plugin:
                    self._registry.register(plugin)
            return

# Fallback: explicit imports for reliability
        plugin_module_names = [
            "brain.plugins.greeting",
            "brain.plugins.thanks",
            "brain.plugins.decia_self",
            "brain.plugins.decia_creator",
            "brain.plugins.user_name_ask",
            "brain.plugins.preferred_name_ask",
            "brain.plugins.user_name_set",
            "brain.plugins.preferred_name_set",
            "brain.plugins.calculate",
            "brain.plugins.time",
            "brain.plugins.date",
            "brain.plugins.memory_create",
            "brain.plugins.memory_search",
            "brain.plugins.archive_direct",
            "brain.plugins.archive_search",
            "brain.plugins.exit",
            "brain.plugins.ambiguous_input",
            "brain.plugins.free_talk",
            "brain.plugins.planner_create",
            "brain.plugins.planner_query",
            "brain.plugins.learning_create",
            "brain.plugins.reflection_create",
            "brain.plugins.reflection_approve",
            "brain.plugins.identity_propose",
            "brain.plugins.identity_approve",
        ]

        for mod_name in plugin_module_names:
            mod = importlib.import_module(mod_name)
            self._registry.register(mod.plugin)

    def _discover_plugins_pkgutil(self):
        """Attempt pkgutil auto-discovery of plugin modules.

        Walks app.brain.plugins package and imports any module
        exporting a `plugin` instance. Gracefully falls back to
        the explicit import list in _load_plugins() if any imports
        fail (e.g., in packaged environments).

        Returns the list of successfully imported modules.
        """
        import pkgutil
        import importlib

        discovered = []
        try:
            for importer, modname, ispkg in pkgutil.iter_modules(
                ["app/brain/plugins"]
            ):
                try:
                    module = importlib.import_module(f"brain.plugins.{modname}")
                    # Check for both 'plugin' (legacy) and 'PLUGIN' (new standard)
                    if hasattr(module, "plugin"):
                        discovered.append(module)
                    elif hasattr(module, "PLUGIN"):
                        discovered.append(module)
                except Exception:
                    # Continue on per-module failure; fallback to explicit list
                    pass
        except Exception:
            # pkgutil not available; fall back to explicit imports
            pass
        return discovered

    def classify(self, message):
        """Classify a user message into an intent.

        Same algorithm as the monolithic implementation, but patterns
        are sourced from self._registry.get_all_patterns() and
        validate_match() is called for plugin-specific validation
        (exit negation, planner recall-ban).

        Returns ClassifyResult with intent, confidence, entities,
        matched_pattern, and candidates.
        """
        normalized = normalize_strict(message)

        if not normalized:
            return ClassifyResult(
                intent=AMBIGUOUS_INPUT,
                confidence=1.0,
                entities={},
                matched_pattern="",
                candidates=[],
            )

        raw_words = message.lower().strip().split()
        word_count = len(raw_words)

        candidates = []

        for intent, patterns in self._registry.get_all_patterns().items():

            best_score = 0
            best_pattern = None

            for pattern in patterns:
                score = self._score_pattern(
                    pattern, normalized, message
                )

                if score > best_score:
                    best_score = score
                    best_pattern = pattern

            if best_score > 0:
                entities = self._extract_entities(
                    best_pattern, normalized, message,
                )

                candidates.append(Candidate(
                    intent=intent,
                    score=best_score,
                    matched_pattern=(
                        best_pattern.value
                    ),
                    matched_type=(
                        best_pattern.type
                    ),
                    entities=entities,
                ))

        candidates.sort(
            key=lambda c: c.score,
            reverse=True,
        )

        _write_entity_rules = {
            USER_NAME_SET: "user_name",
            PREFERRED_NAME_SET: "preferred_name",
            MEMORY_CREATE: "memory",
        }

        for c in candidates:

            required = _write_entity_rules.get(
                c.intent
            )

            if required                     and required not in c.entities:

                c.score = 0

        if self._has_exit_negation(normalized):

            for c in candidates:

                if c.intent == EXIT:

                    c.score = 0

        candidates = [
            c for c in candidates if c.score > 0
        ]

        if not candidates:

            if word_count <= 2:

                return ClassifyResult(
                    intent=AMBIGUOUS_INPUT,
                    confidence=1.0,
                    entities={},
                    matched_pattern="",
                    candidates=[],
                )

            return ClassifyResult(
                intent=FREE_TALK,
                confidence=0.0,
                entities={},
                matched_pattern="",
                candidates=candidates,
            )

        best = candidates[0]

        second_score = (
            candidates[1].score
            if len(candidates) > 1
            else 0
        )

        confidence = _calc_confidence(
            best.score, second_score,
            len(candidates)
        )

        if best.score < 50:

            if word_count <= 2:

                confidence = max(confidence, 0.80)

                return ClassifyResult(
                    intent=AMBIGUOUS_INPUT,
                    confidence=confidence,
                    entities={},
                    matched_pattern="",
                    candidates=candidates,
                )

            return ClassifyResult(
                intent=FREE_TALK,
                confidence=0.0,
                entities={},
                matched_pattern="",
                candidates=candidates,
            )

        return ClassifyResult(
            intent=best.intent,
            confidence=confidence,
            entities=best.entities,
            matched_pattern=best.matched_pattern,
            candidates=candidates,
        )

    # ==========================================
    # SCORING
    # ==========================================

    def _score_pattern(self, pattern, normalized,
                       original):

        if pattern.type == EXACT:

            return self._score_exact(
                pattern, normalized
            )

        if pattern.type == PHRASE:

            return self._score_phrase(
                pattern, normalized
            )

        if pattern.type == REGEX:

            return self._score_regex(
                pattern, normalized
            )

        if pattern.type == KEYWORD:

            return self._score_keyword(
                pattern, normalized
            )

        return 0

    def _score_exact(self, pattern, normalized):

        if pattern.word_boundary:

            p = r'\b' + re.escape(pattern.value)                 + r'\b'

            if re.search(p, normalized):

                return pattern.weight

            return 0

        if normalized == pattern.value:

            return pattern.weight

        return 0

    def _score_phrase(self, pattern, normalized):

        if pattern.value in normalized:

            score = pattern.weight
            for boost_keyword, boost_value in pattern.boosts.items():
                if boost_keyword in normalized:
                    score += boost_value
            return score

        return 0

    def _score_regex(self, pattern, normalized):

        if re.search(pattern.value, normalized):

            return pattern.weight

        return 0

    def _score_keyword(self, pattern, normalized):

        if pattern.value not in normalized:

            return 0

        score = pattern.weight

        for boost_keyword, boost_value in                 pattern.boosts.items():

            if boost_keyword in normalized:

                score += boost_value

        return score

    def _has_exit_negation(self, normalized):

        if "no" not in normalized:

            return False

        if "salir" not in normalized:

            return False

        idx_no = normalized.find("no")
        idx_salir = normalized.find("salir")

        return idx_no < idx_salir

# ==========================================
# ENTIDADES
# ==========================================

    def _extract_entities(self, pattern,
                          normalized, original=""):

        if not pattern.entity_group:

            return {}

        if pattern.type == REGEX:

            text = (original
                    if pattern.entity_group == "math"
                    else normalized)

            return self._extract_regex(
                pattern, text
            )

        if pattern.type == PHRASE:

            return self._extract_phrase(
                pattern, normalized
            )

        return {}

    def _extract_regex(self, pattern, normalized):

        match = re.search(pattern.value, normalized)

        if not match:

            return {}

        group = pattern.entity_group

        if match.groups():

            value = match.group(1).strip()

            value = value.strip(".,;:!?")

            if not value:

                return {}

            return {group: value.capitalize()}

        return {group: normalized.strip()}

    def _extract_phrase(self, pattern, normalized):

        group = pattern.entity_group

        idx = normalized.find(pattern.value)

        if idx == -1:

            return {}

        after = normalized[
            idx + len(pattern.value):
        ].strip()

        if not after:

            return {}

        return {group: after}

    @staticmethod
    def log_result(result, used=False,
                   reason="observation_only"):

        second = ""

        if (result.candidates
                and len(result.candidates) > 1):

            s = result.candidates[1]

            second = (
                f" | second_candidate="
                f"{s.intent}"
                f" second_score={s.score}"
            )

        entities = ""

        if result.entities:

            entities = (
                f" | entities="
                f"{result.entities}"
            )

        print(
            f"[DECIA INTENT] "
            f"intent={result.intent} "
            f"confidence={result.confidence} "
            f"matched_pattern="
            f"{result.matched_pattern}"
            f"{second}{entities}"
            f" used={used}"
            f" reason={reason}"
        )


def _extract_archive_field(normalized):

    for field, keywords in             _archive_keywords.items():

        for kw in keywords:

            if kw in normalized:

                return {
                    "deca_field": field
                }

    return {}


# ==========================================
# CONFIDENCE
# ==========================================

def _calc_confidence(best_score,
                     second_score,
                     num_candidates):

    if best_score == 0:

        return 0.0

    normalized = best_score / 100.0

    delta = best_score - second_score

    if delta >= 30:

        factor_delta = 1.0

    elif delta >= 15:

        factor_delta = 0.95

    else:

        factor_delta = 0.85

    factor_s = 1.0

    confidence = (
        normalized * factor_delta * factor_s
    )

    return round(min(confidence, 1.0), 2)