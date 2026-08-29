"""
PHASE 8.9F — BARE HISTORICAL QUERY BEHAVIOR (G6)

Las consultas históricas "desnudas" (sin entidad y sin
referencia temporal) — "que paso", "que sucedio",
"que ocurrio", "que hubo" — son intención histórica/
general: deben responder desde el archivo de historia
(history.json), NUNCA buscar memories.json, NUNCA
inventar "No tengo memorias registradas." y NUNCA
depender de OLLAMA. Si no hay contenido, mensaje
determinista de archivo.

Se conservan intactos: consultas con temporal
("que paso ayer", "que paso la semana pasada"),
entidad+temporal ("que paso con kanye ayer", G7),
ARCHIVE temporal (8.9C), clasificación del Intent
Layer (no se toca), single-pass.
"""
import sys

from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "app"),
)

from unittest.mock import patch

from datetime import datetime, timedelta

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent),
)

from _seed_clock import _seed_clock

from brain.core import think
from brain.context import ConversationContext
from brain.intent_layer import IntentLayer
from brain.handlers import extract_search_entity

from brain.intent_types import (
    AMBIGUOUS_INPUT,
    ARCHIVE_SEARCH,
    MEMORY_SEARCH,
)

IL = IntentLayer()

NOW = datetime.now().astimezone()

BARE_VARIANTES = (
    "que paso",
    "qué pasó",
    "que sucedio",
    "qué sucedió",
    "que ocurrio",
    "qué ocurrió",
    "que hubo",
    "¿Qué pasó?",
    "Que Pasó",
    "QUE SUCEDIO",
    "qué ocurrió!",
    "¿Qué hubo?",
)


def _classify(message):
    return IL.classify(message)


def _day_back(days):
    return (
        NOW.date() - timedelta(days=days)
    ).isoformat()


def _mem(mid, date, description):
    return {
        "id": mid,
        "date": date,
        "time": "10:00",
        "description": description,
    }


def _no_memory_search():
    from brain import core as coremod
    calls = {"n": 0}
    orig = coremod.search_deca_memory

    def wrapped(msg, *args, **kwargs):
        calls["n"] += 1
        return orig(msg, *args, **kwargs)

    coremod.search_deca_memory = wrapped
    return calls, orig


# ==========================================
# A. HISTORIA GENERAL DETERMINISTA
# ==========================================


