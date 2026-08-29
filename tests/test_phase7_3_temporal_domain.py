"""
PHASE 7.3 — TEMPORAL FOLLOW-UP DOMAIN FIX
"""
import sys

from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "app"),
)

from unittest.mock import patch

from brain.core import think
from brain.context import ConversationContext
from brain.followup import resolve_follow_up

from brain.intent_types import (
    ARCHIVE_SEARCH,
    MEMORY_SEARCH,
    DATE,
    TIME,
)


def new_context():
    return ConversationContext(max_turns=10)


def _archive_ctx():
    ctx = new_context()
    ctx.set_context(
        intent=ARCHIVE_SEARCH,
        mode="archive",
        entity="deca",
        source_message="que hay registrado sobre deca",
    )
    return ctx


def _memory_ctx():
    ctx = new_context()
    ctx.set_context(
        intent=MEMORY_SEARCH,
        mode="memory",
        entity="kanye",
        source_message="que recuerdas sobre kanye",
    )
    return ctx


def _time_ctx(intent):
    ctx = new_context()
    ctx.set_context(
        intent=intent,
        mode="time",
        source_message="que hora es",
    )
    return ctx


class TestResolveTemporalDomain:

    def test_archive_y_ayer_no_resuelve_a_memory(self):
        assert resolve_follow_up(
            "y ayer", _archive_ctx(),
        ) is None

    def test_archive_y_hoy_no_resuelve_a_memory(self):
        assert resolve_follow_up(
            "y hoy", _archive_ctx(),
        ) is None

    def test_memory_y_ayer_sigue_resolviendo(self):
        r = resolve_follow_up(
            "y ayer", _memory_ctx(),
        )
        assert r == (
            MEMORY_SEARCH, "que paso ayer",
        )

    def test_memory_y_hoy_sigue_resolviendo(self):
        r = resolve_follow_up(
            "y hoy", _memory_ctx(),
        )
        assert r == (
            MEMORY_SEARCH, "que paso hoy",
        )

    def test_time_y_ayer_sigue_sin_resolver(self):
        assert resolve_follow_up(
            "y ayer", _time_ctx(TIME),
        ) is None

    def test_date_y_hoy_sigue_sin_resolver(self):
        assert resolve_follow_up(
            "y hoy", _time_ctx(DATE),
        ) is None

    def test_frio_y_ayer_no_resuelve(self):
        assert resolve_follow_up(
            "y ayer", new_context(),
        ) is None

    def test_frio_y_hoy_no_resuelve(self):
        assert resolve_follow_up(
            "y hoy", new_context(),
        ) is None

    def test_time_y_la_hora_regresion(self):
        r = resolve_follow_up(
            "y la hora", _time_ctx(DATE),
        )
        assert r == (TIME, "que hora es")

    def test_time_y_que_hora_regresion(self):
        r = resolve_follow_up(
            "y que hora", _time_ctx(DATE),
        )
        assert r == (TIME, "que hora es")

    def test_date_y_el_dia_regresion(self):
        r = resolve_follow_up(
            "y el dia", _time_ctx(TIME),
        )
        assert r == (DATE, "que dia es hoy")

    def test_date_y_la_fecha_regresion(self):
        r = resolve_follow_up(
            "y la fecha", _time_ctx(TIME),
        )
        assert r == (DATE, "que dia es hoy")

    def test_date_y_que_dia_regresion(self):
        r = resolve_follow_up(
            "y que dia", _time_ctx(TIME),
        )
        assert r == (DATE, "que dia es hoy")


