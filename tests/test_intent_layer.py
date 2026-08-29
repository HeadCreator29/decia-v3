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
    MEMORY_CREATE,
    MEMORY_SEARCH,
    ARCHIVE_DIRECT,
    ARCHIVE_SEARCH,
    EXIT,
    AMBIGUOUS_INPUT,
    FREE_TALK,
    CONFIDENCE_SEGURO,
    CONFIDENCE_PROBABLE,
    CONFIDENCE_AMBIGUO,
)


il = IntentLayer()


# ==========================================
# GREETING
# ==========================================


def test_greeting_hola():

    r = il.classify("hola")
    assert r.intent == GREETING
    assert r.confidence >= CONFIDENCE_SEGURO


def test_greeting_buenas():

    r = il.classify("buenas")
    assert r.intent == GREETING
    assert r.confidence >= CONFIDENCE_SEGURO


def test_greeting_buenos_dias():

    r = il.classify("buenos dias")
    assert r.intent == GREETING
    assert r.confidence >= CONFIDENCE_SEGURO


def test_greeting_buenas_tardes():

    r = il.classify("buenas tardes")
    assert r.intent == GREETING
    assert r.confidence >= CONFIDENCE_SEGURO


def test_greeting_buenas_noches():

    r = il.classify("buenas noches")
    assert r.intent == GREETING
    assert r.confidence >= CONFIDENCE_SEGURO


def test_greeting_with_question():

    r = il.classify("hola?")
    assert r.intent == GREETING


def test_greeting_with_punctuation():

    r = il.classify("¡Hola!")
    assert r.intent == GREETING


# ==========================================
# THANKS
# ==========================================


def test_thanks_gracias():

    r = il.classify("gracias")
    assert r.intent == THANKS
    assert r.confidence >= CONFIDENCE_SEGURO


def test_thanks_muchas_gracias():

    r = il.classify("muchas gracias")
    assert r.intent == THANKS
    assert r.confidence >= CONFIDENCE_SEGURO


# ==========================================
# DECIA_SELF
# ==========================================


def test_decia_self_quien_eres():

    r = il.classify("quién eres")
    assert r.intent == DECIA_SELF
    assert r.confidence >= CONFIDENCE_SEGURO


def test_decia_self_que_eres():

    r = il.classify("qué eres")
    assert r.intent == DECIA_SELF
    assert r.confidence >= CONFIDENCE_SEGURO


def test_decia_self_como_te_llamas():

    r = il.classify("cómo te llamas")
    assert r.intent == DECIA_SELF
    assert r.confidence >= CONFIDENCE_SEGURO


def test_decia_self_cual_es_tu_nombre():

    r = il.classify("cuál es tu nombre")
    assert r.intent == DECIA_SELF
    assert r.confidence >= CONFIDENCE_SEGURO


# ==========================================
# DECIA_CREATOR
# ==========================================


def test_decia_creator_quien_te_creo():

    r = il.classify("quién te creó")
    assert r.intent == DECIA_CREATOR
    assert r.confidence >= CONFIDENCE_SEGURO


def test_decia_creator_quien_es_tu_creador():

    r = il.classify("quién es tu creador")
    assert r.intent == DECIA_CREATOR
    assert r.confidence >= CONFIDENCE_SEGURO


def test_decia_creator_como_naciste():

    r = il.classify("cómo naciste")
    assert r.intent == DECIA_CREATOR
    assert r.confidence >= CONFIDENCE_SEGURO


def test_decia_creator_quien_hizo():

    r = il.classify("quién hizo")
    assert r.intent == DECIA_CREATOR
    assert r.confidence >= CONFIDENCE_SEGURO


def test_decia_creator_quien_te_hizo():

    r = il.classify("quién te hizo")
    assert r.intent == DECIA_CREATOR
    assert r.confidence >= CONFIDENCE_SEGURO


# ==========================================
# USER_NAME_ASK
# ==========================================


def test_user_name_ask_como_me_llamo():

    r = il.classify("cómo me llamo")
    assert r.intent == USER_NAME_ASK
    assert r.confidence >= CONFIDENCE_SEGURO


