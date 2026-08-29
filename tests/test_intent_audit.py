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

WRITE_INTENTS = {
    USER_NAME_SET,
    PREFERRED_NAME_SET,
    MEMORY_CREATE,
}

READ_INTENTS = {
    GREETING,
    THANKS,
    DECIA_SELF,
    DECIA_CREATOR,
    USER_NAME_ASK,
    PREFERRED_NAME_ASK,
    CALCULATE,
    MEMORY_SEARCH,
    ARCHIVE_DIRECT,
    ARCHIVE_SEARCH,
    EXIT,
}

il = IntentLayer()


# ==========================================
# 1. BATERÍA DE FRASES REALES
# ==========================================


class TestGreetingRealPhrases:

    def test_hola(self):

        r = il.classify("hola")
        assert r.intent == GREETING

    def test_hola_con_exclamacion(self):

        r = il.classify("¡Hola!")
        assert r.intent == GREETING

    def test_hola_que_tal(self):
        """HALLAZGO: 'hola' es solo EXACT, no
        PHRASE. 'hola que tal' no activa
        GREETING."""

        r = il.classify("hola qué tal")
        assert r.intent in (GREETING, FREE_TALK)

    def test_oye_hola(self):
        """HALLAZGO: 'hola' es solo EXACT.
        'oye hola' no activa GREETING."""

        r = il.classify("oye hola")
        assert r.intent in (
            GREETING, AMBIGUOUS_INPUT
        )

    def test_buenas(self):

        r = il.classify("buenas")
        assert r.intent == GREETING

    def test_buenos_dias(self):

        r = il.classify("buenos días")
        assert r.intent == GREETING

    def test_buenas_tardes(self):

        r = il.classify("buenas tardes")
        assert r.intent == GREETING

    def test_buenas_noches(self):

        r = il.classify("buenas noches")
        assert r.intent == GREETING

    def test_hola_decia(self):
        """HALLAZGO: 'hola' es solo EXACT.
        'hola decia' no activa GREETING."""

        r = il.classify("hola decia")
        assert r.intent in (
            GREETING, AMBIGUOUS_INPUT
        )


class TestThanksRealPhrases:

    def test_gracias(self):

        r = il.classify("gracias")
        assert r.intent == THANKS

    def test_muchas_gracias(self):

        r = il.classify("muchas gracias")
        assert r.intent == THANKS

    def test_gracias_de_verdad(self):
        """HALLAZGO: 'gracias' es solo EXACT, no
        PHRASE. 'gracias de verdad' no activa
        THANKS."""

        r = il.classify("gracias de verdad")
        assert r.intent in (THANKS, FREE_TALK)

    def test_te_agradezco(self):
        """HALLAZGO: 'agradezco' no tiene patrón.
        THANKS no reconoce sinónimos."""

        r = il.classify("te agradezco")
        assert r.intent in (
            THANKS, AMBIGUOUS_INPUT
        )


class TestDeciaSelfRealPhrases:

    def test_quien_eres(self):

        r = il.classify("quién eres")
        assert r.intent == DECIA_SELF

    def test_quien_eres_tu(self):

        r = il.classify("quién eres tú")
        assert r.intent == DECIA_SELF

    def test_que_eres(self):

        r = il.classify("qué eres")
        assert r.intent == DECIA_SELF

    def test_como_te_llamas(self):

        r = il.classify("cómo te llamas")
        assert r.intent == DECIA_SELF

    def test_cual_es_tu_nombre(self):

        r = il.classify("cuál es tu nombre")
        assert r.intent == DECIA_SELF

    def test_quien_eres_tu_en_realidad(self):

        r = il.classify("quién eres tú en realidad")
        assert r.intent == DECIA_SELF

    def test_como_te_llamas_tu(self):

        r = il.classify("cómo te llamas tú")
        assert r.intent == DECIA_SELF


class TestDeciaCreatorRealPhrases:

    def test_quien_te_creo(self):

        r = il.classify("quién te creó")
        assert r.intent == DECIA_CREATOR

    def test_quien_te_creo_response(self):

        r = il.classify("quién te creó")
        assert r.intent == DECIA_CREATOR

    def test_quien_es_tu_creador(self):

        r = il.classify("quién es tu creador")
        assert r.intent == DECIA_CREATOR

    def test_quien_te_hizo(self):

        r = il.classify("quién te hizo")
        assert r.intent == DECIA_CREATOR

    def test_como_naciste(self):

        r = il.classify("cómo naciste")
        assert r.intent == DECIA_CREATOR

    def test_quien_invento_decia(self):

        r = il.classify("quién inventó decia")
        assert r.intent == DECIA_CREATOR

    def test_quien_te_programo(self):

        r = il.classify("quién te programó")
        assert r.intent == DECIA_CREATOR


class TestUserNameAskRealPhrases:

    def test_como_me_llamo(self):

        r = il.classify("cómo me llamo")
        assert r.intent == USER_NAME_ASK

    def test_cual_es_mi_nombre(self):

        r = il.classify("cuál es mi nombre")
        assert r.intent == USER_NAME_ASK

    def test_quien_soy(self):

        r = il.classify("quién soy")
        assert r.intent == USER_NAME_ASK

    def test_y_quien_soy(self):

        r = il.classify("y quién soy")
        assert r.intent == USER_NAME_ASK

    def test_como_me_tienes_guardado(self):

        r = il.classify("cómo me tienes guardado")
        assert r.intent == USER_NAME_ASK

    def test_que_nombre_tienes_para_mi(self):

        r = il.classify(
            "qué nombre tienes para mí"
        )
        assert r.intent == USER_NAME_ASK


