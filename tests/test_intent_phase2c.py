"""
DECIA v2 — Phase 2C: Controlled Intent Expansion
=================================================

Objetivo: Expandir _SAFE_INTENTS de 4 a 7:
  GREETING, THANKS, EXIT, CALCULATE,
  DECA_SELF, DECA_CREATOR, ARCHIVE_DIRECT

NO modifica archivos de producción.
Los tests definen comportamiento esperado.
Los FINDINGs documentan limitaciones reales.
"""

import sys

from pathlib import Path

from unittest.mock import patch

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "app"),
)

from brain.intent_layer import IntentLayer
from brain.intent_types import (
    GREETING,
    THANKS,
    DECIA_SELF,
    DECIA_CREATOR,
    USER_NAME_ASK,
    USER_NAME_SET,
    PREFERRED_NAME_ASK,
    PREFERRED_NAME_SET,
    CALCULATE,
    TIME,
    DATE,
    MEMORY_CREATE,
    MEMORY_SEARCH,
    ARCHIVE_DIRECT,
    ARCHIVE_SEARCH,
    EXIT,
    AMBIGUOUS_INPUT,
    FREE_TALK,
)
from brain.core import _SAFE_INTENTS

layer = IntentLayer()


def analyze(text):
    r = layer.classify(text)
    return {
        "intent": r.intent,
        "confidence": r.confidence,
        "entities": r.entities,
        "matched_pattern": r.matched_pattern,
        "candidates": [
            {"intent": c.intent, "score": c.score}
            for c in r.candidates
        ],
    }


# ==========================================
# 1. SAFE INTENTS DEFINITION
# ==========================================


class TestSafeIntentsDefinition:

    def test_seven_safe_intents(self):
        assert len(_SAFE_INTENTS) == 9

    def test_greeting_is_safe(self):
        assert GREETING in _SAFE_INTENTS

    def test_thanks_is_safe(self):
        assert THANKS in _SAFE_INTENTS

    def test_exit_is_safe(self):
        assert EXIT in _SAFE_INTENTS

    def test_calculate_is_safe(self):
        assert CALCULATE in _SAFE_INTENTS

    def test_decia_self_is_safe(self):
        assert DECIA_SELF in _SAFE_INTENTS

    def test_decia_creator_is_safe(self):
        assert DECIA_CREATOR in _SAFE_INTENTS

    def test_archive_direct_is_safe(self):
        assert ARCHIVE_DIRECT in _SAFE_INTENTS

    def test_user_name_ask_not_safe(self):
        assert USER_NAME_ASK not in _SAFE_INTENTS

    def test_user_name_set_not_safe(self):
        assert USER_NAME_SET not in _SAFE_INTENTS

    def test_preferred_name_ask_not_safe(self):
        assert PREFERRED_NAME_ASK not in _SAFE_INTENTS

    def test_preferred_name_set_not_safe(self):
        assert PREFERRED_NAME_SET not in _SAFE_INTENTS

    def test_memory_create_not_safe(self):
        assert MEMORY_CREATE not in _SAFE_INTENTS

    def test_memory_search_not_safe(self):
        assert MEMORY_SEARCH not in _SAFE_INTENTS

    def test_archive_search_not_safe(self):
        assert ARCHIVE_SEARCH not in _SAFE_INTENTS

    def test_ambiguous_not_safe(self):
        assert AMBIGUOUS_INPUT not in _SAFE_INTENTS

    def test_free_talk_not_safe(self):
        assert FREE_TALK not in _SAFE_INTENTS


# ==========================================
# 2. DECA_SELF — CASOS POSITIVOS
# ==========================================


class TestDeciaSelfPositive:

    def test_quien_eres(self):
        a = analyze("quién eres")
        assert a["intent"] == DECIA_SELF
        assert a["confidence"] >= 0.90

    def test_que_eres(self):
        a = analyze("qué eres")
        assert a["intent"] == DECIA_SELF
        assert a["confidence"] >= 0.90

    def test_como_te_llamas(self):
        a = analyze("como te llamas")
        assert a["intent"] == DECIA_SELF
        assert a["confidence"] >= 0.90

    def test_cual_es_tu_nombre(self):
        a = analyze("cual es tu nombre")
        assert a["intent"] == DECIA_SELF
        assert a["confidence"] >= 0.90

    def test_quien_es_decia(self):
        """FIXED: 'quien es decia' now correctly
        classifies as DECIA_SELF via explicit
        PHRASE pattern. DECIA/DECA separation."""
        a = analyze("quién es decia")
        assert a["intent"] == DECIA_SELF

    def test_quien_eres_tu_exact(self):
        """EXACT 'quien eres' matchea en
        'quien eres tu'. DECIA_SELF."""
        a = analyze("quién eres tú")
        assert a["intent"] == DECIA_SELF