def test_user_name_ask_cual_es_mi_nombre():

    r = il.classify("cuál es mi nombre")
    assert r.intent == USER_NAME_ASK
    assert r.confidence >= CONFIDENCE_SEGURO


def test_user_name_ask_quien_soy():

    r = il.classify("quién soy")
    assert r.intent == USER_NAME_ASK
    assert r.confidence >= CONFIDENCE_PROBABLE


def test_user_name_ask_como_me_tienes():

    r = il.classify("cómo me tienes guardado")
    assert r.intent == USER_NAME_ASK
    assert r.confidence >= CONFIDENCE_SEGURO


# ==========================================
# PREFERRED_NAME_ASK
# ==========================================


def test_preferred_name_ask_como_quieres():

    r = il.classify("cómo quieres llamarme")
    assert r.intent == PREFERRED_NAME_ASK
    assert r.confidence >= CONFIDENCE_SEGURO


def test_preferred_name_ask_como_me_llama():

    r = il.classify("cómo me llama")
    assert r.intent == PREFERRED_NAME_ASK
    assert r.confidence >= CONFIDENCE_SEGURO


# ==========================================
# USER_NAME_SET
# ==========================================


def test_user_name_set_mi_nombre_es():

    r = il.classify("mi nombre es Carlos")
    assert r.intent == USER_NAME_SET
    assert r.confidence >= CONFIDENCE_SEGURO
    assert "user_name" in r.entities
    assert r.entities["user_name"] == "Carlos"


def test_user_name_set_me_llamo():

    r = il.classify("me llamo María")
    assert r.intent == USER_NAME_SET
    assert r.confidence >= CONFIDENCE_PROBABLE
    assert r.entities["user_name"] == "Maria"


def test_user_name_set_yo_me_llamo():

    r = il.classify("yo me llamo Pedro")
    assert r.intent == USER_NAME_SET
    assert r.entities["user_name"] == "Pedro"


def test_user_name_set_ese_es_mi_nombre():

    r = il.classify("ese es mi nombre Ana")
    assert r.intent == USER_NAME_SET
    assert r.entities["user_name"] == "Ana"


def test_user_name_set_el_mio_es():

    r = il.classify("el mío es Luis")
    assert r.intent == USER_NAME_SET
    assert r.entities["user_name"] == "Luis"


# ==========================================
# PREFERRED_NAME_SET
# ==========================================


def test_preferred_name_set_llamame():

    r = il.classify("llámame Creador")
    assert r.intent == PREFERRED_NAME_SET
    assert r.confidence >= CONFIDENCE_PROBABLE
    assert "preferred_name" in r.entities
    assert r.entities["preferred_name"] == \
        "Creador"


def test_preferred_name_set_puedes_llamarme():

    r = il.classify("puedes llamarme Boss")
    assert r.intent == PREFERRED_NAME_SET
    assert r.entities["preferred_name"] == "Boss"


def test_preferred_name_set_quiero_que_me_llames():

    r = il.classify(
        "quiero que me llames Amigo"
    )
    assert r.intent == PREFERRED_NAME_SET
    assert r.entities["preferred_name"] == \
        "Amigo"


def test_preferred_name_set_desde_ahora():

    r = il.classify(
        "desde ahora llámame Jefe"
    )
    assert r.intent == PREFERRED_NAME_SET
    assert r.entities["preferred_name"] == "Jefe"


def test_preferred_name_set_de_ahora_en_adelante():

    r = il.classify(
        "de ahora en adelante llámame Maestro"
    )
    assert r.intent == PREFERRED_NAME_SET
    assert r.entities["preferred_name"] == \
        "Maestro"


# ==========================================
# CALCULATE
# ==========================================


def test_calculate_simple():

    r = il.classify("2+2")
    assert r.intent == CALCULATE
    assert r.confidence >= CONFIDENCE_SEGURO
    assert "math" in r.entities
    assert r.entities["math"] == "2+2"