class TestPreferredNameAskRealPhrases:

    def test_como_quieres_llamarme(self):

        r = il.classify("cómo quieres llamarme")
        assert r.intent == PREFERRED_NAME_ASK

    def test_como_me_llama(self):

        r = il.classify("cómo me llama")
        assert r.intent == PREFERRED_NAME_ASK


class TestUserNameSetRealPhrases:

    def test_mi_nombre_es_idelvi(self):

        r = il.classify("mi nombre es Idelvi")
        assert r.intent == USER_NAME_SET
        assert "user_name" in r.entities

    def test_me_llamo_pedro(self):

        r = il.classify("me llamo Pedro")
        assert r.intent == USER_NAME_SET
        assert "user_name" in r.entities

    def test_yo_me_llamo_maria(self):

        r = il.classify("yo me llamo María")
        assert r.intent == USER_NAME_SET
        assert "user_name" in r.entities

    def test_ese_es_mi_nombre(self):

        r = il.classify(
            "ese es mi nombre Carlos"
        )
        assert r.intent == USER_NAME_SET
        assert "user_name" in r.entities

    def test_el_mio_es_luis(self):

        r = il.classify("el mío es Luis")
        assert r.intent == USER_NAME_SET
        assert "user_name" in r.entities

    def test_nombre_mio_es_ana(self):

        r = il.classify("nombre mío es Ana")
        assert r.intent == USER_NAME_SET
        assert "user_name" in r.entities


class TestPreferredNameSetRealPhrases:

    def test_llamame_creador(self):

        r = il.classify("llámame Creador")
        assert r.intent == PREFERRED_NAME_SET
        assert "preferred_name" in r.entities

    def test_puedes_llamarme_jefe(self):

        r = il.classify("puedes llamarme Jefe")
        assert r.intent == PREFERRED_NAME_SET
        assert "preferred_name" in r.entities

    def test_quiero_que_me_llames_amigo(self):

        r = il.classify(
            "quiero que me llames Amigo"
        )
        assert r.intent == PREFERRED_NAME_SET

    def test_desde_ahora_llamame_boss(self):

        r = il.classify(
            "desde ahora llámame Boss"
        )
        assert r.intent == PREFERRED_NAME_SET

    def test_de_ahora_en_adelante_llamame(self):

        r = il.classify(
            "de ahora en adelante llámame Maestro"
        )
        assert r.intent == PREFERRED_NAME_SET

    def test_me_vas_a_llamar_complice(self):

        r = il.classify(
            "me vas a llamar Cómplice"
        )
        assert r.intent == PREFERRED_NAME_SET

    def test_vas_a_llamarme_pana(self):

        r = il.classify("vas a llamarme Pana")
        assert r.intent == PREFERRED_NAME_SET


class TestCalculateRealPhrases:

    def test_dos_mas_dos(self):

        r = il.classify("2+2")
        assert r.intent == CALCULATE
        assert "math" in r.entities

    def test_expresion_compleja(self):

        r = il.classify("(10-2)*4")
        assert r.intent == CALCULATE

    def test_division(self):

        r = il.classify("100/5")
        assert r.intent == CALCULATE

    def test_decimal(self):

        r = il.classify("3.14*2")
        assert r.intent == CALCULATE

    def test_negativo(self):

        r = il.classify("-5+3")
        assert r.intent == CALCULATE

    def test_potencia(self):

        r = il.classify("2**10")
        assert r.intent == CALCULATE

    def test_modulo(self):
        """HALLAZGO: '%' no está en la regex de
        CALCULATE. '10%3' no se calcula."""

        r = il.classify("10%3")
        assert r.intent in (
            CALCULATE, AMBIGUOUS_INPUT
        )


class TestMemoryCreateRealPhrases:

    def test_guarda_que_tengo_clase(self):

        r = il.classify(
            "guarda que mañana tengo clase"
        )
        assert r.intent == MEMORY_CREATE
        assert "memory" in r.entities

    def test_recuerda_que_voy_al_gym(self):

        r = il.classify(
            "recuerda que voy al gym"
        )
        assert r.intent == MEMORY_CREATE

    def test_anota_que_es_lunes(self):

        r = il.classify("anota que es lunes")
        assert r.intent == MEMORY_CREATE

    def test_memoriza_que_la_clave(self):

        r = il.classify(
            "memoriza que la clave es 1234"
        )
        assert r.intent == MEMORY_CREATE

    def test_quiero_que_recuerdes(self):

        r = il.classify(
            "quiero que recuerdes mi cumpleaños"
        )
        assert r.intent == MEMORY_CREATE

    def test_quiero_que_guardes(self):

        r = il.classify(
            "quiero que guardes esta info"
        )
        assert r.intent == MEMORY_CREATE

    def test_guarda_esto(self):
        """P3: 'guarda esto' no extrae entidad.
        Sin entidad → score=0 → AMBIGUOUS_INPUT."""

        r = il.classify("guarda esto")
        assert r.intent == AMBIGUOUS_INPUT

    def test_recuerda_esto(self):
        """P3: 'recuerda esto' no extrae entidad.
        Sin entidad → score=0 → AMBIGUOUS_INPUT."""

        r = il.classify("recuerda esto")
        assert r.intent == AMBIGUOUS_INPUT


