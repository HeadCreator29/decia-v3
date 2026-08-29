# brain.plugins.free_talk - FREE_TALK intent plugin
# Special case: no patterns, fallback for unmatched conversational input

from brain.plugins.base import IntentPlugin
from brain.intent_types import FREE_TALK

# No patterns - this is a fallback intent handled by classify() logic
_free_talk_patterns = []

# Plugin instance - priority 0 (lowest)
free_talk_plugin = IntentPlugin(
    name=FREE_TALK,
    category="FALLBACK",
    patterns=_free_talk_patterns,
    priority=0,
)

# Alias for registry access (mod.plugin)
plugin = free_talk_plugin