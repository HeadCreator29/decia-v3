# app/brain/plugins/reflection_approve.py - REFLECTION_APPROVE Intent Plugin
# Patterns: "aprobar reflexión", "confirmar reflexión", "publicar reflexión", "aceptar borrador"
# Intent: REFLECTION_APPROVE
# Priority: 5
# Entity group: reflection_id
# Normalized patterns: "aprobar reflexion", "confirmar reflexion", "publicar reflexion", "aceptar borrador"

import re
from brain.plugins.base import IntentPlugin
from brain.intent_types import Pattern, EXACT, PHRASE, REGEX, KEYWORD, REFLECTION_APPROVE

# REFLECTION_APPROVE intent patterns - priority 5 per design.md
_reflection_approve_patterns = [
    # "aprobar reflexión" - approve reflection (normalized: "aprobar reflexion")
    Pattern(
        PHRASE,
        "aprobar reflexion",
        95,
        entity_group="reflection_id",
        boosts={"aprobar": 10, "reflexion": 5},
    ),
    # "confirmar reflexión" - confirm reflection (normalized: "confirmar reflexion")
    Pattern(
        PHRASE,
        "confirmar reflexion",
        90,
        entity_group="reflection_id",
        boosts={"confirmar": 10, "reflexion": 5},
    ),
    # "publicar reflexión" - publish reflection (normalized: "publicar reflexion")
    Pattern(
        PHRASE,
        "publicar reflexion",
        88,
        entity_group="reflection_id",
        boosts={"publicar": 10, "reflexion": 5},
    ),
    # "aceptar borrador" - accept draft (normalized: "aceptar borrador")
    Pattern(
        PHRASE,
        "aceptar borrador",
        92,
        entity_group="reflection_id",
        boosts={"aceptar": 10, "borrador": 5},
    ),
    # "aprobar" - approve (standalone)
    Pattern(
        PHRASE,
        "aprobar",
        75,
        entity_group="reflection_id",
        boosts={"aprobar": 5},
    ),
    # "confirmar" - confirm (standalone)
    Pattern(
        PHRASE,
        "confirmar",
        72,
        entity_group="reflection_id",
        boosts={"confirmar": 5},
    ),
]

# Plugin instance - priority 5 per design.md
reflection_approve_plugin = IntentPlugin(
    name=REFLECTION_APPROVE,
    category="REFLECTION",
    patterns=_reflection_approve_patterns,
    priority=5,
    entity_group="reflection_id",
)

# Alias for registry access (mod.plugin)
plugin = reflection_approve_plugin