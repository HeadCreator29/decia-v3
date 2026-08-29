# brain.plugins.greeting - GREETING intent plugin
# Extracted from intent_layer._init_patterns()

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, EXACT, PHRASE, GREETING

# Patterns copied verbatim from intent_layer._init_patterns()
_greeting_patterns = [
    Pattern(EXACT, "hola", 100, word_boundary=True),
    Pattern(PHRASE, "buenos dias", 95, {"buenos": 5}),
    Pattern(PHRASE, "buenas tardes", 95, {"buenas": 5}),
    Pattern(PHRASE, "buenas noches", 95, {"buenas": 5}),
    Pattern(PHRASE, "buenas", 90),
]

# Plugin instance - priority 10 per design.mod
greeting_plugin = IntentPlugin(
    name="GREETING",
    category="SOCIAL",
    patterns=_greeting_patterns,
    priority=10,
)

# Alias for registry access (mod.plugin)
plugin = greeting_plugin