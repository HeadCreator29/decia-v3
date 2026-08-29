"""
DECIA v2 — Phase 2B: Intent Layer Stress Test
==============================================

Objetivo: Intentar romper la clasificación y
documentar hallazgos.

NO modifica ningún archivo de producción.

Categorías:
  A) PASS     — comportamiento correcto
  B) FINDING  — limitación o mejora posible
  C) REGRESSION — comportamiento que contradice
                   una regla que ya funcionaba
"""

import sys

from pathlib import Path

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
    CONFIDENCE_SEGURO,
)
from brain.core import _SAFE_INTENTS


il = IntentLayer()


def analyze(phrase):
    """Clasificar y retornar info completa."""
    r = il.classify(phrase)
    second = (
        r.candidates[1]
        if len(r.candidates) > 1
        else None
    )
    return {
        "intent": r.intent,
        "confidence": r.confidence,
        "matched_pattern": r.matched_pattern,
        "entities": r.entities,
        "candidates": [
            (c.intent, c.score) for c in r.candidates
        ],
        "second": second,
        "delta": (
            r.candidates[0].score - second.score
            if second
            else r.candidates[0].score
            if r.candidates
            else 0
        ),
        "would_auto_route": (
            r.intent in _SAFE_INTENTS
            and r.confidence >= 0.90
        ),
    }


# ==========================================
# 1. SAFE INTENTS
# ==========================================


class TestSafeGreeting:

    def test_hola(self):
        a = analyze("hola")
        assert a["intent"] == GREETING
        assert a["confidence"] >= 0.90
        assert a["would_auto_route"]

    def test_buenas(self):
        a = analyze("buenas")
        assert a["intent"] == GREETING
        assert a["confidence"] >= 0.90
        assert a["would_auto_route"]

    def test_buenos_dias(self):
        a = analyze("buenos dias")
        assert a["intent"] == GREETING
        assert a["confidence"] >= 0.90
        assert a["would_auto_route"]

    def test_buenas_tardes(self):
        a = analyze("buenas tardes")
        assert a["intent"] == GREETING
        assert a["confidence"] >= 0.90
        assert a["would_auto_route"]

    def test_buenas_noches(self):
        a = analyze("buenas noches")
        assert a["intent"] == GREETING
        assert a["confidence"] >= 0.90
        assert a["would_auto_route"]

    def test_hola_decia(self):
        """PASS (FIXED 2B.1): 'hola' con
        word_boundary matchea en 'hola decia'.
        GREETING con conf >= 0.90."""
        a = analyze("hola decia")
        assert a["intent"] == GREETING
        assert a["confidence"] >= 0.90

    def test_hola_que_tal(self):
        """PASS (FIXED 2B.1): 'hola' con
        word_boundary matchea en 'hola que tal'.
        GREETING con conf >= 0.90."""
        a = analyze("hola que tal")
        assert a["intent"] == GREETING
        assert a["confidence"] >= 0.90

    def test_oye_hola(self):
        """PASS (FIXED 2B.1): 'hola' con
        word_boundary matchea al final de
        'oye hola'. GREETING con conf >= 0.90."""
        a = analyze("oye hola")
        assert a["intent"] == GREETING
        assert a["confidence"] >= 0.90


class TestSafeThanks:

    def test_gracias(self):
        a = analyze("gracias")
        assert a["intent"] == THANKS
        assert a["confidence"] >= 0.90
        assert a["would_auto_route"]

    def test_muchas_gracias(self):
        a = analyze("muchas gracias")
        assert a["intent"] == THANKS
        assert a["confidence"] >= 0.90
        assert a["would_auto_route"]

    def test_gracias_de_verdad(self):
        """Phase 2E fix: 'gracias de verdad' → THANKS.
        PHRASE 'gracias' matches substring."""
        a = analyze("gracias de verdad")
        assert a["intent"] == THANKS

    def test_te_doy_las_gracias(self):
        """FINDING: No hay patrón para
        'te doy las gracias'. No activa
        THANKS. Caerá a AMBIGUOUS o FREE_TALK."""
        a = analyze("te doy las gracias")
        assert a["intent"] in (
            THANKS, AMBIGUOUS_INPUT, FREE_TALK,
        )


