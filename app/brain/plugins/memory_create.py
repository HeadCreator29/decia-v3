# brain.plugins.memory_create - MEMORY_CREATE intent plugin
# Extracted from intent_layer._init_patterns()

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, PHRASE, MEMORY_CREATE

# Patterns copied verbatim from intent_layer._init_patterns()
_memory_create_patterns = [
    Pattern(PHRASE, "guarda que", 100, entity_group="memory"),
    Pattern(PHRASE, "guarda esto", 100, entity_group="memory"),
    Pattern(PHRASE, "recuerda que", 100, entity_group="memory"),
    Pattern(PHRASE, "recuerda esto", 100, entity_group="memory"),
    Pattern(PHRASE, "anota que", 100, entity_group="memory"),
    Pattern(PHRASE, "anota esto", 100, entity_group="memory"),
    Pattern(PHRASE, "memoriza que", 100, entity_group="memory"),
    Pattern(PHRASE, "quiero que recuerdes", 95, entity_group="memory"),
    Pattern(PHRASE, "quiero que guardes", 95, entity_group="memory"),
]

# Plugin instance - priority 5 per design.md
memory_create_plugin = IntentPlugin(
    name=MEMORY_CREATE,
    category="MEMORY",
    patterns=_memory_create_patterns,
    priority=5,
    entity_group="memory",
)

# Alias for registry access (mod.plugin)
plugin = memory_create_plugin