class TestHistoriaGeneral:

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_desnudo_responde_historia(
        self, mock_env, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_env.return_value = {"memories": [
            _mem("r", _day_back(1),
                 "memoria personal real"),
        ]}
        calls, orig = _no_memory_search()
        try:
            ctx = ConversationContext()
            r = think("que paso", context=ctx)
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig
        assert "Inicio de la d" in r
        assert "Nacimiento de DECIA" in r
        assert "memoria personal real" not in r
        assert "No tengo memorias" not in r
        assert "OLLAMA" not in r
        assert mock_oa.call_count == 0
        assert mock_env.call_count == 0
        assert ctx.conversation_mode == "archive"

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_todas_las_variantes_deterministas(
        self, mock_env, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_env.return_value = {"memories": []}
        for ask in BARE_VARIANTES:
            calls, orig = _no_memory_search()
            try:
                ctx = ConversationContext()
                r = think(ask, context=ctx)
            finally:
                import brain.core as coremod
                coremod.search_deca_memory = orig
            assert r, ask
            assert "Inicio de la d" in r, ask
            assert "Nacimiento de DECIA" in r, ask
            assert r != "OLLAMA", ask
            assert "No tengo memorias" not in r, ask
            assert mock_oa.call_count == 0, ask
            assert mock_env.call_count == 0, ask
            assert ctx.conversation_mode == "archive", ask
            assert calls["n"] == 0, ask


# ==========================================
# B. SIN CONTENIDO: AVISO DE ARCHIVO
# ==========================================


class TestSinContenidoHistoria:

    @patch("brain.core.ask_ollama")
    @patch("brain.handlers.get_history")
    def test_sin_eventos_aviso_archivo(
        self, mock_h, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_h.return_value = {"events": []}
        r = think(
            "que paso",
            context=ConversationContext(),
        )
        assert (
            "No encontré información "
            "registrada en el archivo."
            in r
        )
        assert "No tengo memorias" not in r
        assert mock_oa.call_count == 0


# ==========================================
# C. CLASIFICACIÓN INTACTA (NO SE TOCA TIL)
# ==========================================


class TestClasificacionIntacta:

    def test_que_paso_sigue_memory(self):
        r = _classify("que paso")
        assert r.intent == MEMORY_SEARCH
        assert r.confidence == 0.60

    def test_desnudos_siguen_ambiguos(self):
        for ask in (
            "que sucedio",
            "que ocurrio",
            "que hubo",
        ):
            r = _classify(ask)
            assert r.intent == AMBIGUOUS_INPUT, ask


# ==========================================
# D. TEMPORALES INTACTOS (8.9A–8.9E, G7)
# ==========================================


class TestTemporalesIntactos:

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_que_paso_ayer(self, mock_env, mock_oa):
        mock_oa.return_value = "OLLAMA"
        mock_env.return_value = {"memories": [
            _mem("a", _day_back(1),
                 "recorde algo importante ayer"),
        ]}
        calls, orig = _no_memory_search()
        try:
            ctx = ConversationContext()
            r = think("que paso ayer", context=ctx)
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig
        assert "recorde algo importante ayer" in r
        assert "Inicio de la d" not in r
        assert mock_oa.call_count == 0
        assert ctx.conversation_mode == "memory"
        assert calls["n"] == 1

    @patch("brain.core.ask_ollama")
    @_seed_clock
    def test_que_paso_semana_pasada(self, mock_oa):
        mock_oa.return_value = "OLLAMA"
        calls, orig = _no_memory_search()
        try:
            ctx = ConversationContext()
            r = think("que paso la semana pasada",
                      context=ctx)
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig
        assert "No tengo memorias registradas." in r
        assert mock_oa.call_count == 0
        assert ctx.conversation_mode == "memory"
        assert calls["n"] == 1

    @patch("brain.core.ask_ollama")
    @_seed_clock
    def test_que_paso_con_kanye_ayer(self, mock_oa):
        mock_oa.return_value = "OLLAMA"
        calls, orig = _no_memory_search()
        try:
            ctx = ConversationContext()
            r = think(
                "que paso con kanye ayer",
                context=ctx,
            )
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig
        assert r
        assert "Kanye" in r
        assert "kanye ayer" not in r
        assert r != "OLLAMA"
        assert mock_oa.call_count == 0
        assert ctx.conversation_mode == "memory"
        assert calls["n"] == 1

    def test_g7_entidad_limpia(self):
        assert extract_search_entity(
            "que paso con kanye el lunes"
        ) == "kanye"


# ==========================================
# E. ARCHIVE TEMPORAL (8.9C) INTACTO
# ==========================================


class TestArchiveTemporal:

    @patch("brain.core.ask_ollama")
    @_seed_clock
    def test_eventos_semana_pasada_intacto(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        r = think(
            "que eventos de deca hubo la semana pasada",
            context=ConversationContext(),
        )
        assert (
            "No encontré información "
            "registrada en el archivo."
            in r
        )
        assert mock_oa.call_count == 0

    @patch("brain.core.ask_ollama")
    @_seed_clock
    def test_eventos_esta_semana_intacto(self,
                                         mock_oa):
        mock_oa.return_value = "OLLAMA"
        r = think(
            "que eventos de deca hubo esta semana",
            context=ConversationContext(),
        )
        assert "Nacimiento de DECIA" in r
        assert "Inicio de la d" not in r
        assert mock_oa.call_count == 0