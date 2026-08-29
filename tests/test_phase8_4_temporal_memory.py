"""
PHASE 8.4 — MEMORIA TEMPORAL CONTROLADA

Resolución determinista de consultas temporales
("que paso hoy/ayer/anteayer") usando exclusivamente
memorias del día solicitado.

Aditivo: no altera recall de consultas NO temporales.
"""
import sys

from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "app"),
)

from unittest.mock import patch

from datetime import datetime, timedelta

from brain.core import think
from brain.context import ConversationContext
from brain.followup import resolve_follow_up
from brain.intent_layer import IntentLayer
from brain.handlers import search_deca_memory

from brain.intent_types import (
    ARCHIVE_SEARCH,
    MEMORY_SEARCH,
    DATE,
    TIME,
)

from services.archive import search_archive, normalize

IL = IntentLayer()


def _classify(message):
    return IL.classify(message)


def _temporal_dates():
    now = datetime.now().astimezone()
    today = now.strftime("%Y-%m-%d")
    yesterday = (
        now - timedelta(days=1)
    ).strftime("%Y-%m-%d")
    anteayer = (
        now - timedelta(days=2)
    ).strftime("%Y-%m-%d")
    return today, yesterday, anteayer


def _fake_memories():
    today, yesterday, anteayer = _temporal_dates()
    return {"memories": [
        {
            "id": "hoy",
            "date": today,
            "description":
                "macarrones con la abuela",
            "title": "Comida",
        },
        {
            "id": "ayer",
            "date": yesterday,
            "description":
                "reunion con kanye en el estudio",
            "title": "Studio",
        },
        {
            "id": "anteayer",
            "date": anteayer,
            "description": "paseo por el parque",
            "title": "Paseo",
        },
        {
            "id": "vieja",
            "date": "2020-01-01",
            "description":
                "memoria antigua sobre kanye",
            "title": "Vieja",
        },
    ]}


def _memory_result(results):
    for r in results:
        if r.get("field") == "memories":
            return r
    return None


def _events_result(score=100):
    return {
        "type": "history",
        "file": "history.json",
        "field": "events",
        "score": score,
        "data": [{
            "date": "2025-08-29",
            "title": "Hito",
            "description": "evento de prueba",
        }],
    }


def _memory_ctx():
    ctx = ConversationContext(max_turns=10)
    ctx.set_context(
        intent=MEMORY_SEARCH,
        mode="memory",
        entity="kanye",
        source_message="que recuerdas sobre kanye",
    )
    return ctx


def _archive_ctx():
    ctx = ConversationContext(max_turns=10)
    ctx.set_context(
        intent=ARCHIVE_SEARCH,
        mode="archive",
        entity="deca",
        source_message=
            "que hay registrado sobre deca",
    )
    return ctx


# ==========================================
# A. FILTRO TEMPORAL POR FECHA EN search_archive
# ==========================================


