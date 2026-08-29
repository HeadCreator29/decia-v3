# brain.plugins.archive_direct - ARCHIVE_DIRECT intent plugin
# Extracted from intent_layer._init_patterns()

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, PHRASE, REGEX, ARCHIVE_DIRECT

# Patterns copied verbatim from intent_layer._init_patterns_
_archive_direct_patterns = [
    Pattern(PHRASE, "cuando comenzo deca", 90),
    Pattern(PHRASE, "cuando empezo deca", 90),
    Pattern(PHRASE, "que significa deca", 90),
    Pattern(PHRASE, "significado de deca", 90),
    Pattern(PHRASE, "valores de deca", 90),
    Pattern(PHRASE, "cuales son los valores de deca", 90),
    Pattern(PHRASE, "vision de deca", 90),
    Pattern(PHRASE, "cual es la vision de deca", 90),
    Pattern(PHRASE, "quien creo deca", 90),
    Pattern(PHRASE, "quien es el creador de deca", 90),
    Pattern(PHRASE, "origen de deca", 90),
    Pattern(PHRASE, "quien fundo deca", 90),
    Pattern(PHRASE, "hablame de deca", 90),
    Pattern(PHRASE, "cuentame de deca", 90),
    Pattern(PHRASE, "cuentame un poco sobre deca", 90),
    Pattern(PHRASE, "que es deca", 90),
    Pattern(PHRASE, "cuentame sobre deca", 90),
    Pattern(PHRASE, "hablame sobre deca", 90),
    Pattern(PHRASE, "fundador de deca", 90),
    Pattern(PHRASE, "quien es el fundador de deca", 90),
    Pattern(PHRASE, "principios de deca", 90),
    Pattern(REGEX, r"inicio\s+(?:de\s+)?deca\b", 90),
    Pattern(REGEX, r"nacio\s+deca\b", 90),
]

# Plugin instance - priority 5 per design.md
archive_direct_plugin = IntentPlugin(
    name=ARCHIVE_DIRECT,
    category="DECA_ARCHIVE",
    patterns=_archive_direct_patterns,
    priority=5,
)

# Alias for registry access (mod.plugin)
plugin = archive_direct_plugin