class TestSafeCalculate:

    def test_2plus2(self):
        a = analyze("2+2")
        assert a["intent"] == CALCULATE
        assert a["confidence"] >= 0.90
        assert a["entities"]["math"] == "2+2"
        assert a["would_auto_route"]

    def test_3star4plus1(self):
        a = analyze("3*4+1")
        assert a["intent"] == CALCULATE
        assert a["confidence"] >= 0.90
        assert a["entities"]["math"] == "3*4+1"
        assert a["would_auto_route"]

    def test_division_complex(self):
        a = analyze("(10-2)/4")
        assert a["intent"] == CALCULATE
        assert a["confidence"] >= 0.90
        assert a["entities"]["math"] == "(10-2)/4"
        assert a["would_auto_route"]

    def test_division_with_spaces(self):
        a = analyze("10 / 2")
        assert a["intent"] == CALCULATE
        assert a["confidence"] >= 0.90
        assert a["entities"]["math"] == "10 / 2"

    def test_subtraction_with_spaces(self):
        a = analyze("100 - 25")
        assert a["intent"] == CALCULATE
        assert a["confidence"] >= 0.90
        assert a["entities"]["math"] == "100 - 25"

    def test_decimal_multiply(self):
        """PASS (FIXED 2B.1): '2.5 * 4' preserva
        el punto decimal en entity math.
        Antes se normalizaba a '25 * 4'."""
        a = analyze("2.5 * 4")
        assert a["intent"] == CALCULATE
        assert a["confidence"] >= 0.90
        assert a["entities"]["math"] == "2.5 * 4"


class TestSafeExit:

    def test_salir(self):
        a = analyze("salir")
        assert a["intent"] == EXIT
        assert a["confidence"] >= 0.90
        assert a["would_auto_route"]

    def test_exit(self):
        a = analyze("exit")
        assert a["intent"] == EXIT
        assert a["confidence"] >= 0.90
        assert a["would_auto_route"]

    def test_quit(self):
        a = analyze("quit")
        assert a["intent"] == EXIT
        assert a["confidence"] >= 0.90
        assert a["would_auto_route"]


# ==========================================
# 2. FALSOS POSITIVOS
# ==========================================


class TestFalsePositivesTemporal:

    def test_hoy_me_siento_genial(self):
        """PASS: 'hoy' con base baja (30),
        sin boost de memoria → FREE_TALK."""
        a = analyze("hoy me siento genial")
        assert a["intent"] == FREE_TALK
        assert a["intent"] != MEMORY_SEARCH
        assert a["intent"] != MEMORY_CREATE

    def test_hoy_fui_al_trabajo(self):
        """PASS: 'hoy' solo, sin contexto."""
        a = analyze("hoy fui al trabajo")
        assert a["intent"] == FREE_TALK
        assert a["intent"] != MEMORY_SEARCH

    def test_ayer_fui_al_supermercado(self):
        """PASS: 'ayer' con base baja (30),
        sin contexto de memoria → FREE_TALK."""
        a = analyze("ayer fui al supermercado")
        assert a["intent"] == FREE_TALK
        assert a["intent"] != MEMORY_SEARCH

    def test_ayer_estaba_cansado(self):
        a = analyze("ayer estaba cansado")
        assert a["intent"] == FREE_TALK
        assert a["intent"] != MEMORY_SEARCH


class TestFalsePositivesSignifica:

    def test_que_significa_la_vida(self):
        """PASS: 'significa' base 35, sin
        boost deca → no alcanza 50 → FREE_TALK."""
        a = analyze("que significa la vida")
        assert a["intent"] == FREE_TALK
        assert a["intent"] != ARCHIVE_SEARCH
        assert a["intent"] != ARCHIVE_DIRECT

    def test_que_significa_esto(self):
        a = analyze("que significa esto")
        assert a["intent"] == FREE_TALK
        assert a["intent"] != ARCHIVE_DIRECT

    def test_cual_es_el_significado_de_todo(self):
        """PASS: 'significado' base 35, sin
        boost deca → FREE_TALK."""
        a = analyze(
            "cual es el significado de todo"
        )
        assert a["intent"] == FREE_TALK
        assert a["intent"] != ARCHIVE_DIRECT


class TestFalsePositivesMisc:

    def test_recuerda_suelto(self):
        """PASS: 'recuerda' como keyword activa
        MEMORY_SEARCH (70) o ARCHIVE_SEARCH (35).
        Sin memoria/DECA context → MEMORY_SEARCH."""
        a = analyze("recuerda")
        assert a["intent"] in (
            MEMORY_SEARCH, AMBIGUOUS_INPUT,
        )

    def test_recuerda_esto(self):
        """PASS: MEMORY_CREATE sin entidad →
        score=0 → AMBIGUOUS_INPUT."""
        a = analyze("recuerda esto")
        assert a["intent"] == AMBIGUOUS_INPUT

    def test_deca_suelto(self):
        """PASS: 'deca' sin contexto no activa
        ARCHIVE_DIRECT. Sin patrón propio."""
        a = analyze("DECA")
        assert a["intent"] in (
            AMBIGUOUS_INPUT, ARCHIVE_SEARCH,
        )

    def test_algo(self):
        a = analyze("algo")
        assert a["intent"] == AMBIGUOUS_INPUT

    def test_mira(self):
        a = analyze("mira")
        assert a["intent"] == AMBIGUOUS_INPUT


# ==========================================
# 3. CONFLICTOS
# ==========================================