class TestSearchArchiveTemporal:

    @patch("services.archive.get_memories")
    def test_hoy_solo_date_hoy(self, mock_env):
        mock_env.return_value = _fake_memories()
        today, _, _ = _temporal_dates()
        mem = _memory_result(
            search_archive("que paso hoy")
        )
        assert mem is not None
        data = mem["data"]
        assert len(data) == 1
        assert data[0]["id"] == "hoy"
        assert data[0]["date"] == today

    @patch("services.archive.get_memories")
    def test_ayer_solo_date_ayer(self, mock_env):
        mock_env.return_value = _fake_memories()
        _, yesterday, _ = _temporal_dates()
        mem = _memory_result(
            search_archive("que paso ayer")
        )
        assert mem is not None
        data = mem["data"]
        assert len(data) == 1
        assert data[0]["id"] == "ayer"
        assert data[0]["date"] == yesterday

    @patch("services.archive.get_memories")
    def test_anteayer_solo_date_anteayer(
        self, mock_env,
    ):
        mock_env.return_value = _fake_memories()
        _, _, anteayer = _temporal_dates()
        mem = _memory_result(
            search_archive("que paso anteayer")
        )
        assert mem is not None
        data = mem["data"]
        assert len(data) == 1
        assert data[0]["id"] == "anteayer"
        assert data[0]["date"] == anteayer

    @patch("services.archive.get_memories")
    def test_anteayer_no_cae_en_rama_ayer(
        self, mock_env,
    ):
        mock_env.return_value = _fake_memories()
        _, yesterday, anteayer = _temporal_dates()
        mem = _memory_result(
            search_archive("que paso anteayer")
        )
        assert mem is not None
        dates = {
            m["date"] for m in mem["data"]
        }
        assert dates == {anteayer}
        assert yesterday not in dates
        assert {"ayer", "hoy", "vieja"} & {
            m["id"] for m in mem["data"]
        } == set()

    def test_anteayer_real_no_devuelve_ayer(
        self,
    ):
        _, yesterday, anteayer = _temporal_dates()
        mem = _memory_result(
            search_archive("que paso anteayer")
        )
        assert mem is None or all(
            m.get("date", "") != yesterday
            for m in mem["data"]
        )
        assert mem is None or all(
            m.get("date", "") == anteayer
            for m in mem["data"]
        )

    @patch("services.archive.get_memories")
    def test_recall_temporal_sin_keyword_match(
        self, mock_env,
    ):
        mock_env.return_value = _fake_memories()
        today, _, _ = _temporal_dates()
        mem = _memory_result(
            search_archive("que paso hoy")
        )
        assert mem is not None
        data = mem["data"]
        assert len(data) == 1
        assert data[0]["description"] == (
            "macarrones con la abuela"
        )

    @patch("services.archive.get_memories")
    def test_fuera_de_temporal_recall_sin_cambios(
        self, mock_env,
    ):
        mock_env.return_value = _fake_memories()
        mem = _memory_result(
            search_archive("que recuerdas sobre kanye")
        )
        assert mem is not None
        ids = {
            m["id"] for m in mem["data"]
        }
        assert {"ayer", "vieja"} <= ids
        assert "hoy" not in ids


# ==========================================
# B. DEDUPLICACIÓN Y LÍMITE
# ==========================================


class TestSearchArchiveDedupeLimit:

    @patch("services.archive.get_memories")
    def test_dedupe_y_limite_20(self, mock_env):
        today, _, _ = _temporal_dates()
        entries = []
        for i in range(30):
            desc = (
                f"tarea numero {i}"
                if i < 20
                else "duplicada"
            )
            entries.append({
                "id": str(i),
                "date": today,
                "description": desc,
                "title": "T",
            })
        mock_env.return_value = {"memories": entries}
        mem = _memory_result(
            search_archive("que paso hoy")
        )
        assert mem is not None
        data = mem["data"]
        assert len(data) <= 20
        keys = {
            (m["date"], normalize(m["description"]))
            for m in data
        }
        assert len(keys) == len(data)
        assert mem.get("total") == 21


# ==========================================
# C. prefer_field en search_deca_memory
# ==========================================


class TestSearchDecaMemoryPrefer:

    def test_prefer_memories_prioriza(self):
        memories = {
            "type": "memory",
            "file": "memories.json",
            "field": "memories",
            "score": 90,
            "data": [{
                "date": "2026-08-26",
                "title": "M",
                "description": "memoria real",
            }],
            "total": 1,
        }
        with patch(
            "brain.handlers.search_archive",
            return_value=[
                _events_result(score=100),
                memories,
            ],
        ):
            r = search_deca_memory(
                "que paso ayer",
                prefer_field="memories",
            )
        assert r is not None
        assert r["field"] == "memories"

    def test_sin_prefer_mantiene_comportamiento(
        self,
    ):
        memories = {
            "type": "memory",
            "file": "memories.json",
            "field": "memories",
            "score": 90,
            "data": [],
            "total": 0,
        }
        with patch(
            "brain.handlers.search_archive",
            return_value=[
                _events_result(score=100),
                memories,
            ],
        ):
            r = search_deca_memory(
                "que paso ayer"
            )
        assert r is not None
        assert r["field"] == "events"

    def test_prefer_sin_memories_cae_al_primero(
        self,
    ):
        with patch(
            "brain.handlers.search_archive",
            return_value=[_events_result(score=100)],
        ):
            r = search_deca_memory(
                "que paso ayer",
                prefer_field="memories",
            )
        assert r is not None
        assert r["field"] == "events"


