from dataclasses import dataclass


# ==========================================
# TIPOS DE INTENT
# ==========================================


SOCIAL = "SOCIAL"
DECIA_IDENTITY = "DECIA_IDENTITY"
USER_IDENTITY = "USER_IDENTITY"
UTILITY = "UTILITY"
MEMORY = "MEMORY"
DECA_ARCHIVE = "DECA_ARCHIVE"
NAVIGATION = "NAVIGATION"
AMBIGUOUS = "AMBIGUOUS"
CONVERSATION = "CONVERSATION"


# ==========================================
# NOMBRES DE INTENT
# ==========================================


GREETING = "GREETING"
THANKS = "THANKS"
DECIA_SELF = "DECIA_SELF"
DECIA_CREATOR = "DECIA_CREATOR"
USER_NAME_ASK = "USER_NAME_ASK"
USER_NAME_SET = "USER_NAME_SET"
PREFERRED_NAME_ASK = "PREFERRED_NAME_ASK"
PREFERRED_NAME_SET = "PREFERRED_NAME_SET"
CALCULATE = "CALCULATE"
TIME = "TIME"
DATE = "DATE"
MEMORY_CREATE = "MEMORY_CREATE"
MEMORY_SEARCH = "MEMORY_SEARCH"
ARCHIVE_DIRECT = "ARCHIVE_DIRECT"
ARCHIVE_SEARCH = "ARCHIVE_SEARCH"
EXIT = "EXIT"
AMBIGUOUS_INPUT = "AMBIGUOUS_INPUT"
FREE_TALK = "FREE_TALK"
PLANNER_CREATE = "PLANNER_CREATE"
PLANNER_QUERY = "PLANNER_QUERY"
DECISION_CREATE = "DECISION_CREATE"
DECISION_CONFIRM = "DECISION_CONFIRM"
PREDICTION_CREATE = "PREDICTION_CREATE"
PREDICTION_REVIEW = "PREDICTION_REVIEW"
LEARNING_CREATE = "LEARNING_CREATE"
REFLECTION_CREATE = "REFLECTION_CREATE"
REFLECTION_APPROVE = "REFLECTION_APPROVE"
IDENTITY_PROPOSE = "IDENTITY_PROPOSE"
IDENTITY_APPROVE = "IDENTITY_APPROVE"
TEMPORAL_QUERY = "TEMPORAL_QUERY"
PATTERN_SUGGEST = "PATTERN_SUGGEST"


# ==========================================
# TIPOS DE PATRÓN
# ==========================================


EXACT = "exact"
PHRASE = "phrase"
REGEX = "regex"
KEYWORD = "keyword"


# ==========================================
# UMBRALES DE CONFIDENCE
# ==========================================


CONFIDENCE_SEGURO = 0.90
CONFIDENCE_PROBABLE = 0.70
CONFIDENCE_AMBIGUO = 0.50


# ==========================================
# PATRÓN DE DETECCIÓN
# ==========================================


@dataclass
class Pattern:

    type: str
    value: str
    weight: int
    boosts: dict = None
    entity_group: str = None
    word_boundary: bool = False

    def __post_init__(self):

        if self.boosts is None:

            self.boosts = {}


# ==========================================
# CANDIDATO
# ==========================================


@dataclass
class Candidate:

    intent: str
    score: int
    matched_pattern: str
    matched_type: str
    entities: dict


# ==========================================
# RESULTADO DE CLASIFICACIÓN
# ==========================================


@dataclass
class ClassifyResult:

    intent: str
    confidence: float
    entities: dict
    matched_pattern: str
    candidates: list