class TestConflicts:

    def test_quien_creo_deca(self):
        """PASS: ARCHIVE_DIRECT (PHRASE 90) vence
        a DECIA_CREATOR (KEYWORD ~80)."""
        a = analyze("quien creo deca")
        assert a["intent"] == ARCHIVE_DIRECT
        assert a["confidence"] >= 0.70

    def test_que_significa_deca(self):
        """PASS: ARCHIVE_DIRECT (PHRASE 90) vence
        a ARCHIVE_SEARCH (KEYWORD 70)."""
        a = analyze("que significa deca")
        assert a["intent"] == ARCHIVE_DIRECT
        assert a["confidence"] >= 0.70

    def test_recuerda_que_tengo_clase(self):
        """PASS: MEMORY_CREATE (PHRASE 100)
        vence a MEMORY_SEARCH (KEYWORD ~65)."""
        a = analyze("recuerda que tengo clase")
        assert a["intent"] == MEMORY_CREATE
        assert a["confidence"] >= 0.90

    def test_que_recuerdas(self):
        """PASS: MEMORY_SEARCH gana."""
        a = analyze("que recuerdas")
        assert a["intent"] == MEMORY_SEARCH

    def test_quien_soy(self):
        """PASS: USER_NAME_ASK vence a
        DECIA_SELF. Confidence = 0.85 (< 0.90)
        porque 'quien' como KEYWORD en
        DECIA_CREATOR genera segundo candidato
        con score alto, reduciendo delta."""
        a = analyze("quien soy")
        assert a["intent"] == USER_NAME_ASK
        assert a["confidence"] >= 0.70

    def test_quien_eres(self):
        """PASS: DECIA_SELF gana."""
        a = analyze("quien eres")
        assert a["intent"] == DECIA_SELF
        assert a["confidence"] >= 0.90

    def test_que_hizo_deca(self):
        """FINDING: 'hizo' activa MEMORY_SEARCH
        (score 60) vs ARCHIVE_SEARCH (sin boost
        suficiente). MEMORY_SEARCH gana.
        Posible mejora: ARCHIVE_SEARCH con boost
        deca para 'hizo'."""
        a = analyze("que hizo deca")
        assert a["intent"] in (
            MEMORY_SEARCH, ARCHIVE_SEARCH,
        )

    def test_historia_de_deca(self):
        """Phase 2C: ARCHIVE_SEARCH (KEYWORD 50 +
        boost deca 10 = 60). Confidence lowered
        due to reduced deca boost."""
        a = analyze("historia de deca")
        assert a["intent"] == ARCHIVE_SEARCH
        assert a["confidence"] >= 0.50


# ==========================================
# 4. ESCRITURAS
# ==========================================


class TestWriteIntentsComplete:

    def test_mi_nombre_es_pedro(self):
        a = analyze("mi nombre es pedro")
        assert a["intent"] == USER_NAME_SET
        assert a["confidence"] >= 0.90
        assert a["entities"]["user_name"] == "Pedro"

    def test_me_llamo_pedro(self):
        a = analyze("me llamo pedro")
        assert a["intent"] == USER_NAME_SET
        assert a["confidence"] >= 0.70
        assert "user_name" in a["entities"]

    def test_yo_me_llamo_pedro(self):
        a = analyze("yo me llamo pedro")
        assert a["intent"] == USER_NAME_SET
        assert "user_name" in a["entities"]

    def test_llamame_creador(self):
        a = analyze("llamame creador")
        assert a["intent"] == PREFERRED_NAME_SET
        assert a["confidence"] >= 0.70
        assert "preferred_name" in a["entities"]

    def test_puedes_llamarme_creador(self):
        a = analyze("puedes llamarme creador")
        assert a["intent"] == PREFERRED_NAME_SET
        assert "preferred_name" in a["entities"]

    def test_guarda_que_tengo_clase(self):
        a = analyze("guarda que tengo clase")
        assert a["intent"] == MEMORY_CREATE
        assert a["confidence"] >= 0.90
        assert a["entities"]["memory"] == \
            "tengo clase"

    def test_recuerda_que_manana_gym(self):
        a = analyze(
            "recuerda que manana voy al gimnasio"
        )
        assert a["intent"] == MEMORY_CREATE
        assert "memory" in a["entities"]

    def test_memoriza_que_debo_comprar_pan(self):
        a = analyze(
            "memoriza que debo comprar pan"
        )
        assert a["intent"] == MEMORY_CREATE
        assert "memory" in a["entities"]


