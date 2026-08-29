# brain.plugins.user_name_ask - USER_NAME_ASK intent plugin
# Extracted from intent_layer._init_patterns()

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, EXACT, PHRASE, USER_NAME_ASK

# Patterns copied verbatim from intent_layer._init_patterns()
_user_name_ask_patterns = [
    Pattern(EXACT, "como me llamo", 100),
    Pattern(EXACT, "cual es mi nombre", 100),
    Pattern(EXACT, "cuales es mi nombre", 100),
    Pattern(EXACT, "que nombre tienes para mi", 100),
    Pattern(EXACT, "por que nombre me llamas", 100),
    Pattern(EXACT, "como me tengo guardado", 100),
    Pattern(EXACT, "como me tienes guardado", 100),
    Pattern(EXACT, "quien soy", 90),
    Pattern(EXACT, "y quien soy", 90),
    Pattern(PHRASE, "como me llamo", 85),
    Pattern(PHRASE, "cual es mi nombre", 85),
    Pattern(PHRASE, "quien soy", 80),
]

# Plugin instance - priority 5 per design.md
user_name_ask_plugin = IntentPlugin(
    name=USER_NAME_ASK,
    category="IDENTITY",
    patterns=_user_name_ask_patterns,
    priority=5,
)

# Alias for registry access (mod.plugin)
plugin = user_name_ask_plugin