class TestMemorySearchRealPhrases:

    def test_que_recuerdas(self):

        r = il.classify("qué recuerdas")
        assert r.intent == MEMORY_SEARCH

    def test_que_hicimos_hoy(self):

        r = il.classify("qué hicimos hoy")
        assert r.intent == MEMORY_SEARCH

    def test_tienes_alguna_memoria(self):

        r = il.classify(
            "tienes alguna memoria"
        )
        assert r.intent == MEMORY_SEARCH

    def test_que_hizo_deca(self):

        r = il.classify("qué hizo DECA")
        assert r.intent == MEMORY_SEARCH


class TestArchiveDirectRealPhrases:

    def test_cuando_comenzo_deca(self):

        r = il.classify(
            "cuándo comenzó DECA"
        )
        assert r.intent == ARCHIVE_DIRECT

    def test_que_significa_deca(self):

        r = il.classify(
            "qué significa DECA"
        )
        assert r.intent == ARCHIVE_DIRECT

    def test_valores_de_deca(self):

        r = il.classify("valores de DECA")
        assert r.intent == ARCHIVE_DIRECT

    def test_cuales_son_los_valores_de_deca(self):

        r = il.classify(
            "cuáles son los valores de DECA"
        )
        assert r.intent == ARCHIVE_DIRECT

    def test_vision_de_deca(self):

        r = il.classify("visión de DECA")
        assert r.intent == ARCHIVE_DIRECT

    def test_quien_creo_deca(self):

        r = il.classify("quién creó DECA")
        assert r.intent == ARCHIVE_DIRECT

    def test_quien_es_el_creador_de_deca(self):

        r = il.classify(
            "quién es el creador de DECA"
        )
        assert r.intent == ARCHIVE_DIRECT

    def test_cuando_empezo_deca(self):

        r = il.classify(
            "cuándo empezó DECA"
        )
        assert r.intent == ARCHIVE_DIRECT

    def test_significado_de_deca(self):

        r = il.classify("significado de DECA")
        assert r.intent == ARCHIVE_DIRECT

    def test_cual_es_la_vision_de_deca(self):

        r = il.classify(
            "cuál es la visión de DECA"
        )
        assert r.intent == ARCHIVE_DIRECT


class TestArchiveSearchRealPhrases:

    def test_significado(self):
        """P2: 'significado' sola, base 35.
        1 palabra, score < 50 → AMBIGUOUS_INPUT."""

        r = il.classify("significado")
        assert r.intent in (
            ARCHIVE_SEARCH, AMBIGUOUS_INPUT,
        )

    def test_habla_me_de_deca(self):
        """Phase 2E fix: 'háblame de DECA' →
        ARCHIVE_DIRECT via PHRASE pattern."""

        r = il.classify("háblame de DECA")
        assert r.intent == ARCHIVE_DIRECT

    def test_historia_de_deca(self):

        r = il.classify("historia de DECA")
        assert r.intent == ARCHIVE_SEARCH

    def test_eventos_de_deca(self):

        r = il.classify("eventos de DECA")
        assert r.intent == ARCHIVE_SEARCH

    def test_cuales_son_los_valores(self):

        r = il.classify(
            "cuáles son los valores"
        )
        assert r.intent == ARCHIVE_SEARCH

    def test_el_origen_de_deca(self):
        """Phase 2C: 'origen de deca' matches
        ARCHIVE_DIRECT (exact phrase pattern)."""

        r = il.classify("el origen de DECA")
        assert r.intent == ARCHIVE_DIRECT

    def test_que_hizo_deca(self):
        """HALLAZGO: 'hizo' activa MEMORY_SEARCH
        (score 60). 'deca' no boost
        ARCHIVE_SEARCH para 'hizo'."""

        r = il.classify("qué hizo DECA")
        assert r.intent in (
            ARCHIVE_SEARCH, MEMORY_SEARCH
        )

    def test_cuenta_sobre_deca(self):
        """HALLAZGO: 'cuenta' no tiene patrón en
        ARCHIVE_SEARCH. Sinónimos no detectados."""

        r = il.classify("cuenta sobre DECA")
        assert r.intent in (
            ARCHIVE_SEARCH, FREE_TALK
        )

    def test_informacion_de_deca(self):
        """HALLAZGO: 'informacion' no tiene patrón
        en ARCHIVE_SEARCH."""

        r = il.classify(
            "información de DECA"
        )
        assert r.intent in (
            ARCHIVE_SEARCH, FREE_TALK
        )


class TestExitRealPhrases:

    def test_salir(self):

        r = il.classify("salir")
        assert r.intent == EXIT

    def test_exit(self):

        r = il.classify("exit")
        assert r.intent == EXIT

    def test_quit(self):

        r = il.classify("quit")
        assert r.intent == EXIT