class TestWriteIntentsIncomplete:

    def test_mi_nombre_es_vacio(self):
        """PASS: 'mi nombre es' sin entidad.
        REGEX no captura grupo → entity vacía →
        score=0 → AMBIGUOUS_INPUT."""
        a = analyze("mi nombre es")
        assert a["intent"] != USER_NAME_SET
        assert "user_name" not in a["entities"]

    def test_me_llamo_vacio(self):
        """PASS: 'me llamo' sin nombre.
        REGEX no captura grupo → score=0."""
        a = analyze("me llamo")
        assert a["intent"] != USER_NAME_SET
        assert "user_name" not in a["entities"]

    def test_llamame_vacio(self):
        """PASS: 'llamame' sin nombre.
        REGEX no captura grupo → score=0."""
        a = analyze("llamame")
        assert a["intent"] != PREFERRED_NAME_SET
        assert "preferred_name" not in a["entities"]

    def test_guarda_esto(self):
        """PASS: MEMORY_CREATE sin entidad
        extraíble → score=0 → AMBIGUOUS_INPUT."""
        a = analyze("guarda esto")
        assert a["intent"] == AMBIGUOUS_INPUT

    def test_recuerda_esto(self):
        """PASS: MEMORY_CREATE sin entidad →
        score=0 → AMBIGUOUS_INPUT."""
        a = analyze("recuerda esto")
        assert a["intent"] == AMBIGUOUS_INPUT


# ==========================================
# 5. WHISPER-LIKE INPUTS
# ==========================================


class TestWhisperLikeInputs:

    def test_kien_eres(self):
        """FINDING: 'kien' ≠ 'quien' (spelling,
        no accent). No match. 2 palabras →
        AMBIGUOUS_INPUT. La Intent Layer NO
        corrige errores ortográficos."""
        a = analyze("kien eres")
        assert a["intent"] in (
            AMBIGUOUS_INPUT, DECIA_SELF,
        )

    def test_kien_te_creo(self):
        """FINDING: 'kien' ≠ 'quien'. Sin match
        para DECIA_CREATOR. 'creo' como keyword
        en ARCHIVE_SEARCH (score 60) gana.
        Resultado inesperado: ARCHIVE_SEARCH."""
        a = analyze("kien te creo")
        assert a["intent"] in (
            FREE_TALK, DECIA_CREATOR,
            ARCHIVE_SEARCH,
        )

    def test_como_me_llamo(self):
        """PASS: 'como' se normaliza igual.
        Sin acentos en esta frase → match."""
        a = analyze("como me llamo")
        assert a["intent"] in (
            USER_NAME_ASK, USER_NAME_SET,
        )

    def test_llamame_creador(self):
        """PASS: Sin acentos en esta frase.
        REGEX captura 'creador'."""
        a = analyze("llamame creador")
        assert a["intent"] == PREFERRED_NAME_SET
        assert "preferred_name" in a["entities"]

    def test_grasias(self):
        """FINDING: 'grasias' ≠ 'gracias'.
        Misspelling. No match para THANKS.
        1 palabra → AMBIGUOUS_INPUT."""
        a = analyze("grasias")
        assert a["intent"] in (
            THANKS, AMBIGUOUS_INPUT,
        )

    def test_buenas_dias(self):
        """PASS: Sin tildes funciona igual."""
        a = analyze("buenas dias")
        assert a["intent"] == GREETING
        assert a["confidence"] >= 0.90

    def test_ke_significa_deca(self):
        """FINDING: 'ke' ≠ 'que'. Misspelling.
        'significa' sin boost 'deca' no activa
        ARCHIVE_SEARCH. 'ke' no tiene patrón."""
        a = analyze("ke significa deca")
        assert a["intent"] in (
            ARCHIVE_SEARCH, FREE_TALK,
            AMBIGUOUS_INPUT,
        )

    def test_kien_creo_deca(self):
        """FINDING: 'kien' ≠ 'quien'. Sin match
        para ARCHIVE_DIRECT. 'creo' como keyword
        en ARCHIVE_SEARCH con boost 'deca'."""
        a = analyze("kien creo deca")
        assert a["intent"] in (
            ARCHIVE_DIRECT, ARCHIVE_SEARCH,
            FREE_TALK,
        )


# ==========================================
# 6. FRASES NATURALES
# ==========================================