# ==========================================
# D. RUTA DE EJECUCIÓN EN core (think)
# ==========================================


class TestThinkTemporal:

    def test_cadena_ayer_busca_y_entrega_memory(
        self,
    ):
        _, yesterday, _ = _temporal_dates()
        memories = {
            "type": "memory",
            "file": "memories.json",
            "field": "memories",
            "score": 100,
            "data": [{
                "date": yesterday,
                "title": "t",
                "description":
                    "sesion con maria ayer",
            }],
            "total": 1,
        }
        with patch(
            "brain.handlers.search_archive",
            return_value=[
                _events_result(score=100),
                memories,
            ],
        ):
            with patch(
                "brain.core.ask_ollama",
                return_value="OLLAMA",
            ) as mock_oa:
                ctx = ConversationContext()
                r = think("que paso ayer", context=ctx)
        assert "sesion con maria ayer" in r
        assert ctx.conversation_mode == "memory"
        assert ctx.last_intent == MEMORY_SEARCH
        assert mock_oa.call_count == 0

    def test_prefer_field_solo_en_memory(
        self,
    ):
        from brain import core as coremod
        recorded = []

        def fake(msg, prefer_field=None):
            recorded.append(prefer_field)
            return _events_result(score=100)

        orig = coremod.search_deca_memory
        coremod.search_deca_memory = fake
        try:
            with patch(
                "brain.core.ask_ollama",
                return_value="OLLAMA",
            ) as mock_oa:
                think(
                    "cual es la historia de deca",
                    context=ConversationContext(),
                )
                think(
                    "que paso ayer",
                    context=ConversationContext(),
                )
                assert mock_oa.call_count == 0
        finally:
            coremod.search_deca_memory = orig
        assert recorded == [None, "memories"]

    def test_single_pass_temporal_una_busqueda(
        self,
    ):
        from brain import core as coremod
        calls = {"n": 0}
        orig = coremod.search_deca_memory

        def wrapped(msg, *args, **kwargs):
            calls["n"] += 1
            return orig(msg, *args, **kwargs)

        coremod.search_deca_memory = wrapped
        try:
            with patch(
                "brain.core.ask_ollama",
                return_value="OLLAMA",
            ) as mock_oa:
                think(
                    "que paso ayer",
                    context=ConversationContext(),
                )
                assert mock_oa.call_count == 0
        finally:
            coremod.search_deca_memory = orig
        assert calls["n"] == 1

    def test_gate_field_memories_se_mantiene(
        self,
    ):
        with patch(
            "brain.handlers.search_archive",
            return_value=[_events_result(score=100)],
        ):
            with patch(
                "brain.core.ask_ollama",
                return_value="OLLAMA",
            ) as mock_oa:
                r = think(
                    "que paso ayer",
                    context=ConversationContext(),
                )
        assert "No tengo memorias registradas." in r
        assert mock_oa.call_count == 0


# ==========================================
# E. FOLLOW-UPS MEMORY ("y hoy / ayer /
#    anteayer")
# ==========================================


class TestFollowUpsMemory:

    def test_y_ayer(self):
        r = resolve_follow_up("y ayer", _memory_ctx())
        assert r == (MEMORY_SEARCH, "que paso ayer")
        assert _classify(r[1]).intent == MEMORY_SEARCH

    def test_y_hoy(self):
        r = resolve_follow_up("y hoy", _memory_ctx())
        assert r == (MEMORY_SEARCH, "que paso hoy")
        assert _classify(r[1]).intent == MEMORY_SEARCH

    def test_y_anteayer(self):
        r = resolve_follow_up(
            "y anteayer", _memory_ctx(),
        )
        assert r == (
            MEMORY_SEARCH, "que paso anteayer",
        )
        assert _classify(r[1]).intent == MEMORY_SEARCH


# ==========================================
# F. SIN CRUCE ARCHIVE → MEMORY
# ==========================================