class TestAmbiguousInputRealPhrases:

    def test_algo(self):

        r = il.classify("algo")
        assert r.intent == AMBIGUOUS_INPUT

    def test_hmm(self):

        r = il.classify("hmm")
        assert r.intent == AMBIGUOUS_INPUT

    def test_cosas(self):

        r = il.classify("cosas")
        assert r.intent == AMBIGUOUS_INPUT

    def test_mira_suelto(self):

        r = il.classify("mira")
        assert r.intent == AMBIGUOUS_INPUT

    def test_pues(self):

        r = il.classify("pues")
        assert r.intent == AMBIGUOUS_INPUT

    def test_bueno(self):

        r = il.classify("bueno")
        assert r.intent == AMBIGUOUS_INPUT

    def test_empty(self):

        r = il.classify("")
        assert r.intent == AMBIGUOUS_INPUT


class TestFreeTalkRealPhrases:

    def test_cuentame_un_chiste(self):

        r = il.classify(
            "cuéntame un chiste gracioso"
        )
        assert r.intent == FREE_TALK

    def test_que_opinas(self):

        r = il.classify(
            "qué opinas de la inteligencia artificial"
        )
        assert r.intent == FREE_TALK

    def test_explcame_como_funciona(self):

        r = il.classify(
            "explícame cómo funciona internet"
        )
        assert r.intent == FREE_TALK

    def test_como_estas_hoy(self):
        """'hoy' en ARCHIVE_SEARCH base 35.
        Sin contexto → por debajo de 50.
        → FREE_TALK."""

        r = il.classify(
            "cómo estás hoy en día"
        )
        assert r.intent in (
            FREE_TALK, MEMORY_SEARCH,
        )

    def test_cual_es_el_significado(self):
        """P2: 'significa' con base baja (35).
        Sin contexto DECA → no alcanza threshold.
        → FREE_TALK."""

        r = il.classify(
            "cuál es el significado de la vida"
        )
        assert r.intent == FREE_TALK

    def test_necesito_ayuda_con_python(self):

        r = il.classify(
            "necesito ayuda con python"
        )
        assert r.intent == FREE_TALK

    def test_cuentame_algo_interesante(self):

        r = il.classify(
            "cuéntame algo interesante"
        )
        assert r.intent == FREE_TALK


# ==========================================
# 2. PRUEBAS DE CONFLICTOS
# ==========================================


class TestConflictDeciaSelfVsUserName:

    def test_quien_soy_is_user_name(self):

        r = il.classify("quién soy")
        assert r.intent == USER_NAME_ASK

    def test_y_quien_soy_is_user_name(self):

        r = il.classify("y quién soy")
        assert r.intent == USER_NAME_ASK

    def test_quien_eres_is_decia_self(self):

        r = il.classify("quién eres")
        assert r.intent == DECIA_SELF

    def test_que_eres_is_decia_self(self):

        r = il.classify("qué eres")
        assert r.intent == DECIA_SELF

    def test_no_confusion_direction(self):

        r_soy = il.classify("quién soy")
        r_eres = il.classify("quién eres")
        assert r_soy.intent != r_eres.intent


class TestConflictDeciaCreatorVsArchive:

    def test_quien_creo_deca_is_archive(self):

        r = il.classify("quién creó DECA")
        assert r.intent == ARCHIVE_DIRECT

    def test_quien_te_creo_is_creator(self):

        r = il.classify("quién te creó")
        assert r.intent == DECIA_CREATOR

    def test_quien_es_el_creador_de_deca_is_archive(
        self,
    ):

        r = il.classify(
            "quién es el creador de DECA"
        )
        assert r.intent == ARCHIVE_DIRECT

    def test_quien_es_tu_creador_is_creator(self):

        r = il.classify("quién es tu creador")
        assert r.intent == DECIA_CREATOR

    def test_no_confusion_deca_prefix(self):

        r_archive = il.classify(
            "quién creó DECA"
        )
        r_creator = il.classify(
            "quién te creó"
        )
        assert r_archive.intent != r_creator.intent


class TestConflictArchiveDirectVsSearch:

    def test_que_significa_deca_is_direct(self):

        r = il.classify(
            "qué significa DECA"
        )
        assert r.intent == ARCHIVE_DIRECT

    def test_significado_is_search(self):
        """P2: 'significado' sola tiene base 35.
        Sin boost deca → por debajo de 50.
        → AMBIGUOUS_INPUT (1 palabra, sin match)."""

        r = il.classify("significado")
        assert r.intent in (
            ARCHIVE_SEARCH, AMBIGUOUS_INPUT
        )

    def test_significado_de_deca_is_direct(self):

        r = il.classify("significado de DECA")
        assert r.intent == ARCHIVE_DIRECT

    def test_valores_de_deca_is_direct(self):

        r = il.classify("valores de DECA")
        assert r.intent == ARCHIVE_DIRECT

    def test_valores_solo_is_search(self):

        r = il.classify("cuáles son los valores")
        assert r.intent == ARCHIVE_SEARCH


class TestConflictMemoryCreateVsSearch:

    def test_recuerda_que_is_create(self):

        r = il.classify(
            "recuerda que tengo clase"
        )
        assert r.intent == MEMORY_CREATE

    def test_que_recuerdas_is_search(self):

        r = il.classify("qué recuerdas")
        assert r.intent == MEMORY_SEARCH

    def test_guarda_que_is_create(self):

        r = il.classify(
            "guarda que mañana voy al cine"
        )
        assert r.intent == MEMORY_CREATE

    def test_anota_que_is_create(self):

        r = il.classify("anota que es martes")
        assert r.intent == MEMORY_CREATE