class TestNaturalPhrases:

    def test_oye_decia_quien_eres(self):
        """PASS: 'quien eres' contenido en la
        frase → DECIA_SELF."""
        a = analyze("oye decia quien eres")
        assert a["intent"] == DECIA_SELF

    def test_decia_dime_quien_eres(self):
        """PASS: 'quien eres' contenido →
        DECIA_SELF."""
        a = analyze("decia dime quien eres")
        assert a["intent"] == DECIA_SELF

    def test_hola_decia_buenos_dias(self):
        """FINDING: 'hola' (EXACT 100) vence a
        'buenos dias' (PHRASE 95).
        GREETING gana por 'hola'. 'buenos dias'
        se ignora como boost."""
        a = analyze("hola decia buenos dias")
        assert a["intent"] == GREETING
        assert a["confidence"] >= 0.90

    def test_oye_muchas_gracias(self):
        """PASS: 'muchas gracias' EXACT 100.
        THANKS gana."""
        a = analyze("oye muchas gracias")
        assert a["intent"] == THANKS
        assert a["confidence"] >= 0.90

    def test_decia_cuanto_es_25_por_4(self):
        """PASS: No match determinista.
        6 palabras → FREE_TALK → Ollama."""
        a = analyze("decia cuanto es 25 por 4")
        assert a["intent"] == FREE_TALK

    def test_oye_que_significa_deca(self):
        """PASS: 'significa' con boost 'deca'."""
        a = analyze("oye que significa deca")
        assert a["intent"] in (
            ARCHIVE_DIRECT, ARCHIVE_SEARCH,
        )

    def test_me_puedes_decir_quien_creo_deca(self):
        """PASS: 'quien creo deca' contenido en
        la frase. ARCHIVE_DIRECT debe ganar."""
        a = analyze(
            "me puedes decir quien creo deca"
        )
        assert a["intent"] == ARCHIVE_DIRECT

    def test_dime_como_me_llamo(self):
        """PASS: 'como me llamo' contenido.
        USER_NAME_ASK debe ganar."""
        a = analyze("dime como me llamo")
        assert a["intent"] == USER_NAME_ASK

    def test_quiero_que_recuerdes_manana_reunion(
        self,
    ):
        """PASS: 'quiero que recuerdes' activa
        MEMORY_CREATE. 'manana tengo una reunion'
        es la memoria."""
        a = analyze(
            "quiero que recuerdes que manana "
            "tengo una re union"
        )
        assert a["intent"] == MEMORY_CREATE
        assert "memory" in a["entities"]


# ==========================================
# 7. EDGE CASES
# ==========================================


class TestEdgeCasesStress:

    def test_empty_string(self):
        a = analyze("")
        assert a["intent"] == AMBIGUOUS_INPUT
        assert a["confidence"] == 1.0

    def test_whitespace_only(self):
        a = analyze("   ")
        assert a["intent"] == AMBIGUOUS_INPUT
        assert a["confidence"] == 1.0

    def test_uppercase_hola(self):
        a = analyze("HOLA")
        assert a["intent"] == GREETING
        assert a["confidence"] >= 0.90

    def test_gracias_with_exclamation(self):
        """PASS: normalize_strict quita '!'."""
        a = analyze("Gracias!")
        assert a["intent"] == THANKS
        assert a["confidence"] >= 0.90

    def test_2plus2_exact(self):
        a = analyze("2+2")
        assert a["intent"] == CALCULATE
        assert a["confidence"] >= 0.90

    def test_deca_uppercase(self):
        """FINDING: 'DECA' (1 palabra) sin
        patrón propio → AMBIGUOUS_INPUT."""
        a = analyze("DECA")
        assert a["intent"] in (
            AMBIGUOUS_INPUT, ARCHIVE_SEARCH,
        )

    def test_hola_with_exclamation(self):
        """PASS: normalize_strict quita '!'."""
        a = analyze("hola!")
        assert a["intent"] == GREETING
        assert a["confidence"] >= 0.90

    def test_salir_with_exclamation(self):
        """PASS: normalize_strict quita '!'."""
        a = analyze("salir!")
        assert a["intent"] == EXIT
        assert a["confidence"] >= 0.90

    def test_one_word_hello(self):
        a = analyze("hola")
        assert a["intent"] == GREETING
        assert len(a["candidates"]) >= 1

    def test_two_words_mixed(self):
        """2 palabras sin match →
        AMBIGUOUS_INPUT."""
        a = analyze("mira esto")
        assert a["intent"] == AMBIGUOUS_INPUT

    def test_three_words_no_match(self):
        """3 palabras sin match → FREE_TALK."""
        a = analyze("cuéntame algo chistoso")
        assert a["intent"] == FREE_TALK

    def test_four_words_no_match(self):
        """4 palabras sin match → FREE_TALK."""
        a = analyze("hoy es un buen día")
        assert a["intent"] in (
            FREE_TALK, MEMORY_SEARCH,
        )


# ==========================================
# 8. DECISION SAFETY
# ==========================================


