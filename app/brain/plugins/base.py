# brain.plugins.base - IntentPlugin dataclass
# Provides the IntentPlugin data structure for intent classification plugins

from dataclasses import dataclass
import re
from brain.intent_types import Pattern, EXACT, PHRASE, KEYWORD, REGEX, ClassifyResult, Candidate, AMBIGUOUS_INPUT, FREE_TALK, CONFIDENCE_SEGURO, CONFIDENCE_PROBABLE, CONFIDENCE_AMBIGUO


@dataclass
class IntentPlugin:
    """Dataclass representing a single intent plugin.

    Attributes:
        name: The intent name identifier (e.g., "GREETING", "CALCULATE")
        category: The intent category (e.g., "SOCIAL", "UTILITY")
        patterns: List of Pattern objects for matching
        entity_group: Optional entity group for entity extraction ("user_name", "preferred_name", "memory", "math")
        priority: Integer tie-breaker (higher wins) for deterministic classification
        validate: Optional validation hook; defaults to returning True
    """

    name: str
    category: str
    patterns: list[Pattern]
    entity_group: str | None = None
    priority: int = 0

    def validate(self, message: str, entities: dict) -> bool:
        """Default validation hook. Returns True by default.

        Subclasses or concrete plugin instances can override this method
        to add custom validation logic (e.g., exit negation, planner recall-ban).
        """
        return True

    def classify(self, message: str) -> ClassifyResult:
        """Classify a message using this plugin's patterns.

        Returns a ClassifyResult with intent, confidence, entities, matched_pattern, and candidates.
        """
        normalized = message.lower().strip()

        if not normalized:
            return ClassifyResult(
                intent=AMBIGUOUS_INPUT,
                confidence=1.0,
                entities={},
                matched_pattern="",
                candidates=[],
            )

        candidates = []

        for pattern in self.patterns:

            score = self._score_pattern(pattern, normalized)

            if score > 0:
                entities = self._extract_entities(pattern, normalized, message)

                candidates.append(Candidate(
                    intent=self.name,
                    score=score,
                    matched_pattern=pattern.value,
                    matched_type=pattern.type,
                    entities=entities,
                ))

        if not candidates:
            word_count = len(message.split())
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
                candidates=[],
            )

        best = candidates[0]
        second_score = candidates[1].score if len(candidates) > 1 else 0

        delta = best.score - second_score
        if delta >= 30:
            factor_delta = 1.0
        elif delta >= 15:
            factor_delta = 0.95
        else:
            factor_delta = 0.85

        normalized = best.score / 100.0
        confidence = round(min(normalized * factor_delta, 1.0), 2)

        return ClassifyResult(
            intent=best.intent,
            confidence=confidence,
            entities=best.entities,
            matched_pattern=best.matched_pattern,
            candidates=candidates,
        )

    def _score_pattern(self, pattern, normalized):
        if pattern.type == EXACT:
            return self._score_exact(pattern, normalized)
        if pattern.type == PHRASE:
            return self._score_phrase(pattern, normalized)
        if pattern.type == REGEX:
            return self._score_regex(pattern, normalized)
        if pattern.type == KEYWORD:
            return self._score_keyword(pattern, normalized)
        return 0

    def _score_exact(self, pattern, normalized):
        if pattern.word_boundary:
            import re
            p = r'\b' + re.escape(pattern.value) + r'\b'
            if re.search(p, normalized):
                return pattern.weight
            return 0
        if normalized == pattern.value:
            return pattern.weight
        return 0

    def _score_phrase(self, pattern, normalized):
        if pattern.value in normalized:
            return pattern.weight
        return 0

    def _score_regex(self, pattern, normalized):
        import re
        if re.search(pattern.value, normalized):
            return pattern.weight
        return 0

    def _score_keyword(self, pattern, normalized):
        if pattern.value not in normalized:
            return 0
        score = pattern.weight
        for boost_keyword, boost_value in pattern.boosts.items():
            if boost_keyword in normalized:
                score += boost_value
        return score

    def _extract_entities(self, pattern, normalized, original=""):
        if not pattern.entity_group:
            return {}
        if pattern.type == REGEX:
            text = normalized
            match = re.search(pattern.value, text)
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
        if pattern.type == PHRASE:
            group = pattern.entity_group
            idx = normalized.find(pattern.value)
            if idx == -1:
                return {}
            after = normalized[idx + len(pattern.value):].strip()
            if not after:
                return {}
            return {group: after}
        return {}