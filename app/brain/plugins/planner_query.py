# brain.plugins.planner_query - PLANNER_QUERY intent plugin
# Extracted from intent_layer._init_patterns()

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, REGEX, PLANNER_QUERY

# Patterns copied verbbatim from intent_layer._init_patterns()
_planner_query_patterns = [
    Pattern(REGEX, r"^que\s+tengo\s+pendiente\b", 90),
    Pattern(REGEX, r"^que\s+tengo\s+que\s+hacer", 90),
    Pattern(REGEX, r"^que\s+debo\s+hacer", 90),
    Pattern(REGEX, r"^que\s+(?:eventos|planes|recordatorios)", 90),
    Pattern(REGEX, r"^que\s+hay", 85),
    Pattern(REGEX, r"^que\s+tengo", 90),
]

# Plugin instance - priority 5 per design.md
planner_query_plugin = IntentPlugin(
    name=PLANNER_QUERY,
    category="PLANNING",
    patterns=_planner_query_patterns,
    priority=5,
)

# Alias for registry access (mod.plugin)
plugin = planner_query_plugin