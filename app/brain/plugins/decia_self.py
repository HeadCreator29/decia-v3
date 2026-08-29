# brain.plugins.decia_self - DECIA_SELF intent plugin
# Extracted from intent_layer._init_patterns()

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, EXACT, PHRASE, DECIA_SELF

# Patterns copied verbatim from intent_layer._init_patterns()
_decia_self_patterns = [
    Pattern(EXACT, "quien eres", 100),
    Pattern(EXACT, "que eres", 100),
    Pattern(EXACT, "como te llamas", 100),
    Pattern(EXACT, "cual es tu nombre", 100),
    Pattern(PHRASE, "quien eres", 90),
    Pattern(PHRASE, "que eres", 90),
    Pattern(PHRASE, "como te llamas", 90),
    Pattern(PHRASE, "cual es tu nombre", 90),
    Pattern(PHRASE, "que es decia", 100),
    Pattern(PHRASE, "hablame de decia", 100),
    Pattern(PHRASE, "hablame sobre decia", 100),
    Pattern(PHRASE, "que significa decia", 100),
    Pattern(PHRASE, "quien es decia", 100),
    Pattern(PHRASE, "de donde vienes", 90),
    Pattern(PHRASE, "para que sirves", 90),
    Pattern(PHRASE, "cuales son tus funciones", 90),
    Pattern(PHRASE, "para que estas creada", 90),
]

# Plugin instance - priority 5 per design.md
decia_self_plugin = IntentPlugin(
    name=DECIA_SELF,
    category="IDENTITY",
    patterns=_decia_self_patterns,
    priority=5,
)

# Alias for registry access (mod.plugin)
plugin = decia_self_plugin