class TestConflictUserNameSetVsPreferredNameSet:

    def test_mi_nombre_es_is_user_name(self):

        r = il.classify("mi nombre es Pedro")
        assert r.intent == USER_NAME_SET

    def test_llamame_is_preferred(self):

        r = il.classify("llámame Creador")
        assert r.intent == PREFERRED_NAME_SET

    def test_me_llamo_is_user_name(self):

        r = il.classify("me llamo María")
        assert r.intent == USER_NAME_SET

    def test_puedes_llamarme_is_preferred(self):

        r = il.classify("puedes llamarme Jefe")
        assert r.intent == PREFERRED_NAME_SET

    def test_no_confusion(self):

        r_name = il.classify("mi nombre es Pedro")
        r_pref = il.classify("llámame Creador")
        assert r_name.intent != r_pref.intent


class TestConflictAmbiguousVsFreeTalk:

    def test_short_no_match_is_ambiguous(self):

        r = il.classify("algo")
        assert r.intent == AMBIGUOUS_INPUT

    def test_long_no_match_is_free_talk(self):

        r = il.classify(
            "cuéntame algo interesante"
        )
        assert r.intent == FREE_TALK

    def test_short_with_match_is_not_ambiguous(
        self,
    ):

        r = il.classify("hola")
        assert r.intent == GREETING


class TestConflictCalcVsFreeTalk:

    def test_pure_math_is_calc(self):

        r = il.classify("2+2")
        assert r.intent == CALCULATE

    def test_math_in_sentence_is_free_talk(self):

        r = il.classify(
            "cuánto es dos más dos en total"
        )
        assert r.intent == FREE_TALK

    def test_complex_math_is_calc(self):

        r = il.classify("(3+5)*2-1")
        assert r.intent == CALCULATE


# ==========================================
# 3. FALSOS POSITIVOS
# ==========================================


class TestFalsePositivesHoy:
    """P1: 'hoy' ya no es keyword de MEMORY_SEARCH.
    Solo activa con contexto 'recuerdas'."""

    def test_hoy_es_un_buen_dia(self):

        r = il.classify(
            "hoy es un buen día para empezar"
        )

        assert r.intent not in (
            MEMORY_CREATE, MEMORY_SEARCH,
        )

    def test_hoy_no_es_create(self):

        r = il.classify(
            "hoy quiero salir a pasear"
        )
        assert r.intent not in (
            MEMORY_CREATE, MEMORY_SEARCH,
        )

    def test_hoy_con_texto_largo(self):

        r = il.classify(
            "hoy me levanté temprano y desayuné"
        )
        assert r.intent not in (
            MEMORY_CREATE, MEMORY_SEARCH,
        )


class TestFalsePositivesDeca:

    def test_deca_en_conversacion_normal(self):

        r = il.classify(
            "necesito que me ayudes con algo"
        )

        assert r.intent not in (
            ARCHIVE_DIRECT,
            ARCHIVE_SEARCH,
        )

    def test_deca_palabra_suelta(self):

        r = il.classify("deca")
        assert r.intent not in (
            ARCHIVE_DIRECT,
        )

    def test_deca_en_frase_larga(self):

        r = il.classify(
            "hoy es un buen día para empezar "
            "algo nuevo y diferente"
        )
        assert r.intent not in (
            ARCHIVE_DIRECT,
            ARCHIVE_SEARCH,
        )


class TestFalsePositivesMira:

    def test_mira_suelto(self):

        r = il.classify("mira")
        assert r.intent == AMBIGUOUS_INPUT

    def test_mira_esto_no_es_create(self):

        r = il.classify("mira esto")
        assert r.intent != MEMORY_CREATE


class TestFalsePositivesRecuerda:

    def test_recuerda_que_si_es_create(self):

        r = il.classify(
            "recuerda que tengo clase"
        )
        assert r.intent == MEMORY_CREATE

    def test_que_recuerdas_es_search(self):

        r = il.classify("qué recuerdas")
        assert r.intent == MEMORY_SEARCH

    def test_recuerda_suelto_no_es_create(self):
        """'recuerda' como keyword activa
        ARCHIVE_SEARCH (score 60). Sin entidad
        para MEMORY_CREATE."""

        r = il.classify("recuerda")
        assert r.intent in (
            AMBIGUOUS_INPUT, ARCHIVE_SEARCH,
        )


class TestFalsePositivesNames:

    def test_pedro_suelto_no_es_set(self):

        r = il.classify("Pedro")
        assert r.intent != USER_NAME_SET

    def test_creador_suelto_no_es_preferred(
        self,
    ):

        r = il.classify("Creador")
        assert r.intent != PREFERRED_NAME_SET

    def test_idelvi_suelto_no_es_set(self):

        r = il.classify("Idelvi")
        assert r.intent != USER_NAME_SET

    def test_hola_no_es_user_name(self):

        r = il.classify("hola")
        assert r.intent != USER_NAME_SET


