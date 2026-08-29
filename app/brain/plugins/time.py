# brain.plugins.time - TIME intent plugin
# Extracted from intent_layer._init_patterns()

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, PHRASE, REGEX, TIME

# Patterns copied verbatim from intent_layer._init_patterns()
_time_patterns = [
    Pattern(PHRASE, "que hora es", 100),
    Pattern(PHRASE, "cuanto es la hora", 100),
    Pattern(PHRASE, "dime la hora", 95),
    Pattern(PHRASE, "me dices la hora", 95),
    Pattern(PHRASE, "puedes decirme la hora", 90),
    Pattern(PHRASE, "me puedes decir la hora", 90),
    Pattern(PHRASE, "sabes que hora es", 90),
    Pattern(REGEX,
            r"que\s+hora\s+(es|tien[ea]|tenemos|estamos)",
            100),
    Pattern(REGEX,
            r"hora\s+(actual|ahora|de\s+ahora)",
            85),
    Pattern(REGEX,
            r"(?:dime|me\s+dices|me\s+puedes\s+decir|sabes|cual|cuanto)\s+(es)?\s?(la )?hora",
            80),
]

# Plugin instance - priority 10 per design.md
plugin = IntentPlugin(
    name=TIME,
    category="SOCIAL",
    patterns=_time_patterns,
    priority=10,
)