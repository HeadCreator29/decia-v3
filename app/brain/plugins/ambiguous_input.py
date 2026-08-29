# brain.plugins.ambiguous_input - AMBIGUOUS_INPUT intent plugin
# Special case: no patterns, fallback for ambiguous/short input

from brain.plugins.base import IntentPlugin
from brain.intent_types import AMBIGUOUS_INPUT

# No patterns - this is a fallback intent handled by classify() logic
_ambiguous_input_patterns = []

# Plugin instance - priority 0 (lowest)
ambiguous_input_plugin = IntentPlugin(
    name=AMBIGUOUS_INPUT,
    category="FALLBACK",
    patterns=_ambiguous_input_patterns,
    priority=0,
)

# Alias for registry access (mod.plugin)
plugin = ambiguous_input_plugin