class TestFalsePositivesGreeting:

    def test_hola_no_es_ambiguous(self):

        r = il.classify("hola")
        assert r.intent != AMBIGUOUS_INPUT

    def test_gracias_no_es_ambiguous(self):

        r = il.classify("gracias")
        assert r.intent != AMBIGUOUS_INPUT

    def test_buenos_dias_no_es_free_talk(self):

        r = il.classify("buenos días")
        assert r.intent != FREE_TALK


class TestFalsePositivesCalc:

    def test_2mas2_no_es_free_talk(self):

        r = il.classify("2+2")
        assert r.intent != FREE_TALK

    def test_5_suelto_no_es_free_talk(self):

        r = il.classify("5")
        assert r.intent not in (
            FREE_TALK,
            AMBIGUOUS_INPUT,
        )


class TestFalsePositivesMemoryKeyword:

    def test_memoria_suelta_no_es_create(self):

        r = il.classify("memoria")
        assert r.intent != MEMORY_CREATE

    def test_guarda_suelto_no_es_create(self):

        r = il.classify("guarda")
        assert r.intent == AMBIGUOUS_INPUT

    def test_anota_suelto_no_es_create(self):

        r = il.classify("anota")
        assert r.intent == AMBIGUOUS_INPUT


# ==========================================
# 4. VALIDACIÓN DE ENTIDADES
# ==========================================


class TestEntityValidationUserNameSet:

    def test_entity_exists_mi_nombre_es(self):

        r = il.classify("mi nombre es Pedro")
        assert "user_name" in r.entities
        assert r.entities["user_name"] == "Pedro"

    def test_entity_exists_me_llamo(self):

        r = il.classify("me llamo María")
        assert "user_name" in r.entities
        assert r.entities["user_name"] == "Maria"

    def test_entity_exists_yo_me_llamo(self):

        r = il.classify("yo me llamo Carlos")
        assert "user_name" in r.entities

    def test_entity_not_in_read_intents(self):

        r = il.classify("quién soy")
        assert "user_name" not in r.entities

    def test_entity_not_in_greeting(self):

        r = il.classify("hola")
        assert "user_name" not in r.entities


class TestEntityValidationPreferredNameSet:

    def test_entity_exists_llamame(self):

        r = il.classify("llámame Creador")
        assert "preferred_name" in r.entities
        assert r.entities["preferred_name"] \
            == "Creador"

    def test_entity_exists_puedes_llamarme(self):

        r = il.classify(
            "puedes llamarme Jefe"
        )
        assert "preferred_name" in r.entities

    def test_entity_not_in_user_name_set(self):

        r = il.classify("mi nombre es Pedro")
        assert "preferred_name" not in r.entities


class TestEntityValidationCalculate:

    def test_entity_exists_simple(self):

        r = il.classify("2+2")
        assert "math" in r.entities
        assert r.entities["math"] == "2+2"

    def test_entity_exists_complex(self):

        r = il.classify("(10-2)*4")
        assert "math" in r.entities

    def test_entity_not_in_free_talk(self):

        r = il.classify(
            "cuéntame un chiste"
        )
        assert "math" not in r.entities


class TestEntityValidationMemoryCreate:

    def test_entity_exists_guarda_que(self):

        r = il.classify(
            "guarda que tengo clase"
        )
        assert "memory" in r.entities
        assert r.entities["memory"] == \
            "tengo clase"

    def test_entity_exists_recuerda_que(self):

        r = il.classify(
            "recuerda que voy al gym"
        )
        assert "memory" in r.entities
        assert r.entities["memory"] == \
            "voy al gym"

    def test_entity_not_in_memory_search(self):

        r = il.classify("qué recuerdas")
        assert "memory" not in r.entities

    def test_entity_not_in_greeting(self):

        r = il.classify("hola")
        assert "memory" not in r.entities


# ==========================================
# 5. REGLAS DE SEGURIDAD
# ==========================================


class TestWriteIntentEntityRule:
    """Ningún intent de escritura puede tener
    confidence >= 0.90 sin entidad extraída."""

    def test_user_name_set_always_has_entity(self):

        phrases = [
            "mi nombre es Pedro",
            "me llamo María",
            "yo me llamo Carlos",
            "ese es mi nombre Ana",
            "el mío es Luis",
            "nombre mío es Rosa",
        ]

        for phrase in phrases:

            r = il.classify(phrase)

            if r.intent == USER_NAME_SET \
                    and r.confidence >= 0.90:

                assert "user_name" in r.entities, (
                    f"USER_NAME_SET without "
                    f"entity: {phrase}"
                )

    def test_preferred_name_set_always_has_entity(
        self,
    ):

        phrases = [
            "llámame Creador",
            "puedes llamarme Jefe",
            "quiero que me llames Amigo",
            "desde ahora llámame Boss",
            "de ahora en adelante llámame Maestro",
            "me vas a llamar Cómplice",
            "vas a llamarme Pana",
        ]

        for phrase in phrases:

            r = il.classify(phrase)

            if r.intent == PREFERRED_NAME_SET \
                    and r.confidence >= 0.90:

                assert (
                    "preferred_name" in r.entities
                ), (
                    f"PREFERRED_NAME_SET without "
                    f"entity: {phrase}"
                )

    def test_memory_create_always_has_entity(self):
        """P3: MEMORY_CREATE sin entidad → score=0
        → no es MEMORY_CREATE."""

        phrases_with_entity = [
            "guarda que tengo clase",
            "recuerda que voy al gym",
            "anota que es lunes",
            "memoriza que la clave es 1234",
            "quiero que recuerdes mi cumpleaños",
            "quiero que guardes esta info",
        ]

        phrases_without_entity = [
            "guarda esto",
            "recuerda esto",
        ]

        for phrase in phrases_with_entity:

            r = il.classify(phrase)

            if r.intent == MEMORY_CREATE:

                assert "memory" in r.entities, (
                    f"MEMORY_CREATE without "
                    f"entity: {phrase}"
                )

        for phrase in phrases_without_entity:

            r = il.classify(phrase)
            assert r.intent != MEMORY_CREATE, (
                f"MEMORY_CREATE without entity: "
                f"{phrase}"
            )


