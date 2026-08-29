# brain.plugins.thanks - THANKS intent plugin
# Extracted from intent_layer._init_patterns()

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, EXACT, PHRASE, THANKS

# Patterns copied verbatim from intent_layer._init_patterns()
_thanks_patterns = [
    Pattern(EXACT, "gracias", 100),
    Pattern(EXACT, "muchas gracias", 100),
    Pattern(PHRASE, "muchas gracias", 95),
    Pattern(PHRASE, "gracias", 90),
]

# Plugin instance - priority 10 per design.md
plugin = IntentPlugin(
    name="THANKS",
    category="SOCIAL",
    patterns=_thanks_patterns,
    priority=10,
)