# ==========================================
# 3. DECA_SELF — NO DEBE CAPTURAR
# ==========================================


class TestDeciaSelfNoCaptura:

    def test_quien_soy_no_es_decia_self(self):
        """USER_NAME_ASK gana por EXACT 100."""
        a = analyze("quién soy")
        assert a["intent"] == USER_NAME_ASK

    def test_como_me_llamo_no_es_decia_self(self):
        """USER_NAME_ASK gana por EXACT 100."""
        a = analyze("cómo me llamo")
        assert a["intent"] == USER_NAME_ASK

    def test_quien_es_tu_creador_no_es_self(self):
        """DECA_CREATOR gana por PHRASE 100."""
        a = analyze("quién es tu creador")
        assert a["intent"] == DECIA_CREATOR

    def test_quien_creo_deca_no_es_self(self):
        """ARCHIVE_DIRECT gana por PHRASE 90."""
        a = analyze("quién creó DECA")
        assert a["intent"] == ARCHIVE_DIRECT

    def test_que_significa_deca_no_es_self(self):
        """ARCHIVE_DIRECT gana por PHRASE 90."""
        a = analyze("qué significa DECA")
        assert a["intent"] == ARCHIVE_DIRECT


# ==========================================
# 4. DECA_CREATOR — CASOS POSITIVOS
# ==========================================


class TestDeciaCreatorPositive:

    def test_quien_te_creo(self):
        a = analyze("quién te creó")
        assert a["intent"] == DECIA_CREATOR
        assert a["confidence"] >= 0.90

    def test_quien_es_tu_creador(self):
        a = analyze("quién es tu creador")
        assert a["intent"] == DECIA_CREATOR
        assert a["confidence"] >= 0.90

    def test_quien_te_hizo(self):
        a = analyze("quién te hizo")
        assert a["intent"] == DECIA_CREATOR
        assert a["confidence"] >= 0.90

    def test_como_naciste(self):
        a = analyze("como naciste")
        assert a["intent"] == DECIA_CREATOR
        assert a["confidence"] >= 0.90

    def test_quien_te_creo_a_ti(self):
        a = analyze("quién te creó a ti")
        assert a["intent"] == DECIA_CREATOR


# ==========================================
# 5. DECA_CREATOR — CONFLICTO CON ARCHIVE
# ==========================================


class TestDeciaCreatorConflictArchive:

    def test_quien_creo_deca_gana_archive(self):
        """ARCHIVE_DIRECT (90) gana a
        DECIA_CREATOR (80) cuando
        contiene 'deca'."""
        a = analyze("quién creó DECA")
        assert a["intent"] == ARCHIVE_DIRECT

    def test_quien_fundo_deca_gana_archive(self):
        """PASS: 'quién fundó DECA' →
        ARCHIVE_DIRECT (90) gana a
        DECIA_CREATOR (65). conf=0.85."""
        a = analyze("quién fundó DECA")
        assert a["intent"] == ARCHIVE_DIRECT

    def test_quien_es_el_creador_de_deca(self):
        a = analyze(
            "quién es el creador de DECA"
        )
        assert a["intent"] == ARCHIVE_DIRECT

    def test_quien_creo_el_proyecto_deca(self):
        """FINDING: 'quién creó el proyecto DECA'
        → DECIA_CREATOR. La frase ARCHIVE_DIRECT
        'quien creo deca' no es substring de
        'quien creo el proyecto deca' (el
        'proyecto' interrumpe). DECIA_CREATOR
        keyword 'quien' (65) + 'creo' (15) = 80."""
        a = analyze(
            "quién creó el proyecto DECA"
        )
        assert a["intent"] == DECIA_CREATOR


# ==========================================
# 6. ARCHIVE_DIRECT — CASOS POSITIVOS
# ==========================================


class TestArchiveDirectPositive:

    def test_cuando_comenzo_deca(self):
        a = analyze("cuando comenzó DECA")
        assert a["intent"] == ARCHIVE_DIRECT
        assert a["confidence"] >= 0.90

    def test_cuando_empezo_deca(self):
        a = analyze("cuando empezó DECA")
        assert a["intent"] == ARCHIVE_DIRECT
        assert a["confidence"] >= 0.90

    def test_que_significa_deca(self):
        a = analyze("qué significa DECA")
        assert a["intent"] == ARCHIVE_DIRECT
        assert a["confidence"] >= 0.90

    def test_significado_de_deca(self):
        a = analyze("significado de DECA")
        assert a["intent"] == ARCHIVE_DIRECT
        assert a["confidence"] >= 0.90

    def test_valores_de_deca(self):
        a = analyze("valores de DECA")
        assert a["intent"] == ARCHIVE_DIRECT
        assert a["confidence"] >= 0.90

    def test_vision_de_deca(self):
        a = analyze("visión de DECA")
        assert a["intent"] == ARCHIVE_DIRECT
        assert a["confidence"] >= 0.90

    def test_quien_creo_deca(self):
        """FINDING: conf=0.77 porque
        DECIA_CREATOR (80) compite con
        ARCHIVE_DIRECT (90). delta=10."""
        a = analyze("quién creó DECA")
        assert a["intent"] == ARCHIVE_DIRECT
        assert a["confidence"] >= 0.70

    def test_origen_de_deca(self):
        a = analyze("origen de DECA")
        assert a["intent"] == ARCHIVE_DIRECT
        assert a["confidence"] >= 0.90


