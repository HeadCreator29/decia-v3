# brain.plugins.memory_search - MEMORY_SEARCH intent plugin
# Extracted from intent_layer._init_patterns()

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, KEYWORD, PHRASE, REGEX, MEMORY_SEARCH

# Patterns copied verbatim from intent_layer._init_patterns()
_memory_search_patterns = [
    Pattern(KEYWORD, "recuerdame", 70),
    Pattern(KEYWORD, "hoy", 30,
            {"recuerdas": 25,
             "hablado": 25}),
    Pattern(KEYWORD, "ayer", 30,
            {"recuerdas": 25}),
    Pattern(REGEX,
            r"me\s+gusta",
            65, entity_group="memory"),
    Pattern(REGEX,
            r"quiero\s+terminar",
            65, entity_group="memory"),
    Pattern(REGEX,
            r"como\s+se\s+llama\s+mi",
            65, entity_group="memory"),
    Pattern(PHRASE,
            "que sabes de mi", 75),
    Pattern(PHRASE,
            "que recuerdas de mi", 75),
    Pattern(PHRASE,
            "que sabes sobre mi", 75),
    Pattern(REGEX,
            r"cual\s+es\s+mi\s+\w+",
            70, entity_group="memory"),
    Pattern(REGEX,
            r"en\s+que\s+proyecto\s+"
            r"(estoy|trabajo|trabajando)",
            70, entity_group="memory"),
    Pattern(PHRASE,
            "que paso hoy", 75),
    Pattern(PHRASE,
            "que paso ayer", 75),
    Pattern(REGEX,
            r"^que\s+paso\b(?:$|\s+(?:con|sobre)\s+\S+)",
            60),
    Pattern(REGEX,
            r"que\s+paso\s+(hoy|ayer|anteayer|\s+(?:semana|la\s+semana)\s+pasada)",
            75),
    Pattern(REGEX,
            r"que\s+(hicimos|hice|habiamos\s+hecho)"
            r"(?:\s+(hoy|ayer|anteayer|\s+(?:semana|la\s+semana)\s+pasada))?",
            75),
    Pattern(REGEX,
            r"que\s+hizo\b",
            60),
    Pattern(REGEX,
            r"(?:de\s+)?que\s+(?:hemos\s+)?habl(?:amos|ado)\b",
            70),
    Pattern(REGEX,
            r"que\s+(?:(?:te\s+)?dije|"
            r"(?:me\s+)?dijiste)"
            r"(?:\s+(hoy|ayer|anteayer|\s+(?:semana|la\s+semana)\s+pasada))?",
            70),
    Pattern(REGEX,
            r"(?:me\s+)?dijiste\s+algo\b",
            70),
    Pattern(KEYWORD, "paso", 40,
            {"hoy": 20, "ayer": 20}),
    Pattern(REGEX,
            r"que\s+(?:cosas\s+)?recuerd[ao]s?\b",
            75),
    Pattern(REGEX,
            r"que\s+recuerd[ao]s?\s+(?:sobre|de)\s+\S+",
            80),
    Pattern(REGEX,
            r"recuerdas\s+(?:algo\s+)?"
            r"(?:sobre|de)\s+\S+",
            75),
    Pattern(REGEX,
            r"recuerd[ao]\s+lo\b",
            70),
    Pattern(REGEX,
            r"tienes?\s+(?:algun[oa]\s+)?"
            r"(?:en\s+|de\s+)?(?:la\s+)?"
            r"memorias?",
            70),
    Pattern(REGEX,
            r"que\s+memorias?\s+tienes",
            70),
    Pattern(KEYWORD, "acuerdas", 65,
            {"de": 10}),
]

# Plugin instance - priority 5 per design.md
memory_search_plugin = IntentPlugin(
    name=MEMORY_SEARCH,
    category="MEMORY",
    patterns=_memory_search_patterns,
    priority=5,
    entity_group="memory",
)

# Alias for registry access (mod.plugin)
plugin = memory_search_plugin