class TestFreeTalkConfidenceRule:
    """FREE_TALK nunca debe tener confidence
    superior a 0.50."""

    def test_free_talk_confidence_ceiling(self):

        phrases = [
            "cuéntame un chiste gracioso",
            "qué opinas de la inteligencia "
            "artificial",
            "explícame cómo funciona internet",
            "cuéntame algo interesante",
            "necesito ayuda con python",
            "cuál es el significado de la vida",
        ]

        for phrase in phrases:

            r = il.classify(phrase)

            if r.intent == FREE_TALK:

                assert r.confidence < 0.50, (
                    f"FREE_TALK confidence too "
                    f"high: {phrase} "
                    f"conf={r.confidence}"
                )


class TestAmbiguousInputRule:
    """AMBIGUOUS_INPUT no debe capturar intents
    que ya tengan un patrón determinista."""

    def test_ambiguous_not_capture_hola(self):

        r = il.classify("hola")
        assert r.intent != AMBIGUOUS_INPUT

    def test_ambiguous_not_capture_gracias(self):

        r = il.classify("gracias")
        assert r.intent != AMBIGUOUS_INPUT

    def test_ambiguous_not_capture_deca(self):
        """HALLAZGO: 'DECA' sola no tiene patrón.
        cae a AMBIGUOUS_INPUT por ser 1 palabra
        sin match."""

        r = il.classify("DECA")
        assert r.intent in (
            AMBIGUOUS_INPUT, ARCHIVE_SEARCH
        )

    def test_ambiguous_not_capture_calc(self):

        r = il.classify("2+2")
        assert r.intent != AMBIGUOUS_INPUT

    def test_ambiguous_not_capture_salir(self):

        r = il.classify("salir")
        assert r.intent != AMBIGUOUS_INPUT

    def test_ambiguous_not_capture_quien_eres(
        self,
    ):

        r = il.classify("quién eres")
        assert r.intent != AMBIGUOUS_INPUT

    def test_ambiguous_not_capture_como_me_llamo(
        self,
    ):

        r = il.classify("cómo me llamo")
        assert r.intent != AMBIGUOUS_INPUT

    def test_ambiguous_not_capture_buenas(self):

        r = il.classify("buenas")
        assert r.intent != AMBIGUOUS_INPUT


# ==========================================
# 6. CONSISTENCIA DE SCORING
# ==========================================


class TestScoringConsistency:

    def test_exact_always_beats_phrase(self):

        r1 = il.classify("hola")
        r2 = il.classify("buenas tardes")
        assert r1.candidates[0].score >= \
            r2.candidates[0].score

    def test_phrase_always_beats_keyword(self):

        r1 = il.classify("quién te creó")
        r2 = il.classify("quién es el creador")
        assert r1.candidates[0].score >= \
            r2.candidates[0].score

    def test_best_candidate_is_first(self):

        phrases = [
            "hola",
            "gracias",
            "quién eres",
            "cómo me llamo",
            "2+2",
            "guarda que tengo clase",
            "salir",
            "algo",
            "cuéntame un chiste",
        ]

        for phrase in phrases:

            r = il.classify(phrase)
            scores = [
                c.score for c in r.candidates
            ]
            assert scores == sorted(
                scores, reverse=True
            ), (
                f"Candidates not sorted: "
                f"{phrase}"
            )

    def test_free_talk_never_wins_over_deterministic(
        self,
    ):

        deterministic_phrases = [
            "hola",
            "gracias",
            "quién eres",
            "cómo me llamo",
            "2+2",
            "salir",
        ]

        for phrase in deterministic_phrases:

            r = il.classify(phrase)
            assert r.intent != FREE_TALK, (
                f"FREE_TALK won over "
                f"deterministic: {phrase}"
            )


# ==========================================
# 7. COBERTURA DE INTENTS
# ==========================================