class TestDecisionSafety:

    def test_only_seven_safe_intents(self):
        """Verificar que los intents seguros
        están en _SAFE_INTENTS."""
        assert len(_SAFE_INTENTS) == 9
        assert _SAFE_INTENTS == {
            GREETING, THANKS, CALCULATE, EXIT,
            TIME, DATE, DECIA_SELF,
            DECIA_CREATOR, ARCHIVE_DIRECT,
        }

    def test_write_intents_never_safe(self):
        """Ningún intent de escritura puede
        estar en _SAFE_INTENTS."""
        assert USER_NAME_SET not in _SAFE_INTENTS
        assert (
            PREFERRED_NAME_SET not in _SAFE_INTENTS
        )
        assert MEMORY_CREATE not in _SAFE_INTENTS

    def test_archive_search_not_safe(self):
        assert ARCHIVE_SEARCH not in _SAFE_INTENTS

    def test_memory_search_not_safe(self):
        assert MEMORY_SEARCH not in _SAFE_INTENTS

    def test_user_asks_not_safe(self):
        assert USER_NAME_ASK not in _SAFE_INTENTS
        assert (
            PREFERRED_NAME_ASK not in _SAFE_INTENTS
        )

    def test_ambiguous_and_free_talk_not_safe(self):
        assert AMBIGUOUS_INPUT not in _SAFE_INTENTS
        assert FREE_TALK not in _SAFE_INTENTS

    def test_all_safe_intents_confidence_above_090(
        self,
    ):
        """Todos los safe intents deben alcanzar
        confidence >= 0.90 con inputs típicos."""
        safe_cases = {
            GREETING: "hola",
            THANKS: "gracias",
            CALCULATE: "2+2",
            EXIT: "salir",
        }

        for intent, phrase in safe_cases.items():

            r = il.classify(phrase)

            assert r.confidence >= 0.90, (
                f"{intent} confidence "
                f"{r.confidence} < 0.90"
            )

    def test_all_high_confidence_are_safe(
        self,
    ):
        """Phase 2C: todo intent con confidence
        >= 0.90 DEBE ser safe intent."""
        test_phrases = [
            "hola", "gracias", "salir", "2+2",
            "quien eres", "quien te creo",
            "cuando comenzo deca",
            "que significa deca",
        ]
        for phrase in test_phrases:
            r = il.classify(phrase)
            if r.confidence >= 0.90:
                assert r.intent in _SAFE_INTENTS, (
                    f"{phrase}: {r.intent} conf="
                    f"{r.confidence} not in "
                    f"_SAFE_INTENTS"
                )

    def test_would_auto_route_true_for_safe(self):
        for phrase in [
            "hola", "gracias", "2+2", "salir",
        ]:

            a = analyze(phrase)

            assert a["would_auto_route"], (
                f"{phrase} should auto-route"
            )

    def test_would_auto_route_false_for_non_safe(
        self,
    ):
        """Phase 2C: these intents are NOT safe
        → should NOT auto-route."""
        non_safe = [
            "como me llamo",
            "guarda que tengo clase",
            "que recuerdas",
            "algo",
            "cuéntame un chiste",
        ]

        for phrase in non_safe:

            a = analyze(phrase)

            assert not a["would_auto_route"], (
                f"{phrase} should NOT auto-route "
                f"intent={a['intent']} "
                f"conf={a['confidence']}"
            )

    def test_calculate_deterministic_source_of_truth(
        self,
    ):
        """calculate() sigue siendo fuente de
        verdad para cálculos. La Intent Layer
        solo clasifica, calculate() ejecuta."""
        from brain.handlers import calculate

        assert calculate("2+2") == "4"
        assert calculate("3*4+1") == "13"

    def test_routing_chain_unchanged(self):
        """Verificar que la cadena de routing
        original sigue intacta."""
        from unittest.mock import patch

        with patch(
            "brain.core.quick_response",
            return_value=None,
        ), patch(
            "brain.core.identity_response",
            return_value="identity",
        ):

            from brain.core import think

            r = think("quien eres")

            assert r == "identity"


# ==========================================
# 9. SCORING ANALYSIS
# ==========================================


class TestScoringAnalysis:

    def test_hola_candidates(self):
        """Análisis de candidatos para 'hola'."""
        a = analyze("hola")
        assert a["intent"] == GREETING
        assert a["candidates"][0] == (
            GREETING, 100
        )
        assert a["delta"] >= 30

    def test_quien_eres_candidates(self):
        """Análisis de candidatos para
        'quién eres'."""
        a = analyze("quien eres")
        assert a["intent"] == DECIA_SELF
        assert a["candidates"][0][0] == DECIA_SELF

    def test_que_significa_deca_candidates(self):
        """Análisis de candidatos para
        'qué significa DECA'."""
        a = analyze("que significa deca")
        assert a["intent"] == ARCHIVE_DIRECT
        assert len(a["candidates"]) >= 1

    def test_guarda_que_candidates(self):
        """Análisis de candidatos para
        'guarda que tengo clase'."""
        a = analyze("guarda que tengo clase")
        assert a["intent"] == MEMORY_CREATE
        assert a["candidates"][0][0] == \
            MEMORY_CREATE

    def test_algo_candidates_empty(self):
        """AMBIGUOUS_INPUT sin candidatos."""
        a = analyze("algo")
        assert a["intent"] == AMBIGUOUS_INPUT
        assert len(a["candidates"]) == 0


# ==========================================
# 10. CONFIDENCE DISTRIBUTION
# ==========================================


