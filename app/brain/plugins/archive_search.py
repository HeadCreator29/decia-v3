# brain.plugins.archive_search - ARCHIVE_SEARCH intent plugin
# Extracted from intent_layer._init_patterns()

from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, KEYWORD, PHRASE, REGEX, ARCHIVE_SEARCH

# Patterns copied verbatim from intent_layer._init_patterns()
_archive_search_patterns = [
    Pattern(KEYWORD, "significa", 35, {"deca": 10}),
    Pattern(KEYWORD, "significado", 35, {"deca": 10}),
    Pattern(PHRASE, "historia de deca", 85),
    Pattern(PHRASE, "eventos de deca", 85),
    Pattern(REGEX,
            r"que\s+(?:eventos|"
            r"acontecimientos|hechos|"
            r"evento|acontecimiento|hecho)\s+"
            r"(?:sucedio|acontecio|ocurrio|"
            r"sucedieron|acontecieron|"
            r"ocurrieron|pasaron|paso|hubo|"
            r"hubieron|ha\s+pasado|"
            r"han\s+pasado|ha\s+habido|"
            r"han\s+habido)\s+"
            r"(?:(?:con|sobre)\s+.+?\s+)?"
            r"(?:hoy|ayer|anteayer|"
            r"esta\s+semana|"
            r"(?:la\s+)?semana\s+pasada|"
            r"este\s+mes|(?:el\s+)?mes\s+"
            r"pasado|el\s+(?:lunes|martes|"
            r"miercoles|jueves|viernes|"
            r"sabado|domingo)|"
            r"hace\s+(?:una?|\d+)\s+"
            r"(?:dia|dias|semana|semanas|"
            r"mes|meses))\b",
            75),
    Pattern(REGEX,
            r"que\s+acontecio\s+"
            r"(?:(?:con|sobre)\s+.+?\s+)?"
            r"(?:hoy|ayer|anteayer|"
            r"esta\s+semana|"
            r"(?:la\s+)?semana\s+pasada|"
            r"este\s+mes|(?:el\s+)?mes\s+"
            r"pasado|el\s+(?:lunes|martes|"
            r"miercoles|jueves|viernes|"
            r"sabado|domingo)|"
            r"hace\s+(?:una?|\d+)\s+"
            r"(?:dia|dias|semana|semanas|"
            r"mes|meses))\b",
            75),
    Pattern(REGEX,
            r"que\s+(?:eventos|"
            r"acontecimientos|"
            r"acontecimiento|evento|"
            r"hechos|hecho)\s+"
            r"(?:sucedio|acontecio|"
            r"ocurrio|sucedieron|"
            r"acontecieron|ocurrieron|"
            r"pasaron|paso|hubo|hubieron|"
            r"ha\s+pasado|han\s+pasado|"
            r"ha\s+habido|han\s+habido)"
            r"\s+(?:sobre|con)\s+\S+",
            75),
    Pattern(REGEX,
            r"cual(?:es)?\s+son\s+(?:los\s+)?(?:valores|principios)"
            r"(?!\s+d(?:e|el)\s+(?!deca\b))",
            60),
    Pattern(REGEX,
            r"objetivos?\s+(?:de\s+|tiene\s+)?deca\b",
            85),
    Pattern(KEYWORD, "recuerda", 35, {"deca": 15}),
    Pattern(KEYWORD, "recuerdo", 35, {"deca": 15}),
    Pattern(KEYWORD, "memorias", 35, {"deca": 15}),
    Pattern(PHRASE, "que hay registrado", 80),
    Pattern(PHRASE, "que tienes guardado", 80),
    Pattern(PHRASE, "que hay guardado", 80),
    Pattern(PHRASE, "que tienes registrado", 80),
    Pattern(PHRASE, "que hay en el archivo", 85),
    Pattern(PHRASE, "que hay en archivo", 85),
    Pattern(PHRASE, "que tengo guardado", 80),
    Pattern(PHRASE, "que tengo registrado", 80),
    Pattern(REGEX,
            r"que\s+(hay|tienes|tengo)\s+(registrado|guardado|almacenado)",
            80),
    Pattern(REGEX,
            r"que\s+(hay|tienes)\s+en\s+(el\s+)?archivo",
            85),
    Pattern(KEYWORD, "registrado", 45, {"hay": 15, "archivo": 15}),
    Pattern(KEYWORD, "guardado", 45, {"hay": 15, "archivo": 15}),
]

# Plugin instance - priority 5 per design.md
archive_search_plugin = IntentPlugin(
    name=ARCHIVE_SEARCH,
    category="DECA_ARCHIVE",
    patterns=_archive_search_patterns,
    priority=5,
)

# Alias for registry access (mod.plugin)
plugin = archive_search_plugin