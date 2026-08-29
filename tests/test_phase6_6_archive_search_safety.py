"""
PHASE 6.6 — ARCHIVE_SEARCH SAFETY

ARCHIVE = consulta explícita sobre DECA (archivo,
historia, identidad). Una palabra cotidiana
('creo', 'historia', 'valores', 'inicio', ...) por
sí sola NO otorga el executor determinista.
La intención debe estar respaldada por un ancla
explícita que exige contexto DECA.
"""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "app"),
)

from brain.intent_layer import IntentLayer
from brain.core import think
from brain.context import ConversationContext

from brain.intent_types import (
    MEMORY_SEARCH,
    ARCHIVE_SEARCH,
    ARCHIVE_DIRECT,
    MEMORY_CREATE,
    FREE_TALK,
    AMBIGUOUS_INPUT,
    DECIA_CREATOR,
)

IL = IntentLayer()

ARCHIVE_INTENTS = (ARCHIVE_DIRECT, ARCHIVE_SEARCH)

# Respuesta determinista de los ejecutores
# ARCHIVE/ARCHIVE_DIRECT cuando no encuentran.
ARCHIVE_EMPTY_REPLY = "No encontré información"


def _classify(message):
    return IL.classify(message)


def _is_archive(message):
    return (
        _classify(message).intent in ARCHIVE_INTENTS
    )


# ==========================================
# A. CONSULTAS LEGÍTIMAS DECA (MANDATORIAS)
# ==========================================


class TestLegitQueriesMandatorias:

    @pytest.mark.parametrize("ask", [
        "que significa deca",
        "cual es la historia de deca",
        "cuando comenzo deca",
        "cual es el origen de deca",
        "cuales son los valores de deca",
        "quien es el fundador de deca",
        "que objetivos tiene deca",
        "que hay registrado sobre deca",
    ])
    def test_legit_deca_queda_archive(self, ask):
        assert _is_archive(ask), ask

    @pytest.mark.parametrize("ask,esperado", [
        ("que significa deca", ARCHIVE_DIRECT),
        ("cuando comenzo deca", ARCHIVE_DIRECT),
        ("cual es el origen de deca",
         ARCHIVE_DIRECT),
        ("cuales son los valores de deca",
         ARCHIVE_DIRECT),
        ("quien es el fundador de deca",
         ARCHIVE_DIRECT),
        ("cual es la historia de deca",
         ARCHIVE_SEARCH),
        ("que objetivos tiene deca",
         ARCHIVE_SEARCH),
        ("que hay registrado sobre deca",
         ARCHIVE_SEARCH),
    ])
    def test_legit_deca_intent_especifico(
        self, ask, esperado
    ):
        result = _classify(ask)
        assert result.intent == esperado, ask


# ==========================================
# B. NEGATIVOS MANDATORIOS (NUNCA ARCHIVE)
# ==========================================


class TestNegativosMandatorios:

    @pytest.mark.parametrize("ask", [
        "yo creo que si",
        "cuentame una historia",
        "tengo una vision borrosa",
        "mi objetivo de hoy",
        "el archivo adjunto",
        "el inicio de sesion",
        "el fundador de la empresa",
        "como comenzo el fuego",
    ])
    def test_nunca_archive(self, ask):
        assert not _is_archive(ask), ask

    @pytest.mark.parametrize("ask", [
        "yo creo que si",
        "cuentame una historia",
        "tengo una vision borrosa",
        "mi objetivo de hoy",
        "el archivo adjunto",
        "el inicio de sesion",
        "el fundador de la empresa",
        "como comenzo el fuego",
    ])
    def test_cae_a_ollama_o_ambiguo(self, ask):
        r = _classify(ask)
        assert r.intent in (
            FREE_TALK, AMBIGUOUS_INPUT,
        ), ask


# ==========================================
# C. FALSOS POSITIVOS AUDITADOS (PHASE 6.4)
# ==========================================


class TestFalsosPositivosAuditados:

    @pytest.mark.parametrize("ask", [
        "la pelicula empezo bien",
        "el bebe nacio anoche",
        "origen de la especie humana",
        "defiendo mis valores",
        "morir por principios",
        "fundo una ong",
        "el proximo evento",
        "los eventos del dia",
        "un acontecimiento historico",
        "historia de la musica",
        "vision general del negocio",
        "cuales son tus principios",
        "cual es el origen de la vida",
        "que evento importante paso",
        "como empezo la crisis",
        "cual es la vision del negocio",
    ])
    def test_no_archive(self, ask):
        assert not _is_archive(ask), ask


# ==========================================
# D. CONFIANZA EN ANCLAS
# ==========================================