class TestConfidenceDistribution:

    def test_all_safe_above_090(self):
        phrases = [
            "hola", "buenas", "buenos dias",
            "buenas tardes", "buenas noches",
            "gracias", "muchas gracias",
            "2+2", "3*4+1", "(10-2)/4",
            "10 / 2", "100 - 25", "2.5 * 4",
            "salir", "exit", "quit",
        ]

        for phrase in phrases:

            r = il.classify(phrase)

            assert r.confidence >= 0.90, (
                f"Safe intent confidence < 0.90: "
                f"'{phrase}' → {r.intent} "
                f"conf={r.confidence}"
            )

    def test_free_talk_below_050(self):
        phrases = [
            "cuéntame un chiste gracioso",
            "qué opinas de la ia",
            "explícame cómo funciona internet",
            "cuéntame algo interesante",
            "necesito ayuda con python",
        ]

        for phrase in phrases:

            r = il.classify(phrase)

            if r.intent == FREE_TALK:

                assert r.confidence < 0.50, (
                    f"FREE_TALK confidence too "
                    f"high: '{phrase}' "
                    f"conf={r.confidence}"
                )

    def test_decia_self_above_090(self):
        phrases = [
            "quien eres", "que eres",
            "como te llamas", "cual es tu nombre",
        ]

        for phrase in phrases:

            r = il.classify(phrase)

            assert r.confidence >= 0.90, (
                f"DECIA_SELF confidence < 0.90: "
                f"'{phrase}' conf={r.confidence}"
            )


# ==========================================
# 11. ENTITY EXTRACTION STRESS
# ==========================================


class TestEntityExtractionStress:

    def test_user_name_variants(self):
        cases = [
            ("mi nombre es Pedro", "Pedro"),
            ("me llamo Maria", "Maria"),
            ("yo me llamo Carlos", "Carlos"),
            ("ese es mi nombre Ana", "Ana"),
            ("el mio es Luis", "Luis"),
        ]

        for phrase, expected in cases:

            a = analyze(phrase)

            assert a["intent"] == USER_NAME_SET
            assert a["entities"]["user_name"] == \
                expected

    def test_preferred_name_variants(self):
        cases = [
            ("llamame Creador", "Creador"),
            ("puedes llamarme Jefe", "Jefe"),
            (
                "quiero que me llames Amigo",
                "Amigo",
            ),
            ("desde ahora llamame Boss", "Boss"),
        ]

        for phrase, expected in cases:

            a = analyze(phrase)

            assert a["intent"] == \
                PREFERRED_NAME_SET
            assert a["entities"][
                "preferred_name"
            ] == expected

    def test_memory_content_variants(self):
        cases = [
            (
                "guarda que tengo clase",
                "tengo clase",
            ),
            (
                "recuerda que voy al gym",
                "voy al gym",
            ),
            (
                "anota que es lunes",
                "es lunes",
            ),
        ]

        for phrase, expected in cases:

            a = analyze(phrase)

            assert a["intent"] == MEMORY_CREATE
            assert a["entities"]["memory"] == \
                expected

    def test_math_entity_variants(self):
        """PASS (FIXED 2B.1): '2.5 * 4' preserva
        el punto decimal en entity math.
        Antes se normalizaba a '25 * 4'."""
        cases = [
            ("2+2", "2+2"),
            ("3*4+1", "3*4+1"),
            ("(10-2)/4", "(10-2)/4"),
            ("10 / 2", "10 / 2"),
            ("100 - 25", "100 - 25"),
            ("2.5 * 4", "2.5 * 4"),
        ]

        for phrase, expected_math in cases:

            a = analyze(phrase)

            assert a["intent"] == CALCULATE
            assert "math" in a["entities"]
            assert a["entities"]["math"] == \
                expected_math

    def test_no_entities_in_read_intents(self):
        read = [
            "hola",
            "gracias",
            "salir",
            "quien eres",
            "quien te creo",
        ]

        for phrase in read:

            a = analyze(phrase)

            assert a["entities"] == {}, (
                f"Unexpected entities in "
                f"'{phrase}': {a['entities']}"
            )


# ==========================================
# 12. WHISPER EDGE CASES
# ==========================================


class TestWhisperEdgeCases:

    def test_kien_quien_difference(self):
        """FINDING: La normalización NO maneja
        errores ortográficos ('k' por 'qu').
        'kien' ≠ 'quien'."""
        a_kien = analyze("kien eres")
        a_quien = analyze("quien eres")

        assert a_kien["intent"] != \
            a_quien["intent"] or \
            a_kien["confidence"] < \
            a_quien["confidence"]

    def test_ke_que_difference(self):
        """FINDING: 'ke' ≠ 'que'."""
        a_ke = analyze("ke significa deca")
        a_que = analyze("que significa deca")

        assert a_ke["confidence"] <= \
            a_que["confidence"]

    def test_grasias_gracias_difference(self):
        """FINDING: 'grasias' ≠ 'gracias'."""
        a_bad = analyze("grasias")
        a_good = analyze("gracias")

        assert a_bad["confidence"] <= \
            a_good["confidence"]

    def test_buenas_dias_with_tilde(self):
        """PASS: Con tilde funciona igual."""
        a_tilde = analyze("buenos días")
        a_no_tilde = analyze("buenos dias")

        assert a_tilde["intent"] == \
            a_no_tilde["intent"]
        assert a_tilde["confidence"] == \
            a_no_tilde["confidence"]

    def test_llamame_sin_acento(self):
        """PASS: 'llamame' funciona sin tilde."""
        a = analyze("llamame creador")
        assert a["intent"] == PREFERRED_NAME_SET
        assert "preferred_name" in a["entities"]

    def test_mixed_whisper_good_and_bad(self):
        """FINDING: 'kien eres' → AMBIGUOUS.
        'quien eres' → DECIA_SELF.
        La calidad de Whisper impacta
        directamente la clasificación."""
        a = analyze("kien eres")
        assert a["intent"] in (
            AMBIGUOUS_INPUT, DECIA_SELF,
        )