class TestArchiveNoCross:

    @patch("brain.core.ask_ollama")
    def test_y_ayer(self, mock_oa):
        mock_oa.return_value = "OLLAMA"
        ctx = _archive_ctx()
        r = think("y ayer", context=ctx)
        assert "¿Sí?" in r or "Qué necesitas" in r
        assert ctx.conversation_mode != "memory"
        assert mock_oa.call_count == 0

    @patch("brain.core.ask_ollama")
    def test_y_hoy(self, mock_oa):
        mock_oa.return_value = "OLLAMA"
        ctx = _archive_ctx()
        r = think("y hoy", context=ctx)
        assert "¿Sí?" in r or "Qué necesitas" in r
        assert ctx.conversation_mode != "memory"
        assert mock_oa.call_count == 0

    @patch("brain.core.ask_ollama")
    def test_y_anteayer(self, mock_oa):
        mock_oa.return_value = "OLLAMA"
        ctx = _archive_ctx()
        r = think("y anteayer", context=ctx)
        assert "¿Sí?" in r or "Qué necesitas" in r
        assert ctx.conversation_mode != "memory"
        assert mock_oa.call_count == 0


# ==========================================
# G. FRÍO: TEMPORAL NO HEREDA CONTEXTO
# ==========================================


class TestFrioTemporal:

    @patch("brain.core.ask_ollama")
    def test_y_ayer(self, mock_oa):
        mock_oa.return_value = "OLLAMA"
        ctx = ConversationContext()
        r = think("y ayer", context=ctx)
        assert "¿Sí?" in r or "Qué necesitas" in r
        assert mock_oa.call_count == 0
        assert ctx.last_intent is None

    @patch("brain.core.ask_ollama")
    def test_y_hoy(self, mock_oa):
        mock_oa.return_value = "OLLAMA"
        ctx = ConversationContext()
        r = think("y hoy", context=ctx)
        assert "¿Sí?" in r or "Qué necesitas" in r
        assert mock_oa.call_count == 0
        assert ctx.last_intent is None

    @patch("brain.core.ask_ollama")
    def test_y_anteayer(self, mock_oa):
        mock_oa.return_value = "OLLAMA"
        ctx = ConversationContext()
        r = think("y anteayer", context=ctx)
        assert "¿Sí?" in r or "Qué necesitas" in r
        assert mock_oa.call_count == 0
        assert ctx.last_intent is None


# ==========================================
# H. DATE / TIME SIN SEMÁNTICA NUEVA
# ==========================================


class TestDateTimeSinSemanticaNueva:

    @patch("brain.core.ask_ollama")
    def test_date_y_ayer(self, mock_oa):
        mock_oa.return_value = "OLLAMA"
        ctx = ConversationContext(max_turns=10)
        ctx.set_context(
            intent=DATE,
            mode="time",
            source_message="que dia es",
        )
        r = think("y ayer", context=ctx)
        assert "¿Sí?" in r or "Qué necesitas" in r
        assert mock_oa.call_count == 0
        assert ctx.last_intent is None

    @patch("brain.core.ask_ollama")
    def test_time_y_anteayer(self, mock_oa):
        mock_oa.return_value = "OLLAMA"
        ctx = ConversationContext(max_turns=10)
        ctx.set_context(
            intent=TIME,
            mode="time",
            source_message="que hora es",
        )
        r = think("y anteayer", context=ctx)
        assert "¿Sí?" in r or "Qué necesitas" in r
        assert mock_oa.call_count == 0
        assert ctx.last_intent is None


# ==========================================
# I. ENTIDAD + FECHA (REPRODUCCIÓN, SIN
#    SEMÁNTICA NUEVA)
# ==========================================


class TestEntityFecha:

    def test_intent_memory(self):
        for ask in (
            "que paso con kanye ayer",
            "que paso sobre kanye ayer",
        ):
            r = _classify(ask)
            assert r.intent == MEMORY_SEARCH, ask

    @patch("brain.core.ask_ollama")
    def test_determinista_sin_ollama(self, mock_oa):
        mock_oa.return_value = "OLLAMA"
        for ask in (
            "que paso con kanye ayer",
            "que paso sobre kanye ayer",
        ):
            ctx = ConversationContext()
            r = think(ask, context=ctx)
            assert mock_oa.call_count == 0
            assert r
            assert r != "OLLAMA"
            assert ctx.conversation_mode == "memory"