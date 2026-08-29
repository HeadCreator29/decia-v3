# brain.plugins.calculate - CALCULATE intent plugin
# Extracted from intent_layer._init_patterns()

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, REGEX, CALCULATE

# Patterns copied verbatim from intent_layer._init_patterns()
_calculate_patterns = [
    Pattern(REGEX,
            r"^[\d\s\+\-\*\/\(\)\.]+$",
            100, entity_group="math"),
    Pattern(REGEX,
            r"^\d+\s*(mas|menos|por|entre|x|×)\s*\d+",
            95, entity_group="math"),
    Pattern(REGEX,
            r"^cuanto\s+es\s+\d+\s*(mas|menos|por|entre|x|×)\s+\d+",
            90, entity_group="math"),
    Pattern(REGEX,
            r"^que\s+es\s+\d+\s*(mas|menos|por|entre|x|×)\s+\d+",
            90, entity_group="math"),
    Pattern(REGEX,
            r"^calcular\s+\d+\s*(mas|menos|por|entre|x|×)\s*\d+",
            90, entity_group="math"),
]

# Plugin instance - priority 5 per design.md
plugin = IntentPlugin(
    name=CALCULATE,
    category="UTILITY",
    patterns=_calculate_patterns,
    priority=5,
    entity_group="math",
)