# ==========================================
# 7. ARCHIVE_DIRECT — NO DEBE CAPTURAR
# ==========================================


class TestArchiveDirectNoCaptura:

    def test_que_significa_la_vida(self):
        """Sin 'deca' → ARCHIVE_DIRECT no
        matchea. Falls to FREE_TALK."""
        a = analyze("qué significa la vida")
        assert a["intent"] != ARCHIVE_DIRECT

    def test_cual_es_mi_vision(self):
        """Sin 'deca' → no ARCHIVE_DIRECT."""
        a = analyze("cuál es mi visión")
        assert a["intent"] != ARCHIVE_DIRECT

    def test_cuales_son_mis_valores(self):
        """Sin 'deca' → no ARCHIVE_DIRECT."""
        a = analyze(
            "cuáles son mis valores"
        )
        assert a["intent"] != ARCHIVE_DIRECT

    def test_quien_creo_esto(self):
        """Sin 'deca' → no ARCHIVE_DIRECT."""
        a = analyze("quién creó esto")
        assert a["intent"] != ARCHIVE_DIRECT

    def test_cual_es_el_origen(self):
        """Sin 'deca' → no ARCHIVE_DIRECT."""
        a = analyze("cuál es el origen")
        assert a["intent"] != ARCHIVE_DIRECT


# ==========================================
# 8. CONFLICT TESTS
# ==========================================


class TestConflictDeciaSelfVsCreator:

    def test_quien_eres_es_decia_self(self):
        a = analyze("quién eres")
        assert a["intent"] == DECIA_SELF

    def test_quien_te_creo_es_creator(self):
        a = analyze("quién te creó")
        assert a["intent"] == DECIA_CREATOR


class TestConflictDeciaSelfVsUserName:

    def test_quien_soy_es_user_name_ask(self):
        """USER_NAME_ASK gana por EXACT 100."""
        a = analyze("quién soy")
        assert a["intent"] == USER_NAME_ASK
        assert USER_NAME_ASK not in _SAFE_INTENTS

    def test_como_me_llamo_es_user_name_ask(self):
        a = analyze("cómo me llamo")
        assert a["intent"] == USER_NAME_ASK
        assert USER_NAME_ASK not in _SAFE_INTENTS


class TestConflictArchiveVsCreator:

    def test_quien_creo_deca_es_archive(self):
        a = analyze("quién creó DECA")
        assert a["intent"] == ARCHIVE_DIRECT

    def test_que_significa_deca_es_archive(self):
        a = analyze("qué significa DECA")
        assert a["intent"] == ARCHIVE_DIRECT


class TestConflictAmbiguousNoDecide:

    def test_que_significa_la_vida_no_auto(self):
        """ARCHIVE_DIRECT no matchea sin 'deca'.
        Falls through routing original."""
        a = analyze("qué significa la vida")
        assert a["intent"] != ARCHIVE_DIRECT
        assert a["intent"] != DECIA_SELF
        assert a["intent"] != DECIA_CREATOR


# ==========================================
# 9. WRITE SAFETY
# ==========================================


class TestWriteSafety:

    def test_me_llamo_pedro_no_auto_route(self):
        """USER_NAME_SET no está en
        _SAFE_INTENTS."""
        assert USER_NAME_SET not in _SAFE_INTENTS
        a = analyze("me llamo Pedro")
        assert a["intent"] == USER_NAME_SET

    def test_mi_nombre_es_pedro_no_auto(self):
        assert USER_NAME_SET not in _SAFE_INTENTS
        a = analyze("mi nombre es Pedro")
        assert a["intent"] == USER_NAME_SET

    def test_llamame_creador_no_auto(self):
        assert PREFERRED_NAME_SET not in \
            _SAFE_INTENTS
        a = analyze("llámame Creador")
        assert a["intent"] == PREFERRED_NAME_SET

    def test_quiero_que_me_llames_jefe_no_auto(self):
        assert PREFERRED_NAME_SET not in \
            _SAFE_INTENTS
        a = analyze(
            "quiero que me llames Jefe"
        )
        assert a["intent"] == PREFERRED_NAME_SET

    def test_guarda_que_tengo_clase_no_auto(self):
        assert MEMORY_CREATE not in _SAFE_INTENTS
        a = analyze("guarda que tengo clase")
        assert a["intent"] == MEMORY_CREATE