def test_calculate_complex():

    r = il.classify("(10-2)*4")
    assert r.intent == CALCULATE
    assert r.entities["math"] == "(10-2)*4"


def test_calculate_division():

    r = il.classify("10/2")
    assert r.intent == CALCULATE


def test_calculate_decimal():

    r = il.classify("3.14*2")
    assert r.intent == CALCULATE


def test_calculate_negative():

    r = il.classify("-5+3")
    assert r.intent == CALCULATE


# ==========================================
# MEMORY_CREATE
# ==========================================


def test_memory_create_guarda_que():

    r = il.classify("guarda que tengo clase")
    assert r.intent == MEMORY_CREATE
    assert r.confidence >= CONFIDENCE_SEGURO
    assert "memory" in r.entities
    assert r.entities["memory"] == "tengo clase"


def test_memory_create_recuerda_que():

    r = il.classify(
        "recuerda que voy al gym"
    )
    assert r.intent == MEMORY_CREATE
    assert r.entities["memory"] == "voy al gym"


def test_memory_create_anota_que():

    r = il.classify("anota que es lunes")
    assert r.intent == MEMORY_CREATE
    assert r.entities["memory"] == "es lunes"


def test_memory_create_memoriza_que():

    r = il.classify(
        "memoriza que la clave es 1234"
    )
    assert r.intent == MEMORY_CREATE
    assert r.entities["memory"] == "la clave es 1234"


def test_memory_create_quiero_que_recuerdes():

    r = il.classify(
        "quiero que recuerdes mi cumpleaños"
    )
    assert r.intent == MEMORY_CREATE
    assert r.entities["memory"] == "mi cumpleaños"


def test_memory_create_quiero_que_guardes():

    r = il.classify(
        "quiero que guardes esta info"
    )
    assert r.intent == MEMORY_CREATE
    assert r.entities["memory"] == "esta info"


def test_memory_create_guarda_esto():
    """'guarda esto' no extrae entidad.
    Sin entidad → score = 0 → AMBIGUOUS_INPUT."""

    r = il.classify("guarda esto")
    assert r.intent == AMBIGUOUS_INPUT


def test_memory_create_recuerda_esto():
    """'recuerda esto' no extrae entidad.
    Sin entidad → score = 0 → AMBIGUOUS_INPUT."""

    r = il.classify("recuerda esto")
    assert r.intent == AMBIGUOUS_INPUT


# ==========================================
# MEMORY_SEARCH
# ==========================================


def test_memory_search_que_recuerdas():

    r = il.classify("qué recuerdas")
    assert r.intent == MEMORY_SEARCH
    assert r.confidence >= CONFIDENCE_AMBIGUO


def test_memory_search_que_hicimos():

    r = il.classify("qué hicimos hoy")
    assert r.intent == MEMORY_SEARCH


def test_memory_search_alguna_memoria():

    r = il.classify(
        "tienes alguna memoria"
    )
    assert r.intent == MEMORY_SEARCH


# ==========================================
# ARCHIVE_DIRECT
# ==========================================


def test_archive_direct_cuando_comenzo():

    r = il.classify(
        "cuándo comenzó DECA"
    )
    assert r.intent == ARCHIVE_DIRECT
    assert r.confidence >= CONFIDENCE_PROBABLE


def test_archive_direct_que_significa():

    r = il.classify(
        "qué significa DECA"
    )
    assert r.intent == ARCHIVE_DIRECT
    assert r.confidence >= CONFIDENCE_PROBABLE


def test_archive_direct_valores():

    r = il.classify(
        "cuáles son los valores de DECA"
    )
    assert r.intent == ARCHIVE_DIRECT


def test_archive_direct_vision():

    r = il.classify(
        "visión de DECA"
    )
    assert r.intent == ARCHIVE_DIRECT


def test_archive_direct_quien_creo():

    r = il.classify(
        "quién creó DECA"
    )
    assert r.intent == ARCHIVE_DIRECT


def test_archive_direct_quien_es_el_creador():

    r = il.classify(
        "quién es el creador de DECA"
    )
    assert r.intent == ARCHIVE_DIRECT


