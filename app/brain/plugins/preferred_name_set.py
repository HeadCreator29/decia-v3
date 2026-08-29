# brain.plugins.preferred_name_set - PREFERRED_NAME_SET intent plugin
# Extracted from intent_layer._init_patterns()

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, REGEX, PREFERRED_NAME_SET

# Patterns copied verbatim from intent_layer._init_patterns()
_preferred_name_set_patterns = [
    Pattern(REGEX, r"puedes llamarme\s+(.+)", 100, entity_group="preferred_name"),
    Pattern(REGEX, r"quiero que me llames\s+(.+)", 100, entity_group="preferred_name"),
    Pattern(REGEX, r"me vas a llamar\s+(.+)", 95, entity_group="preferred_name"),
    Pattern(REGEX, r"vas a llamarme\s+(.+)", 95, entity_group="preferred_name"),
    Pattern(REGEX, r"desde ahora llamame\s+(.+)", 95, entity_group="preferred_name"),
    Pattern(REGEX, r"de ahora en adelante llamame\s+(.+)", 95, entity_group="preferred_name"),
    Pattern(REGEX, r"llamame\s+(.+)", 85, entity_group="preferred_name"),
]

# Plugin instance - priority 5 per design.md
preferred_name_set_plugin = IntentPlugin(
    name=PREFERRED_NAME_SET,
    category="IDENTITY",
    patterns=_preferred_name_set_patterns,
    priority=5,
    entity_group="preferred_name",
)

# Alias for registry access (mod.plugin)
plugin = preferred_name_set_plugin