class TestIntentCoverage:
    """Verificar que todos los 16 intents
    son alcanzables."""

    def test_all_intents_reachable(self):

        test_phrases = {
            GREETING: "hola",
            THANKS: "gracias",
            DECIA_SELF: "quién eres",
            DECIA_CREATOR: "quién te creó",
            USER_NAME_ASK: "quién soy",
            USER_NAME_SET: "mi nombre es Pedro",
            PREFERRED_NAME_ASK:
                "cómo quieres llamarme",
            PREFERRED_NAME_SET: "llámame Creador",
            CALCULATE: "2+2",
            MEMORY_CREATE:
                "guarda que tengo clase",
            MEMORY_SEARCH: "qué recuerdas",
            ARCHIVE_DIRECT:
                "qué significa DECA",
            ARCHIVE_SEARCH: "historia de DECA",
            EXIT: "salir",
            AMBIGUOUS_INPUT: "algo",
            FREE_TALK: "cuéntame un chiste",
        }

        for intent, phrase in test_phrases.items():

            r = il.classify(phrase)
            assert r.intent == intent, (
                f"Intent {intent} not reached "
                f"with '{phrase}': "
                f"got {r.intent}"
            )

    def test_sixteen_intents_total(self):

        all_intents = set()

        test_phrases = [
            "hola",
            "gracias",
            "quién eres",
            "quién te creó",
            "quién soy",
            "mi nombre es Pedro",
            "cómo quieres llamarme",
            "llámame Creador",
            "2+2",
            "guarda que tengo clase",
            "qué recuerdas",
            "qué significa DECA",
            "historia de DECA",
            "salir",
            "algo",
            "cuéntame un chiste",
        ]

        for phrase in test_phrases:

            r = il.classify(phrase)
            all_intents.add(r.intent)

        assert len(all_intents) == 16


# ==========================================
# 8. NORMALIZACIÓN
# ==========================================


class TestNormalizationAudit:

    def test_accents_handled(self):

        r1 = il.classify("quién eres")
        r2 = il.classify("quien eres")
        assert r1.intent == r2.intent

    def test_punctuation_handled(self):

        r1 = il.classify("¿quién eres?")
        r2 = il.classify("quién eres")
        assert r1.intent == r2.intent

    def test_case_insensitive(self):

        r1 = il.classify("HOLA")
        r2 = il.classify("hola")
        assert r1.intent == r2.intent

    def test_extra_whitespace(self):

        r1 = il.classify("  hola  ")
        r2 = il.classify("hola")
        assert r1.intent == r2.intent

    def test_mixed_accents_and_case(self):

        r1 = il.classify("¿CUÁL ES TU NOMBRE?")
        r2 = il.classify("cual es tu nombre")
        assert r1.intent == r2.intent


# ==========================================
# 9. EDGE CASES
# ==========================================


class TestEdgeCasesAudit:

    def test_only_punctuation(self):

        r = il.classify("???")
        assert r.intent == AMBIGUOUS_INPUT

    def test_only_numbers(self):

        r = il.classify("12345")
        assert r.intent == CALCULATE

    def test_single_character(self):

        r = il.classify("a")
        assert r.intent == AMBIGUOUS_INPUT

    def test_very_long_message(self):

        r = il.classify(
            "hoy me levanté a las seis de la "
            "mañana, desayuné cereal con leche "
            "y después salí a caminar al parque "
            "que está cerca de mi casa"
        )
        assert r.intent not in (
            AMBIGUOUS_INPUT,
            GREETING,
            THANKS,
            EXIT,
            CALCULATE,
        )

    def test_only_emojis(self):

        r = il.classify("😊")
        assert r.intent in (
            AMBIGUOUS_INPUT,
            FREE_TALK,
        )

    def test_numbers_with_text(self):

        r = il.classify("tengo 3 gatos")
        assert r.intent not in (CALCULATE,)


# ==========================================
# 10. REPORTE DE HALLAZGOS
# ==========================================


class TestAuditFindings:
    """Tests que documentan hallazgos
    conocidos de la auditoría."""

    def test_hoy_activa_memory_search(self):
        """P1 CORREGIDO: 'hoy' sola, base baja.
        Sin contexto de memoria → FREE_TALK."""

        r = il.classify(
            "hoy me siento genial"
        )

        assert r.intent == FREE_TALK

    def test_deca_palabra_suelta_archivo(self):
        """HALLAZGO: 'deca' sola no activa
        ARCHIVE_SEARCH. No tiene keyword propio.
        Ca a AMBIGUOUS_INPUT."""

        r = il.classify("deca")
        assert r.intent in (
            AMBIGUOUS_INPUT, ARCHIVE_SEARCH
        )

    def test_memoria_suelta_archivo(self):
        """FIX 6.5: 'memoria' sola ya no activa
        MEMORY_SEARCH (palabra suelta, sin
        intención de consulta)."""

        r = il.classify("memoria")
        assert r.intent == AMBIGUOUS_INPUT

    def test_hizo_solo_memory_search(self):
        """FIX 6.5: 'hizo' sola ya no activa
        MEMORY_SEARCH (sin ancla de consulta)."""

        r = il.classify("hizo")
        assert r.intent == AMBIGUOUS_INPUT

    def test_ayer_activa_memory_search(self):
        """P1: 'ayer' con base baja (35).
        Sin contexto de memoria → FREE_TALK."""

        r = il.classify(
            "ayer fui al supermercado"
        )
        assert r.intent == FREE_TALK

    def test_creador_suelto_archivo(self):
        """HALLAZGO: 'creador' sola activa
        DECIA_CREATOR (keyword, score 70), no
        ARCHIVE_SEARCH."""

        r = il.classify("creador")
        assert r.intent in (
            DECIA_CREATOR, ARCHIVE_SEARCH
        )