# ==========================================
# 13. CONVERSATIONAL STRESS
# ==========================================


class TestConversationalStress:

    def test_multi_intent_phrase(self):
        """FINDING: 'oye decia guardame que
        tengo clase'. 'guarda que' activa
        MEMORY_CREATE. 'decia' se ignora."""
        a = analyze(
            "oye decia guardame que tengo clase"
        )
        assert a["intent"] in (
            MEMORY_CREATE, FREE_TALK,
        )

    def test_very_long_message(self):
        """PASS: Mensaje largo sin patrón
        determinista → FREE_TALK."""
        msg = (
            "hoy me desperté a las seis de la "
            "mañana y desayuné cereal con leche "
            "y después salí a caminar al parque "
            "cerca de mi casa"
        )
        a = analyze(msg)
        assert a["intent"] == FREE_TALK

    def test_repeated_words(self):
        """PASS (FIXED 2B.1): 'hola hola hola' →
        'hola' con word_boundary matchea.
        GREETING con conf >= 0.90."""
        a = analyze("hola hola hola")
        assert a["intent"] == GREETING
        assert a["confidence"] >= 0.90

    def test_only_punctuation(self):
        """PASS: '???' → AMBIGUOUS_INPUT."""
        a = analyze("???")
        assert a["intent"] == AMBIGUOUS_INPUT

    def test_emojis_only(self):
        """PASS: '😊' → AMBIGUOUS o FREE_TALK."""
        a = analyze("😊")
        assert a["intent"] in (
            AMBIGUOUS_INPUT, FREE_TALK,
        )

    def test_numbers_and_text_mixed(self):
        """PASS: 'tengo 3 gatos' no activa
        CALCULATE (contiene texto)."""
        a = analyze("tengo 3 gatos")
        assert a["intent"] != CALCULATE

    def test_just_numbers(self):
        """PASS: '12345' → CALCULATE."""
        a = analyze("12345")
        assert a["intent"] == CALCULATE

    def test_negative_numbers(self):
        """PASS: '-5+3' → CALCULATE."""
        a = analyze("-5+3")
        assert a["intent"] == CALCULATE
        assert "math" in a["entities"]

    def test_power_operator(self):
        """FINDING: '**' no está en la regex
        de CALCULATE. '2**10' podría no matchear.
        Pero regex incluye asterisco que matchea
        cada asterisco."""
        a = analyze("2**10")
        assert a["intent"] in (
            CALCULATE, FREE_TALK,
        )


# ==========================================
# 14. INTENT COVERAGE STRESS
# ==========================================


class TestIntentCoverageStress:

    def test_all_16_intents_reachable(self):
        """Verificar que los 16 intents
        siguen siendo alcanzables."""
        test_phrases = {
            GREETING: "hola",
            THANKS: "gracias",
            DECIA_SELF: "quien eres",
            DECIA_CREATOR: "quien te creo",
            USER_NAME_ASK: "quien soy",
            USER_NAME_SET: "mi nombre es Pedro",
            PREFERRED_NAME_ASK:
                "como quieres llamarme",
            PREFERRED_NAME_SET: "llamame Creador",
            CALCULATE: "2+2",
            MEMORY_CREATE:
                "guarda que tengo clase",
            MEMORY_SEARCH: "que recuerdas",
            ARCHIVE_DIRECT:
                "que significa DECA",
            ARCHIVE_SEARCH: "historia de DECA",
            EXIT: "salir",
            AMBIGUOUS_INPUT: "algo",
            FREE_TALK: "cuéntame un chiste",
        }

        for intent, phrase in test_phrases.items():

            r = il.classify(phrase)
            assert r.intent == intent, (
                f"Intent {intent} not reached "
                f"with '{phrase}': got {r.intent}"
            )

    def test_sixteen_intents_total(self):

        all_intents = set()

        phrases = [
            "hola", "gracias", "quien eres",
            "quien te creo", "quien soy",
            "mi nombre es Pedro",
            "como quieres llamarme",
            "llamame Creador", "2+2",
            "guarda que tengo clase",
            "que recuerdas",
            "que significa DECA",
            "historia de DECA", "salir",
            "algo", "cuéntame un chiste",
        ]

        for phrase in phrases:

            r = il.classify(phrase)
            all_intents.add(r.intent)

        assert len(all_intents) == 16