# ==========================================
# ARCHIVE_SEARCH
# ==========================================


def test_archive_search_significado():
    """'significado' sola, base 35,1 palabra
    → AMBIGUOUS_INPUT."""

    r = il.classify("significado")
    assert r.intent in (
        ARCHIVE_SEARCH, AMBIGUOUS_INPUT,
    )


def test_archive_search_historia():
    """Phase 6.6: ancla genérica
    'cuentame/dime/hablame + la historia' retirada.
    Sin 'deca', 'cuéntame la historia' → FREE_TALK
    (auditoría de límites: SOBREAMPLIA corregida)."""

    r = il.classify("cuéntame la historia")
    assert r.intent == FREE_TALK


def test_archive_search_eventos():
    """Phase 2C: 'deca' boost reduced, confidence
    is now PROBABLE-range but intent still matches."""

    r = il.classify("eventos de DECA")
    assert r.intent == ARCHIVE_SEARCH
    assert r.confidence >= CONFIDENCE_AMBIGUO


def test_archive_search_valores_solo():

    r = il.classify("cuáles son los valores")
    assert r.intent == ARCHIVE_SEARCH


def test_archive_search_origen():
    """Phase 2C: 'origen de deca' matches
    ARCHIVE_DIRECT (exact phrase pattern)."""

    r = il.classify("el origen de DECA")
    assert r.intent == ARCHIVE_DIRECT
    assert r.confidence >= CONFIDENCE_SEGURO


# ==========================================
# EXIT
# ==========================================


def test_exit_salir():

    r = il.classify("salir")
    assert r.intent == EXIT
    assert r.confidence >= CONFIDENCE_SEGURO


def test_exit_quit():

    r = il.classify("quit")
    assert r.intent == EXIT


def test_exit_exit():

    r = il.classify("exit")
    assert r.intent == EXIT


# ==========================================
# AMBIGUOUS_INPUT
# ==========================================


def test_ambiguous_algo():

    r = il.classify("algo")
    assert r.intent == AMBIGUOUS_INPUT
    assert r.confidence >= CONFIDENCE_PROBABLE


def test_ambiguous_hmm():

    r = il.classify("hmm")
    assert r.intent == AMBIGUOUS_INPUT
    assert r.confidence >= CONFIDENCE_PROBABLE


def test_ambiguous_cosas():

    r = il.classify("cosas")
    assert r.intent == AMBIGUOUS_INPUT


def test_ambiguous_mira():

    r = il.classify("mira")
    assert r.intent == AMBIGUOUS_INPUT


def test_ambiguous_empty():

    r = il.classify("")
    assert r.intent == AMBIGUOUS_INPUT
    assert r.confidence == 1.0


def test_ambiguous_short_no_keyword():

    r = il.classify("pues")
    assert r.intent == AMBIGUOUS_INPUT


# ==========================================
# FREE_TALK
# ==========================================


def test_free_talk_chiste():

    r = il.classify(
        "cuéntame un chiste gracioso"
    )
    assert r.intent == FREE_TALK
    assert r.confidence < 0.50


def test_free_talk_opinion():

    r = il.classify(
        "qué opinas de la inteligencia artificial"
    )
    assert r.intent == FREE_TALK


def test_free_talk_explica():

    r = il.classify(
        "explícame cómo funciona internet"
    )
    assert r.intent == FREE_TALK


def test_free_talk_long_message():
    """'hoy' solo ya no activa MEMORY_SEARCH.
    Sin contexto de memoria → FREE_TALK."""

    r = il.classify(
        "hoy me siento un poco cansado pero "
        "quiero aprender algo nuevo"
    )
    assert r.intent == FREE_TALK


# ==========================================
# CONFLICTOS
# ==========================================


def test_conflict_decia_self_vs_user_name():

    r = il.classify("quién soy")
    assert r.intent == USER_NAME_ASK
    assert r.confidence >= CONFIDENCE_PROBABLE


