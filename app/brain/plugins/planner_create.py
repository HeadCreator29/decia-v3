# brain.plugins.planner_create - PLANNER_CREATE intent plugin
# Extracted from intent_layer._init_patterns() + special logic

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, REGEX, PLANNER_CREATE
from utils.date_parser import PLANNER_DATE_MARKERS

# Constants moved from intent_layer.py
_PLANNER_RECALL_BANNED = (
    r"\b(?:algo\s+de|sobre|lo\s+que"
    r"|lo\s+de|ayer|anteayer|hace|"
    r"que\s+(?:(?:te\s+)?dije"
    r"|(?:me\s+)?dijiste"
    r"|(?:hemos\s+)?habl(?:amos"
    r"|ado)|paso|hice|hubo"
    r"|sucedio|ocurrio|acontecio)"
    r"|memoria|memorias|recuerdos)\b"
)

_PLANNER_MARKER_SRC = PLANNER_DATE_MARKERS

_PLANNER_QUERY_WORDS_EXCLUDED = (
    r"^(?!(?:que|y|quien|cual|cuales|"
    r"cuando|donde|como|por|para)\b)"
)


# Plugin instance - priority 5 per design.md
# validate() returns False for banned phrases matching _PLANNER_RECALL_BANNED,
# preventing MEMORY_SEARCH from extracting memory content that would steal the intent
_planner_create_patterns = [
    Pattern(REGEX,
            r"^(?!(?:que|y|quien|cual|cuales|"
            r"cuando|donde|como|por|para)\b)"
            r"(?:(?!\b(?:algo\s+de|sobre|lo\s+que"
            r"|lo\s+de|ayer|anteayer|hace|"
            r"que\s+(?:(?:te\s+)?dije"
            r"|(?:me\s+)?dijiste"
            r"|(?:hemos\s+)?habl(?:amos"
            r"|ado)|paso|hice|hubo"
            r"|suscidio|ocurrio|acontecio)\b)"
            r"|memoria|memorias|recuerdos)\b)*"
            r"a\s+las\s+\d{1,2}(?::\d{2})?\s*"
            r"(?:de\s+la\s+ma[n\u00f1]ana)\b.+",
            85),
    Pattern(REGEX,
            r"^(?:decia\s+)?recuerdame\s+"
            r"(?:(?!\b(?:algo\s+de|sobre|lo\s+que"
            r"|lo\s+de|ayer|anteayer|hace|"
            r"que\s+(?:(?:te\s+)?dije"
            r"|(?:me\s+)?dijiste"
            r"|(?:hemos\s+)?habl(?:amos"
            r"|ado)|paso|hice|hubo"
            r"|suscidio|ocurrio|acontecio)\b)"
            r"|memoria|memorias|recuerdos)\b)+$",
            80),
    Pattern(REGEX,
            r"^(?!(?:que|y|quien|cual|cuales|"
            r"cuando|donde|como|por|para)\b)"
            r"a\s+las\s+\d{1,2}(?::\d{2})?\s*"
            r"(?:de\s+la\s+ma[n\u00f1]ana)\b.+",
            80),
]

planner_create_plugin = IntentPlugin(
    name=PLANNER_CREATE,
    category="UTILITY",
    patterns=_planner_create_patterns,
    priority=5,
)

# Alias for registry access (mod.plugin)
plugin = planner_create_plugin


# PLANNER_CREATE validate() - returns False for recall-ban phrases
# when the message matches _PLANNER_RECALL_BANNED regex,
# preventing MEMORY_SEARCH from stealing memory content
def _check_recall_ban(message: str) -> bool:
    """Check if message contains a banned recall phrase.

    Returns True if the message matches the recall-ban pattern,
    indicating the message should be blocked.

    Returns False if no banned phrase found (validation passes).
    """
    import re
    if re.search(_PLANNER_RECALL_BANNED, message, re.IGNORECASE):
        return True  # banned phrase found
    return False  # no banned phrase


# Override the plugin's validate method
# Called as plugin.validate(message, entities) — no auto-binding, so no self
planner_create_plugin.validate = lambda message, entities: not \
    _check_recall_ban(message)