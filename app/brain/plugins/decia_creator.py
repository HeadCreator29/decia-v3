# brain.plugins.decia_creator - DECIA_CREATOR intent plugin
# Extracted from intent_layer._init_patterns()

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, EXACT, PHRASE, KEYWORD, DECIA_CREATOR

# Patterns copied verbatim from intent_layer._init_patterns()
_decia_creator_patterns = [
    Pattern(PHRASE, "quien te creo", 100),
    Pattern(PHRASE, "quien te creÃ³", 100),
    Pattern(PHRASE, "quien es tu creador", 100),
    Pattern(PHRASE, "quien es tu creadora", 100),
    Pattern(PHRASE, "quien hizo", 95),
    Pattern(PHRASE, "quien te hizo", 95),
    Pattern(PHRASE, "como te crearon", 95),
    Pattern(PHRASE, "como naciste", 95),
    Pattern(KEYWORD, "quien", 65,
            {"creo": 15,
             "hizo": 15}),
    Pattern(KEYWORD, "quiÃ©n", 65,
            {"creo": 15,
             "hizo": 15}),
    Pattern(KEYWORD, "creador", 70,
            {"quien": 10, "quiÃ©n": 10}),
    Pattern(KEYWORD, "creadora", 70,
            {"quien": 10, "quiÃ©n": 10}),
]

# Plugin instance - priority 5 per design.md
decia_creator_plugin = IntentPlugin(
    name=DECIA_CREATOR,
    category="IDENTITY",
    patterns=_decia_creator_patterns,
    priority=5,
)

# Alias for registry access (mod.plugin)
plugin = decia_creator_plugin