def test_conflict_decia_creator_vs_archive():

    r = il.classify("quién creó DECA")
    assert r.intent == ARCHIVE_DIRECT
    assert r.confidence >= CONFIDENCE_PROBABLE


def test_conflict_archive_direct_vs_search():

    r = il.classify("qué significa DECA")
    assert r.intent == ARCHIVE_DIRECT
    assert r.confidence >= CONFIDENCE_PROBABLE


def test_conflict_memory_create_vs_search():

    r = il.classify(
        "recuerda que tengo reunión"
    )
    assert r.intent == MEMORY_CREATE
    assert r.confidence >= CONFIDENCE_SEGURO


def test_conflict_memory_search_vs_create():

    r = il.classify("qué recuerdas de ayer")
    assert r.intent == MEMORY_SEARCH
    assert r.confidence >= CONFIDENCE_AMBIGUO


def test_conflict_ambiguous_vs_greeting():

    r = il.classify("hola")
    assert r.intent == GREETING
    assert r.confidence >= CONFIDENCE_SEGURO


def test_conflict_ambiguous_vs_thanks():

    r = il.classify("gracias")
    assert r.intent == THANKS
    assert r.confidence >= CONFIDENCE_SEGURO


def test_conflict_name_set_vs_preferred():

    r = il.classify("mi nombre es Pedro")
    assert r.intent == USER_NAME_SET
    assert r.confidence >= CONFIDENCE_SEGURO


def test_conflict_preferred_vs_name_set():

    r = il.classify("llámame Creador")
    assert r.intent == PREFERRED_NAME_SET
    assert r.confidence >= CONFIDENCE_PROBABLE


def test_conflict_calc_vs_text():

    r = il.classify("2+2")
    assert r.intent == CALCULATE
    assert r.confidence >= CONFIDENCE_SEGURO


def test_conflict_hola_vs_ambiguous():

    r = il.classify("hola")
    assert r.intent == GREETING
    assert r.confidence >= CONFIDENCE_SEGURO


def test_conflict_decia_self_vs_creator():

    r = il.classify("quién eres")
    assert r.intent == DECIA_SELF

    r2 = il.classify("quién te creó")
    assert r2.intent == DECIA_CREATOR


# ==========================================
# ENTIDADES
# ==========================================


def test_entity_user_name():

    r = il.classify("mi nombre es Idelvi")
    assert r.entities["user_name"] == "Idelvi"


def test_entity_user_name_capitalized():

    r = il.classify("me llamo maría")
    assert r.entities["user_name"] == "Maria"


def test_entity_preferred_name():

    r = il.classify(
        "puedes llamarme Creador"
    )
    assert r.entities["preferred_name"] == \
        "Creador"


def test_entity_math_expression():

    r = il.classify("(3+5)*2")
    assert r.entities["math"] == "(3+5)*2"


def test_entity_memory_content():

    r = il.classify(
        "guarda que tengo clase a las 3"
    )
    assert r.entities["memory"] == \
        "tengo clase a las 3"


def test_entity_no_extraction_greeting():

    r = il.classify("hola")
    assert r.entities == {}


def test_entity_no_extraction_thanks():

    r = il.classify("gracias")
    assert r.entities == {}


def test_entity_no_extraction_exit():

    r = il.classify("salir")
    assert r.entities == {}


def test_entity_no_extraction_decia_self():

    r = il.classify("quién eres")
    assert r.entities == {}


# ==========================================
# CONFIDENCE
# ==========================================


def test_confidence_seguro():

    r = il.classify("hola")
    assert r.confidence >= CONFIDENCE_SEGURO


def test_confidence_probable():
    """Phase 2C: 'deca' boost reduced, confidence
    is now AMBIGUO-range for keyword-only match."""

    r = il.classify("historia de deca")
    assert r.intent == ARCHIVE_SEARCH
    assert r.confidence >= CONFIDENCE_AMBIGUO


def test_confidence_ambiguous():

    r = il.classify("algo")
    assert r.confidence >= CONFIDENCE_AMBIGUO


