import sys

from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "app"),
)

from unittest.mock import patch

from brain.core import think
from brain.intent_layer import IntentLayer
from brain.context import ConversationContext
from brain.followup import resolve_follow_up

from brain.intent_types import (
    ARCHIVE_SEARCH,
    MEMORY_SEARCH,
    MEMORY_CREATE,
    DATE,
    TIME,
    FREE_TALK,
)


il = IntentLayer()


def classify(text):
    return il.classify(text)


def new_context():
    return ConversationContext(max_turns=10)


# ==========================================
# 1. EXPANSIÓN DE BÚSQUEDA DE MEMORIA
# ==========================================


class TestMemorySearchExpansion:

    def test_que_recuerda_de_ayer(self):
        r = classify("que recuerda de ayer")
        assert r.intent == MEMORY_SEARCH

    def test_que_recuerdas_sobre_kanye(self):
        r = classify("que recuerdas sobre kanye")
        assert r.intent == MEMORY_SEARCH

    def test_te_acuerdas_de_ayer(self):
        r = classify("te acuerdas de ayer")
        assert r.intent == MEMORY_SEARCH
        assert r.confidence >= 0.70

    def test_recuerdas_lo_de_ayer(self):
        r = classify("recuerdas lo de ayer")
        assert r.intent == MEMORY_SEARCH

    def test_recuerda_lo_de_ayer(self):
        r = classify("recuerda lo de ayer")
        assert r.intent == MEMORY_SEARCH

    def test_recuerda_comprar_pan_no_memory(self):
        """'recuerda' + infinitivo NO es búsqueda."""
        r = classify("recuerda comprar pan")
        assert r.intent != MEMORY_SEARCH
        assert r.intent != MEMORY_CREATE

    def test_recuerda_llamar_manana_no_memory(self):
        r = classify("recuerda llamar manana")
        assert r.intent != MEMORY_SEARCH
        assert r.intent != MEMORY_CREATE

    def test_recuerda_que_sigue_create(self):
        r = classify("recuerda que tengo clase")
        assert r.intent == MEMORY_CREATE


# ==========================================
# 2. ARCHIVE_SEARCH LLEGA A SU RUTA (5.1/5.5)
# ==========================================