class TestConfianzaAnclas:

    @pytest.mark.parametrize("ask", [
        "que significa deca",
        "cuando comenzo deca",
        "cuando empezo deca",
        "significado de deca",
        "valores de deca",
        "vision de deca",
        "quien creo deca",
        "quien es el creador de deca",
        "origen de deca",
        "quien fundo deca",
        "hablame de deca",
        "fundador de deca",
        "principios de deca",
        "cuando inicio deca",
        "donde nacio deca",
    ])
    def test_direct_alta_confianza(self, ask):
        r = _classify(ask)
        assert r.intent == ARCHIVE_DIRECT, ask
        assert r.confidence >= 0.70, ask

    @pytest.mark.parametrize("ask", [
        "cual es la historia de deca",
        "eventos de deca",
        "que objetivos tiene deca",
        "objetivo de deca",
        "que hay registrado sobre deca",
    ])
    def test_search_confianza_alcanza_umbral(
        self, ask
    ):
        r = _classify(ask)
        assert r.intent == ARCHIVE_SEARCH, ask
        assert r.confidence >= 0.50, ask


# ==========================================
# E. PALABRA SUELTA / SIN CONTEXTO DECA
# ==========================================


class TestPalabrasSueltas:

    @pytest.mark.parametrize("ask", [
        "significado",
        "significa",
        "memoria",
        "memorias",
        "recuerdo",
    ])
    def test_base_baja_sin_contexto(self, ask):
        r = _classify(ask)
        assert r.intent not in ARCHIVE_INTENTS, ask

    def test_significado_sola_ambiguo(self):
        r = _classify("significado")
        assert r.intent in (
            ARCHIVE_SEARCH, AMBIGUOUS_INPUT,
        )

    def test_cual_es_el_significado_de_la_vida(self):
        r = _classify(
            "cual es el significado de la vida"
        )
        assert r.intent == FREE_TALK

    def test_deca_sola_no_archive(self):
        r = _classify("deca")
        assert r.intent not in ARCHIVE_INTENTS

    @pytest.mark.parametrize("ask", [
        "significado de la vida",
        "origen de la vida",
        "valores de la empresa",
        "historia de mi familia",
        "vision profesional",
        "objetivo del dia",
    ])
    def test_sin_deca_queda_fuera(self, ask):
        assert not _is_archive(ask), ask


# ==========================================
# F. CRUCES DIRECT vs SEARCH vs LIBRE
# ==========================================


class TestCruces:

    def test_valores_solo_search(self):
        r = _classify("cuales son los valores")
        assert r.intent == ARCHIVE_SEARCH

    def test_valores_de_deca_direct(self):
        r = _classify("cuales son los valores de deca")
        assert r.intent == ARCHIVE_DIRECT
        assert r.confidence >= 0.90

    def test_fundador_de_deca_direct(self):
        r = _classify("quien es el fundador de deca")
        assert r.intent == ARCHIVE_DIRECT

    def test_fundador_sin_deca_no_archive(self):
        r = _classify("el fundador de la empresa")
        assert r.intent not in ARCHIVE_INTENTS

    def test_inicio_de_deca_direct(self):
        r = _classify("cuando inicio deca")
        assert r.intent == ARCHIVE_DIRECT

    def test_inicio_de_sesion_no_archive(self):
        r = _classify("el inicio de sesion")
        assert r.intent not in ARCHIVE_INTENTS

    def test_nacio_deca_direct(self):
        r = _classify("donde nacio deca")
        assert r.intent == ARCHIVE_DIRECT

    def test_historia_de_deca_search(self):
        r = _classify("historia de DECA")
        assert r.intent == ARCHIVE_SEARCH

    def test_cuentame_la_historia_search(self):
        r = _classify("cuentame la historia")
        assert r.intent == FREE_TALK

    def test_dime_la_historia_de_x_no_archive(self):
        r = _classify("dime la historia de Apple")
        assert r.intent not in ARCHIVE_INTENTS

    def test_hablame_de_la_historia_del_mundo_no_archive(
        self,
    ):
        r = _classify(
            "hablame de la historia del mundo"
        )
        assert r.intent not in ARCHIVE_INTENTS

    def test_cuentame_una_historia_no_archive(
        self,
    ):
        r = _classify("cuentame una historia")
        assert r.intent not in ARCHIVE_INTENTS

    def test_eventos_de_deca_search(self):
        r = _classify("eventos de deca")
        assert r.intent == ARCHIVE_SEARCH

    def test_quien_fundo_deca_direct(self):
        r = _classify("quien fundo deca")
        assert r.intent == ARCHIVE_DIRECT

    def test_quien_te_creo_creator(self):
        r = _classify("quien te creo")
        assert r.intent == DECIA_CREATOR


