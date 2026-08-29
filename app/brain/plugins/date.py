# brain.plugins.date - DATE intent plugin
# Extracted from intent_layer._init_patterns()

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, PHRASE, REGEX, DATE

# Patterns copied verbatim from intent_layer._init_patterns()
_date_patterns = [
    Pattern(PHRASE, "que dia es hoy", 100),
    Pattern(PHRASE, "cual es la fecha", 100),
    Pattern(PHRASE, "que fecha es hoy", 100),
    Pattern(PHRASE, "dime la fecha", 95),
    Pattern(PHRASE, "me dices la fecha", 95),
    Pattern(PHRASE, "puedes decirme la fecha", 90),
    Pattern(PHRASE, "me puedes decir la fecha", 90),
    Pattern(PHRASE, "sabes que dia es", 90),
    Pattern(PHRASE, "en que fecha estamos", 90),
    Pattern(REGEX,
            r"que\s+(dia|fecha)\s+(es|tenemos|estamos)",
            100),
    Pattern(REGEX,
            r"(?:fecha|dia)\s+(actual|hoy|de\s+hoy)",
            85),
    Pattern(REGEX,
            r"(?:dime|me\s+dices|me\s+puedes\s+decir|sabes|cual|cuando)\s+(es)?\s?(la )?(fecha|dia)",
            80),
]

# Plugin instance - priority 10 per design.md
plugin = IntentPlugin(
    name=DATE,
    category="SOCIAL",
    patterns=_date_patterns,
    priority=10,
)