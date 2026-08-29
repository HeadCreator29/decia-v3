# brain.plugins.user_name_set - USER_NAME_SET intent plugin
# Extracted from intent_layer._init_patterns()

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, REGEX, USER_NAME_SET

# Patterns copied verbatim from intent_layer._init_patterns()
_user_name_set_patterns = [
    Pattern(REGEX, r"mi nombre es\s+(.+)", 100, entity_group="user_name"),
    Pattern(REGEX, r"el nombre mio es\s+(.+)", 95, entity_group="user_name"),
    Pattern(REGEX, r"nombre mio es\s+(.+)", 95, entity_group="user_name"),
    Pattern(REGEX, r"me llamo\s+(.+)", 90, entity_group="user_name"),
    Pattern(REGEX, r"yo me llamo\s+(.+)", 90, entity_group="user_name"),
    Pattern(REGEX, r"el mio es\s+(.+)", 85, entity_group="user_name"),
    Pattern(REGEX, r"ese es mi nombre\s+(.+)", 85, entity_group="user_name"),
]

# Plugin instance - priority 5 per design.md
user_name_set_plugin = IntentPlugin(
    name=USER_NAME_SET,
    category="IDENTITY",
    patterns=_user_name_set_patterns,
    priority=5,
    entity_group="user_name",
)

# Alias for registry access (mod.plugin)
plugin = user_name_set_plugin