class TestArchiveSearchExecution:

    @patch("brain.core.ask_ollama")
    def test_que_hay_registrado_no_ollama(
        self, mock_oa,
    ):
        """ARCHIVE_SEARCH detectada DEBE ejecutarse,
        nunca caer a OLLAMA."""
        mock_oa.return_value = "OLLAMA_NO_DEBE"

        ctx = new_context()

        r = think(
            "que hay registrado sobre deca",
            context=ctx,
        )

        assert r != "OLLAMA_NO_DEBE"
        assert r
        mock_oa.assert_not_called()

    @patch("brain.core.ask_ollama")
    def test_no_result_no_ollama(self, mock_oa):
        """Sin resultados → respuesta determinista,
        NUNCA OLLAMA."""
        mock_oa.return_value = "OLLAMA_NO_DEBE"

        ctx = new_context()

        r = think(
            "que hay registrado sobre zzz",
            context=ctx,
        )

        assert r == (
            "No encontré información "
            "registrada sobre zzz."
        )

        mock_oa.assert_not_called()

    @patch("brain.core.ask_ollama")
    def test_que_recuerdas_routes_to_memory(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA_NO_DEBE"

        r = think("que recuerdas")

        assert r != "OLLAMA_NO_DEBE"
        assert r
        mock_oa.assert_not_called()

    @patch("brain.core.ask_ollama")
    def test_memory_sobre_entidad_filtra(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA_NO_DEBE"

        ctx = new_context()

        r = think(
            "que recuerdas sobre kanye",
            context=ctx,
        )

        assert "OLLAMA_NO_DEBE" not in r
        assert "kanye" in r.lower()
        mock_oa.assert_not_called()


# ==========================================
# 3. SEGUIMIENTO CONVERSACIONAL (5.4)
# ==========================================


class TestFollowUpResolution:

    def test_y_sobre_after_archive(self):
        ctx = new_context()
        ctx.set_context(
            ARCHIVE_SEARCH, mode="archive",
            source_message="que hay registrado",
        )
        resolved = resolve_follow_up(
            "y sobre herrera", ctx,
        )
        assert resolved is not None
        intent, message = resolved
        assert intent == ARCHIVE_SEARCH
        assert "herrera" in message

    def test_y_que_dia_after_time(self):
        ctx = new_context()
        ctx.set_context(
            TIME, mode="time",
            source_message="que hora es",
        )
        resolved = resolve_follow_up(
            "y que dia", ctx,
        )
        assert resolved is not None
        intent, message = resolved
        assert intent == DATE
        assert "dia" in message

    def test_no_follow_up_sin_contexto(self):
        ctx = new_context()
        resolved = resolve_follow_up(
            "y que dia", ctx,
        )
        assert resolved is None

    def test_no_follow_up_sin_modo(self):
        ctx = new_context()
        ctx.set_context(
            "GREETING", mode=None,
            source_message="hola",
        )
        resolved = resolve_follow_up(
            "y que dia", ctx,
        )
        assert resolved is None

    def test_y_ayer_after_memory(self):
        ctx = new_context()
        ctx.set_context(
            MEMORY_SEARCH, mode="memory",
            source_message="que recuerdas",
        )
        resolved = resolve_follow_up(
            "y ayer", ctx,
        )
        assert resolved is not None
        intent, message = resolved
        assert intent == MEMORY_SEARCH
        assert "ayer" in message

    @patch("brain.core.ask_ollama")
    def test_hola_luego_y_que_dia_no_inventa(
        self, mock_oa,
    ):
        """Sin contexto relevante, el seguimiento
        NO debe resolverse (contaminación)."""
        mock_oa.return_value = "OLLAMA"

        ctx = new_context()

        think("hola", context=ctx)

        r = think("y que dia", context=ctx)

        assert r == "OLLAMA"
        mock_oa.assert_called_once()

    @patch("brain.core.ask_ollama")
    def test_hora_luego_y_que_dia(self, mock_oa):
        mock_oa.return_value = "OLLAMA"

        ctx = new_context()

        think("que hora es", context=ctx)

        r = think("y que dia", context=ctx)

        assert r != "OLLAMA"
        assert "Hoy es" in r
        mock_oa.assert_not_called()


# ==========================================
# 4. CONTEXTO CORTO (5.3)
# ==========================================


class TestContextFields:

    @patch("brain.core.ask_ollama")
    def test_contexto_se_registra(self, mock_oa):
        ctx = new_context()

        think(
            "que hay registrado sobre deca",
            context=ctx,
        )

        mock_oa.assert_not_called()

        assert ctx.conversation_mode == "archive"
        assert ctx.last_intent == ARCHIVE_SEARCH
        assert ctx.last_entity == "deca"
        assert ctx.previous_user_input == (
            "que hay registrado sobre deca"
        )

    @patch("brain.core.ask_ollama")
    def test_greeting_invalida_contexto(
        self, mock_oa,
    ):
        ctx = new_context()
        ctx.set_context(
            ARCHIVE_SEARCH, mode="archive",
            source_message="que hay registrado",
        )

        think("hola", context=ctx)

        assert ctx.conversation_mode is None
        assert ctx.last_intent is None

    @patch("brain.core.ask_ollama")
    def test_exit_invalida_contexto(self, mock_oa):
        ctx = new_context()
        ctx.set_context(
            ARCHIVE_SEARCH, mode="archive",
            source_message="que hay registrado",
        )

        r = think("salir", context=ctx)

        assert r == "Hasta luego."
        assert ctx.conversation_mode is None
        assert ctx.last_intent is None

    @patch("brain.core.ask_ollama")
    def test_free_talk_invalida_contexto(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"

        ctx = new_context()
        ctx.set_context(
            MEMORY_SEARCH, mode="memory",
            source_message="que recuerdas",
        )

        think("cuentame un chiste", context=ctx)

        assert ctx.conversation_mode is None
        assert ctx.last_intent is None