# ==========================================
# F2. LÍMITES (AUDITORÍA 6.6) — anclas
#     historia genérica y valores/principios
# ==========================================


class TestLimitsHistoriaGenerica:

    @pytest.mark.parametrize("ask", [
        "cuentame la historia",
        "cuentame la historia de Napoleon",
        "cuentame la historia de Republica "
        "Dominicana",
        "dime la historia de Apple",
        "dime la historia de mi abuela",
        "hablame la historia del mundo",
        "hablame de la historia del mundo",
    ])
    def test_sin_deca_va_a_ollama(self, ask):
        assert not _is_archive(ask), ask

    @pytest.mark.parametrize("ask", [
        "cuentame la historia de deca",
        "dime la historia de deca",
        "hablame de la historia de deca",
    ])
    def test_con_deca_sigue_siendo_archive(
        self, ask
    ):
        assert _is_archive(ask), ask


class TestLimitsValoresPrincipios:

    @pytest.mark.parametrize("ask", [
        "cuales son los valores",
        "cuales son los principios",
    ])
    def test_forma_desnuda_search(self, ask):
        r = _classify(ask)
        assert r.intent == ARCHIVE_SEARCH, ask

    @pytest.mark.parametrize("ask", [
        "cuales son los valores de deca",
        "cuales son los principios de deca",
    ])
    def test_con_deca_direct(self, ask):
        r = _classify(ask)
        assert r.intent == ARCHIVE_DIRECT, ask

    @pytest.mark.parametrize("ask", [
        "cuales son los valores de mi empresa",
        "cuales son los valores del equipo",
        "cuales son los principios del estoicismo",
        "cuales son los principios de la filosofia",
        "cuales son los valores de la empresa",
        "cuales son los valores de hoy",
    ])
    def test_de_x_o_del_x_sin_deca_no_archive(
        self, ask
    ):
        assert not _is_archive(ask), ask


# ==========================================
# G. INTERACCIÓN CON MEMORY_SEARCH (INTACTO)
# ==========================================


class TestMemorySearchIntacto:

    @pytest.mark.parametrize("ask", [
        "que hice",
        "que hicimos",
        "que hablamos",
        "que te dije",
        "que recuerdas",
        "que paso ayer",
    ])
    def test_memory_legitima_intacta(self, ask):
        assert _classify(ask).intent == MEMORY_SEARCH

    def test_recuerda_que_sigue_siendo_create(self):
        r = _classify("recuerda que tengo clase")
        assert r.intent == MEMORY_CREATE


# ==========================================
# H. ASSISTED ROUTING (OLLAMA vs EXECUTOR)
# ==========================================


class TestAssistedRouting:

    def test_consulta_deca_usa_archive_sin_ollama(
        self,
    ):
        with patch(
            "brain.core.ask_ollama",
            return_value="OLLAMA",
        ) as mock_ollama:
            response = think(
                "cual es la historia de deca",
                context=ConversationContext(),
            )
        assert mock_ollama.called is False
        assert "No encontré información" not in (
            response
        )

    def test_negativo_va_a_ollama(self):
        with patch(
            "brain.core.ask_ollama",
            return_value="OLLAMA",
        ) as mock_ollama:
            response = think(
                "yo creo que si",
                context=ConversationContext(),
            )
        assert mock_ollama.called is True
        assert response == "OLLAMA"

    def test_inicio_de_sesion_no_archive_executor(
        self,
    ):
        with patch(
            "brain.core.ask_ollama",
            return_value="OLLAMA",
        ) as mock_ollama:
            response = think(
                "el inicio de sesion",
                context=ConversationContext(),
            )
        assert mock_ollama.called is True
        assert response == "OLLAMA"


# ==========================================
# I. NUNCA BÚSQUEDA DETERMINISTA EN NO-ARCHIVE
# ==========================================


class TestNoDeterministicArchive:

    @pytest.mark.parametrize("phrase", [
        "yo creo que si",
        "cuentame una historia",
        "tengo una vision borrosa",
        "mi objetivo de hoy",
        "el archivo adjunto",
        "el inicio de sesion",
        "el fundador de la empresa",
        "como comenzo el fuego",
        "defiendo mis valores",
        "morir por principios",
        "historia de la musica",
        "un acontecimiento historico",
    ])
    def test_no_emit_respuesta_archivo(self, phrase):
        with patch(
            "brain.core.ask_ollama",
            return_value="OLLAMA",
        ) as mock_ollama:
            response = think(
                phrase,
                context=ConversationContext(),
            )
        if mock_ollama.called:
            assert response == "OLLAMA"
            assert ARCHIVE_EMPTY_REPLY not in (
                response
            ), phrase
        else:
            assert ARCHIVE_EMPTY_REPLY not in (
                response
            ), phrase