def test_confidence_unknown():

    r = il.classify("xyzabc123")
    assert r.intent == AMBIGUOUS_INPUT
    assert r.confidence == 1.0


# ==========================================
# CANDIDATES
# ==========================================


def test_candidates_not_empty():

    r = il.classify("hola")
    assert len(r.candidates) > 0


def test_candidates_sorted():

    r = il.classify("quién creó DECA")
    scores = [c.score for c in r.candidates]
    assert scores == sorted(scores, reverse=True)


def test_candidates_best_is_first():

    r = il.classify("hola")
    assert r.candidates[0].intent == GREETING


def test_candidates_have_matched_pattern():

    r = il.classify("hola")
    assert r.candidates[0].matched_pattern \
        != ""


# ==========================================
# MATCHED PATTERN
# ==========================================


def test_matched_pattern_exact():

    r = il.classify("hola")
    assert r.matched_pattern == "hola"


def test_matched_pattern_phrase():

    r = il.classify("buenos días")
    assert r.matched_pattern == "buenos dias"


def test_matched_pattern_regex():

    r = il.classify("mi nombre es Pedro")
    assert "nombre es" in r.matched_pattern


# ==========================================
# NORMALIZACIÓN
# ==========================================


def test_normalization_accents():

    r = il.classify("hola")
    assert r.intent == GREETING

    r2 = il.classify("HOLA")
    assert r2.intent == GREETING


def test_normalization_punctuation():

    r = il.classify("¿quién eres?")
    assert r.intent == DECIA_SELF


def test_normalization_mixed_case():

    r = il.classify("Gracias")
    assert r.intent == THANKS


def test_normalization_extra_spaces():

    r = il.classify("  hola  ")
    assert r.intent == GREETING


# ==========================================
# EDGE CASES
# ==========================================


def test_single_number():

    r = il.classify("5")
    assert r.intent == CALCULATE


def test_single_word_known():

    r = il.classify("hola")
    assert r.intent == GREETING


def test_single_word_unknown():

    r = il.classify("xyz")
    assert r.intent == AMBIGUOUS_INPUT


def test_only_punctuation():

    r = il.classify("???")
    assert r.intent == AMBIGUOUS_INPUT


def test_long_message_no_match():
    """'hoy' solo ya no activa MEMORY_SEARCH.
    Sin contexto de memoria → FREE_TALK."""

    r = il.classify(
        "hoy me desperté temprano y salí a "
        "correr por el parque cerca de mi casa"
    )
    assert r.intent == FREE_TALK


def test_memory_create_with_decia_prefix():

    r = il.classify(
        "decia guarda que tengo clase"
    )
    assert r.intent == MEMORY_CREATE
    assert r.entities["memory"] == \
        "tengo clase"


def test_archive_search_hoy():

    r = il.classify("qué hicimos hoy")
    assert r.intent == MEMORY_SEARCH


def test_decia_creator_keyword_match():

    r = il.classify(
        "quién es el creador"
    )
    assert r.intent == DECIA_CREATOR


def test_archive_search_keyword_with_deca():

    r = il.classify(
        "cuál es la visión de DECA"
    )
    assert r.intent == ARCHIVE_DIRECT


# ==========================================
# SCORING
# ==========================================


def test_scoring_exact_beats_phrase():

    r = il.classify("hola")
    best = r.candidates[0]
    assert best.matched_type == "exact"


def test_scoring_phrase_beats_keyword():

    r = il.classify("quién te creó")
    best = r.candidates[0]
    assert best.intent == DECIA_CREATOR
    assert best.matched_type == "phrase"


def test_scoring_context_boost():

    r = il.classify(
        "cuándo comenzó DECA"
    )
    scores = {
        c.intent: c.score for c in r.candidates
    }
    assert scores[ARCHIVE_DIRECT] > \
        scores.get(ARCHIVE_SEARCH, 0)


def test_scoring_free_talk_never_high():

    r = il.classify(
        "cuéntame algo interesante"
    )
    assert r.intent == FREE_TALK
    assert r.confidence < 0.50
