"""
PHASE 6.5 — MEMORY_SEARCH SAFETY

MEMORY_SEARCH = consulta a lo que DECIA recuerda/
registró. Una palabra cotidiana ('hice', 'memoria',
'recuerdo', ...) por sí sola NO otorga el executor.
La intención debe estar respaldada por un ancla
explícita ('que hice', 'que tienes en memoria', ...).
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
from brain.followup import resolve_follow_up

from brain.intent_types import (
    MEMORY_SEARCH,
    ARCHIVE_SEARCH,
    ARCHIVE_DIRECT,
    MEMORY_CREATE,
    FREE_TALK,
    AMBIGUOUS_INPUT,
)

IL = IntentLayer()

MEMORY_EXECUTOR_REPLIES = (
    "No tengo memorias registradas",
    "No recuerdo nada sobre",
    "recuerdas",
)


def _classify(message):
    return IL.classify(message)


def _not_memory(message):
    return (
        _classify(message).intent != MEMORY_SEARCH
    )


# ==========================================
# A. CONSULTAS LEGÍTIMAS (15+)
# ==========================================


class TestLegitimateMemoryQueries:

    @pytest.mark.parametrize("ask", [
        "que hice",
        "que hice hoy",
        "que hice ayer",
        "que hicimos",
        "que hicimos ayer",
        "que hablamos",
        "de que hablamos",
        "que hemos hablado",
        "que hemos hablado hoy",
        "que te dije",
        "que me dijiste",
        "que dijiste ayer",
        "que recuerdas",
        "que recuerdo",
        "que cosas recuerdas de mi",
        "recuerdame lo que hablamos hoy",
        "que tienes en memoria",
        "que memorias tienes",
        "tienes alguna memoria",
        "que recuerdas sobre maria",
        "que recuerdas de maria",
        "recuerdas algo sobre mi",
        "que paso ayer",
        "que hizo deca",
        "que sabes de mi",
        "que sabes sobre mi",
        "te acuerdas de eso",
        "recuerdas como se llama mi perro",
        "recuerdas que musica me gusta",
        "recuerdas que proyecto quiero terminar",
    ])
    def test_es_memory_search(self, ask):
        result = _classify(ask)
        assert result.intent == MEMORY_SEARCH, ask
        assert result.confidence >= 0.50, ask


# ==========================================
# B. NO-MEMORY (15+)
# ==========================================


class TestNoMemory:

    @pytest.mark.parametrize("phrase", [
        "yo hice la tarea",
        "el hizo la tarea",
        "lo hicimos bien",
        "como te dije",
        "he hablado con el medico",
        "tengo mala memoria",
        "mi mejor recuerdo",
        "tengo muchas memorias",
        "recuerdo esa pelicula",
        "recuerdo cuando era niño",
        "hablamos ayer con Juan",
        "la transmision en vivo",
        "compre unas memorias usb",
        "recuerdo de mi infancia",
        "no me acuerdo de nada",
        "hoy hace mucho calor",
        "ayer fui al supermercado",
        "me acorde de tu cumpleaños",
    ])
    def test_no_es_memory_search(self, phrase):
        assert _not_memory(phrase), phrase

    def test_ni_crea_memoria(self):
        for phrase in [
            "yo hice la tarea",
            "mi mejor recuerdo",
        ]:
            assert (
                _classify(phrase).intent
                != MEMORY_CREATE
            )


# ==========================================
# C. FALSOS POSITIVOS DE PHASE 6.4
# ==========================================


class TestPhase64FalsePositives:

    @pytest.mark.parametrize("phrase", [
        "yo hice la tarea",
        "tengo mala memoria",
        "mi mejor recuerdo",
        "lo hicimos bien",
        "como te dije",
        "he hablado con el medico",
        "la transmision en vivo",
        "compre unas memorias usb",
        "hablamos ayer con Juan",
    ])
    def test_p64_fp_corregidos(self, phrase):
        result = _classify(phrase)
        assert result.intent != MEMORY_SEARCH, phrase

    def test_palabra_suelta_no_ejecuta(self):
        for word in ["hice", "hizo", "memoria",
                     "memorias", "recuerdo",
                     "hablamos", "dije"]:
            result = _classify(word)
            assert result.intent in (
                FREE_TALK, AMBIGUOUS_INPUT,
            ), word


# ==========================================
# D. ACENTOS
# ==========================================


class TestAccents:

    @pytest.mark.parametrize("ask", [
        "qué hice",
        "qué hicimos",
        "qué hablamos",
        "qué te dije",
        "qué me dijiste",
        "qué recuerdas",
        "qué tienes en memoria",
        "qué memorias tienes",
    ])
    def test_consultas_con_acento(self, ask):
        assert (
            _classify(ask).intent == MEMORY_SEARCH
        ), ask

    @pytest.mark.parametrize("neg", [
        "yo hice la tarea",
        "él hizo la tarea",
        "recuerdo cuando era niño",
    ])
    def test_no_memory_con_acento(self, neg):
        assert _not_memory(neg), neg


# ==========================================
# E. PREGUNTAS NATURALES
# ==========================================


class TestNaturalQuestions:

    @pytest.mark.parametrize("ask", [
        "¿qué recuerdas sobre mi perro?",
        "¿me puedes recordar qué hice ayer?",
        "¿qué cosas recuerdas de mí?",
        "¿de qué hablamos la última vez?",
        "¿qué dijiste la semana pasada?",
        "¿y qué hicimos anteayer?",
        "¿me dijiste algo sobre el proyecto?",
    ])
    def test_consulta_natural(self, ask):
        assert (
            _classify(ask).intent == MEMORY_SEARCH
        ), ask


# ==========================================
# F. INTERACCIÓN CON MEMORY_SEARCH EXISTENTE
# ==========================================


class TestExistingMemorySearch:

    @pytest.mark.parametrize("ask", [
        "que sabes de mi",
        "que recuerdas de mi",
        "que paso",
        "que paso hoy",
        "como se llama mi perro",
        "cual es mi color favorito",
        "me gusta la musica de Kanye",
        "quiero terminar el curso",
        "en que proyecto estoy",
        "que recuerdame lo que te dije",
    ])
    def test_patrones_previos_intactos(self, ask):
        assert (
            _classify(ask).intent == MEMORY_SEARCH
        ), ask

    def test_recuerda_que_sigue_creando(self):
        result = _classify(
            "recuerda que tengo clase manana"
        )
        assert result.intent == MEMORY_CREATE
        assert "memory" in result.entities

    def test_que_recuerdas_no_crea(self):
        result = _classify("que recuerdas")
        assert result.intent == MEMORY_SEARCH


# ==========================================
# G. INTERACCIÓN CON ARCHIVE_SEARCH
# ==========================================


class TestArchiveInteraction:

    @pytest.mark.parametrize("ask", [
        "que significa deca",
        "valores de deca",
        "historia de deca",
        "cuando comenzo deca",
    ])
    def test_archive_deca_intacto(self, ask):
        assert _classify(ask).intent in (
            ARCHIVE_DIRECT, ARCHIVE_SEARCH,
        ), ask

    def test_que_recuerdas_de_deca_cae_a_memoria(
        self,
    ):
        result = _classify("que recuerdas de deca")
        assert result.intent == MEMORY_SEARCH


# ==========================================
# H. ASSISTED ROUTING
# ==========================================


class TestAssistedRouting:

    def test_consulta_memory_sin_ollama(self):
        with patch(
            "brain.core.ask_ollama",
            return_value="OLLAMA",
        ) as mock_ollama:
            response = think(
                "que hice",
                context=ConversationContext(),
            )
        assert mock_ollama.called is False
        assert response == "OLLAMA" or (
            "No tengo memorias" in response
            or "No recuerdo" in response
        )

    def test_no_memory_va_a_ollama(self):
        with patch(
            "brain.core.ask_ollama",
            return_value="OLLAMA",
        ) as mock_ollama:
            response = think(
                "yo hice la tarea",
                context=ConversationContext(),
            )
        assert mock_ollama.called is True
        assert response == "OLLAMA"

    def test_consulta_memoria_explicita_sin_ollama(
        self,
    ):
        with patch(
            "brain.core.ask_ollama",
            return_value="OLLAMA",
        ) as mock_ollama:
            think(
                "que tienes en memoria",
                context=ConversationContext(),
            )
        assert mock_ollama.called is False


# ==========================================
# I. SEGUIMIENTO DE MEMORIA EXISTENTE
# ==========================================


class TestMemoryFollowUp:

    def test_y_ayer_tras_memory(self):
        ctx = ConversationContext()
        ctx.set_context(
            MEMORY_SEARCH, mode="memory",
            source_message="que recuerdas",
        )
        resolved = resolve_follow_up("y ayer", ctx)
        assert resolved is not None
        intent, message = resolved
        assert intent == MEMORY_SEARCH
        assert "ayer" in message
        assert _classify(message).intent == (
            MEMORY_SEARCH
        )

    def test_y_hoy_se_resuelve_en_memory_search(
        self,
    ):
        ctx = ConversationContext()
        ctx.set_context(
            MEMORY_SEARCH, mode="memory",
            source_message="que paso",
        )
        resolved = resolve_follow_up("y hoy", ctx)
        assert resolved is not None
        intent, message = resolved
        assert intent == MEMORY_SEARCH
        assert _classify(message).intent == (
            MEMORY_SEARCH
        )


# ==========================================
# J. NUNCA BÚSQUEDA DETERMINISTA EN NO-MEMORY
# ==========================================


class TestNoDeterministicSearch:

    @pytest.mark.parametrize("phrase", [
        "yo hice la tarea",
        "tengo mala memoria",
        "mi mejor recuerdo",
        "lo hicimos bien",
        "como te dije",
        "he hablado con el medico",
        "la transmision en vivo",
        "compre unas memorias usb",
        "hablamos ayer con Juan",
    ])
    def test_no_ejecuta_executor_memoria(self, phrase):
        with patch(
            "brain.core.ask_ollama",
            return_value="OLLAMA",
        ) as mock_ollama:
            response = think(
                phrase,
                context=ConversationContext(),
            )
        if mock_ollama.called:
            assert "No tengo memorias" not in response
            assert "No recuerdo" not in response
        else:
            assert "No tengo memorias" not in response
            assert "No recuerdo" not in response
        assert response != "OLLAMA" or (
            mock_ollama.called is True
        )