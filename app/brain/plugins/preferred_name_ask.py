# brain.plugins.preferred_name_ask - PREFERRED_NAME_ASK intent plugin
# Extracted from intent_layer._init_patterns()

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, EXACT, PHRASE, PREFERRED_NAME_ASK

# Patterns copied verbatim from intent_layer._init_patterns()
_preferred_name_ask_patterns = [
    Pattern(EXACT, "como quieres llamarme", 100),
    Pattern(PHRASE, "como quieres llamarme", 90),
    Pattern(PHRASE, "como me llama", 85),
    Pattern(EXACT, "como me llama", 95),
]

# Plugin instance - priority 5 per design.md
preferred_name_ask_plugin = IntentPlugin(
    name=PREFERRED_NAME_ASK,
    category="IDENTITY",
    patterns=_preferred_name_ask_patterns,
    priority=5,
)

# Alias for registry access (mod.plugin)
plugin = preferred_name_ask_plugin