class TestThinkTemporalDomain:

    @patch("brain.core.ask_ollama")
    def test_archive_deca_y_ayer_no_cambia_a_memory(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        ctx = _archive_ctx()
        r = think("y ayer", context=ctx)
        assert "No tengo memorias" not in r
        assert ctx.conversation_mode != "memory"
        assert ctx.last_intent == ARCHIVE_SEARCH

    @patch("brain.core.ask_ollama")
    def test_archive_deca_y_hoy_no_cambia_a_memory(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        ctx = _archive_ctx()
        r = think("y hoy", context=ctx)
        assert "No tengo memorias" not in r
        assert ctx.conversation_mode != "memory"

    @patch("brain.core.ask_ollama")
    def test_archive_despues_turno_completo_en_dominio(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        ctx = new_context()
        think("que hay registrado sobre deca",
              context=ctx)
        assert ctx.conversation_mode == "archive"
        assert ctx.last_entity == "deca"
        r = think("y ayer", context=ctx)
        assert "No tengo memorias" not in r
        assert ctx.conversation_mode != "memory"

    @patch("brain.core.ask_ollama")
    def test_memory_y_ayer_sigue_resolviendo(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        from brain import core as coremod
        ctx = new_context()
        think("que recuerdas sobre kanye",
              context=ctx)
        assert ctx.conversation_mode == "memory"

        orig = coremod.search_deca_memory

        def fake(msg, prefer_field=None):
            if "ayer" in msg:
                return {
                    "type": "memory",
                    "file": "memories.json",
                    "field": "memories",
                    "score": 100,
                    "data": [{
                        "date": "ayer",
                        "title": "Temporal",
                        "description":
                            "lo que paso ayer "
                            "quedo en memoria",
                    }],
                    "total": 1,
                }
            return orig(
                msg, prefer_field=prefer_field,
            )

        coremod.search_deca_memory = fake
        try:
            r = think("y ayer", context=ctx)
        finally:
            coremod.search_deca_memory = orig
        assert "lo que paso ayer quedo en memoria" in r
        assert ctx.conversation_mode == "memory"
        assert ctx.last_intent == MEMORY_SEARCH
        assert mock_oa.call_count == 0

    @patch("brain.core.ask_ollama")
    def test_frio_y_ayer_no_inventa_contexto(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        ctx = new_context()
        r = think("y ayer", context=ctx)
        assert "¿Sí?" in r or "Qué necesitas" in r
        assert mock_oa.call_count == 0
        assert ctx.last_intent is None

    @patch("brain.core.ask_ollama")
    def test_frio_y_hoy_no_inventa_contexto(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        ctx = new_context()
        r = think("y hoy", context=ctx)
        assert "¿Sí?" in r or "Qué necesitas" in r
        assert mock_oa.call_count == 0
        assert ctx.last_intent is None

    @patch("brain.core.ask_ollama")
    def test_frio_y_ayer_que_paso_clasifica_memory(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        ctx = new_context()
        r = think("y ayer que paso", context=ctx)
        assert mock_oa.call_count == 0
        assert ctx.last_intent == MEMORY_SEARCH

    @patch("brain.core.ask_ollama")
    def test_y_hoy_que_fecha_era_clasifica_date(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        ctx = new_context()
        r = think("y hoy que fecha era", context=ctx)
        assert mock_oa.call_count == 0
        assert ctx.last_intent == DATE

    @patch("brain.core.ask_ollama")
    def test_single_pass_temporal_memory(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        from brain import core as coremod
        ctx = new_context()
        calls = {"n": 0}
        orig = coremod.search_deca_memory

        def wrapped(msg, *args, **kwargs):
            calls["n"] += 1
            return orig(
                msg, *args, **kwargs
            )

        coremod.search_deca_memory = wrapped
        try:
            think("que recuerdas sobre kanye",
                  context=ctx)
            think("y ayer", context=ctx)
        finally:
            coremod.search_deca_memory = orig
        assert calls["n"] == 2

    @patch("brain.core.ask_ollama")
    def test_single_pass_archive_temporal_no_search(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        from brain import core as coremod
        ctx = _archive_ctx()
        calls = {"n": 0}
        orig = coremod.search_deca_memory

        def wrapped(msg, *args, **kwargs):
            calls["n"] += 1
            return orig(
                msg, *args, **kwargs
            )

        coremod.search_deca_memory = wrapped
        try:
            think("y ayer", context=ctx)
        finally:
            coremod.search_deca_memory = orig
        assert calls["n"] == 0

    @patch("brain.core.ask_ollama")
    def test_free_talk_ollama_no_arrastra_temporal(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        ctx = new_context()
        think("que opinas de la vida", context=ctx)
        assert ctx.last_intent is None
        r = think("y ayer", context=ctx)
        assert "¿Sí?" in r or "Qué necesitas" in r
        assert ctx.last_intent is None