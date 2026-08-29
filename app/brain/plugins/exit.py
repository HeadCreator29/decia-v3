# brain.plugins.exit - EXIT intent plugin
# Extracted from intent_layer._init_patterns() + special logic

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, EXACT, PHRASE, EXIT, REGEX

# Patterns copied verbatim from intent_layer._init_patterns()
_exit_patterns = [
    Pattern(EXACT, "salir", 100),
    Pattern(EXACT, "exit", 100),
    Pattern(EXACT, "quit", 100),
    Pattern(EXACT, "adios", 100,
            word_boundary=True),
    Pattern(PHRASE, "salir por favor", 90),
    Pattern(EXACT, "quiero salir", 90),
    Pattern(PHRASE, "hasta luego", 90),
    Pattern(PHRASE, "nos vemos", 90),
    Pattern(PHRASE, "hasta manana", 90),
    Pattern(PHRASE, "me voy a dormir", 85),
    Pattern(REGEX,
            r"^(?:ya\s+)?me\s+voy"
            r"\s*[.!?]*$",
            90),
]

# Plugin instance - priority 10 per design.md
exit_plugin = IntentPlugin(
    name=EXIT,
    category="SOCIAL",
    patterns=_exit_patterns,
    priority=10,
)

# Alias for registry access (mod.plugin)
plugin = exit_plugin


# EXIT validate() - returns False when message contains "no" before "salir"
# preventing exit intent from triggering when the user is negating the command
def _check_exit_negation(message: str) -> bool:
    """Check if message contains exit negation ("no" before "salir").

    Returns True if negation detected (exit should be blocked),
    False otherwise (exit validation passes).
    """
    normalized = message.lower().strip()

    if "no" not in normalized:
        return False  # no negation - validation passes

    if "salir" not in normalized:
        return False  # no "salir" - validation passes

    idx_no = normalized.find("no")
    idx_salir = normalized.find("salir")

    return idx_no < idx_salir


# Override the plugin's validate method
# Returns False when exit negation is detected (no antes de salir)
exit_plugin.validate = lambda message, entities: not _check_exit_negation(message)