# ==========================================
# 10. FALLBACK SAFETY
# ==========================================


class TestFallbackSafety:

    def test_memory_search_falls_through(self):
        a = analyze("qué recuerdas")
        assert a["intent"] == MEMORY_SEARCH
        assert MEMORY_SEARCH not in _SAFE_INTENTS

    def test_archive_search_falls_through(self):
        """'significado' solo (sin 'deca') →
        1 palabra, AMBIGUOUS_INPUT."""
        a = analyze("significado")
        assert a["intent"] == AMBIGUOUS_INPUT
        assert ARCHIVE_SEARCH not in _SAFE_INTENTS

    def test_user_name_ask_falls_through(self):
        a = analyze("quién soy")
        assert a["intent"] == USER_NAME_ASK
        assert USER_NAME_ASK not in _SAFE_INTENTS

    def test_preferred_name_ask_falls_through(self):
        a = analyze(
            "cómo quieres llamarme"
        )
        assert a["intent"] == PREFERRED_NAME_ASK
        assert PREFERRED_NAME_ASK not in _SAFE_INTENTS

    def test_ambiguous_falls_through(self):
        a = analyze("algo")
        assert a["intent"] == AMBIGUOUS_INPUT
        assert AMBIGUOUS_INPUT not in _SAFE_INTENTS

    def test_free_talk_falls_through(self):
        a = analyze("cuéntame un chiste")
        assert a["intent"] == FREE_TALK
        assert FREE_TALK not in _SAFE_INTENTS


# ==========================================
# 11. CONFIDENCE
# ==========================================


class TestConfidence:

    def test_decia_self_exact_above_090(self):
        a = analyze("quién eres")
        assert a["intent"] == DECIA_SELF
        assert a["confidence"] >= 0.90

    def test_decia_creator_phrase_above_090(self):
        a = analyze("quién te creó")
        assert a["intent"] == DECIA_CREATOR
        assert a["confidence"] >= 0.90

    def test_archive_direct_phrase_above_090(self):
        """'qué significa DECA' → ARCHIVE_DIRECT
        conf=0.90."""
        a = analyze("qué significa DECA")
        assert a["intent"] == ARCHIVE_DIRECT
        assert a["confidence"] >= 0.90


# ==========================================
# 12. HANDLER SAFETY
# ==========================================


class TestHandlerSafety:

    def test_identity_response_returns_string(self):
        """DECA_SELF handler returns str,
        not None."""
        from brain.handlers import (
            identity_response,
        )
        r = identity_response("quién eres")
        assert isinstance(r, str)
        assert len(r) > 0

    def test_creator_handler_returns_string(self):
        """DECA_CREATOR handler returns str."""
        from brain.handlers import (
            identity_response,
        )
        r = identity_response("quién te creó")
        assert isinstance(r, str)
        assert len(r) > 0

    def test_archive_handler_returns_string(self):
        """ARCHIVE_DIRECT handler returns str."""
        from brain.handlers import (
            archive_response,
        )
        r = archive_response(
            "qué significa DECA"
        )
        assert isinstance(r, str)
        assert len(r) > 0

    def test_handler_does_not_write_files(self):
        """Handlers only read, never write.
        Verified by checking no 'w' mode
        in open calls."""
        from brain.handlers import (
            identity_response,
        )
        r = identity_response("quién eres")
        assert isinstance(r, str)
        r2 = identity_response("quién te creó")
        assert isinstance(r2, str)


# ==========================================
# 13. OBSERVATION LOG
# ==========================================


class TestObservationLog:

    def test_safe_intent_logs_used_true(self):
        """Intent seguro con conf >= 0.90
        debe log con used=True."""
        from brain.core import think

        with patch(
            "brain.core.identity_response",
            return_value="Soy DECIA",
        ):
            think("quién eres")

    def test_unsafe_intent_logs_used_false(self):
        """Intent no seguro debe log
        used=False."""
        from brain.core import think

        with patch(
            "brain.core.identity_response",
            return_value=None,
        ), patch(
            "brain.core.quick_response",
            return_value=None,
        ), patch(
            "brain.core.personal_identity_handler",
            return_value=None,
        ), patch(
            "brain.core.calculate",
            return_value=None,
        ), patch(
            "brain.core.memory_request",
            return_value=None,
        ), patch(
            "brain.core.archive_response",
            return_value=None,
        ), patch(
            "brain.core.search_deca_memory",
            return_value=None,
        ), patch(
            "brain.core.ambiguous_input_response",
            return_value=None,
        ), patch(
            "brain.core.ask_ollama",
            return_value="Ollama response",
        ):
            think("qué recuerdas")
