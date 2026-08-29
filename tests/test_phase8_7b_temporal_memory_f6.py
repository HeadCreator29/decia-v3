"""
PHASE 8.7B-2 — SEMÁNTICA TEMPORAL F6 (MEMORY SEARCH)

Implementación mínima del hallazgo F6:
  - filtrar la búsqueda de memorias por fecha/rango
    (hoy / ayer / anteayer / hace N dias, semanas o
     meses / el <dia de la semana> / esta semana /
     semana pasada / este mes / mes pasado).
  - des-contaminar la entidad de búsqueda de palabras
    temporales ("sobre kanye la semana pasada").
  - resolver follow-ups temporales en dominio MEMORY
    ("y la semana pasada", "y hace 3 dias", "y el lunes").

Invariantes: sin cruce archive→memory, sin OLLAMA en la
ruta determinista, 1 sola búsqueda por turno, gate de
campo memories intacto, hoy/ayer/anteayer idénticos.
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
from brain.followup import resolve_follow_up
from brain.intent_layer import IntentLayer
from brain.handlers import (
    extract_search_entity,
    filter_memories_by_entity,
)

from brain.intent_types import (
    ARCHIVE_SEARCH,
    MEMORY_SEARCH,
    DATE,
)

from services.archive import search_archive

IL = IntentLayer()


def _classify(message):
    return IL.classify(message)


def _today_date():
    return datetime.now().astimezone().date()


def _iso(day):
    return day.isoformat()


def _week_bounds(week_offset):
    today = _today_date()
    monday = (
        today - timedelta(days=today.weekday())
        + timedelta(weeks=week_offset)
    )
    return (
        monday.isoformat(),
        (monday + timedelta(days=6)).isoformat(),
    )


def _month_bounds(month_offset):
    today = _today_date()
    first = today.replace(day=1)
    sign = 1 if month_offset > 0 else -1
    for _ in range(abs(month_offset)):
        if sign < 0:
            first = (
                first - timedelta(days=1)
            ).replace(day=1)
        else:
            first = (
                first.replace(day=28)
                + timedelta(days=4)
            ).replace(day=1)
    nxt = (
        first.replace(day=28)
        + timedelta(days=4)
    ).replace(day=1)
    return (
        first.isoformat(),
        (nxt - timedelta(days=1)).isoformat(),
    )


def _day_back(days):
    return _iso(
        _today_date() - timedelta(days=days)
    )


def _prev_weekday(target_wd):
    today = _today_date()
    back = (today.weekday() - target_wd) % 7
    if back == 0:
        back = 7
    return _iso(today - timedelta(days=back))


def _mem(id_, date, desc, title="T"):
    return {
        "id": id_,
        "date": date,
        "description": desc,
        "title": title,
    }


def _memory_result(results):
    for r in results:
        if r.get("field") == "memories":
            return r
    return None


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
# A. RANGOS EN search_archive
# ==========================================


class TestRangeSemanaPasada:

    @patch("services.archive.get_memories")
    def test_semana_pasada_solo_rango(self, mock_env):
        start, end = _week_bounds(-1)
        mock_env.return_value = {"memories": [
            _mem(
                "hoy", _day_back(0),
                "terminar decia esta semana",
            ),
            _mem(
                "ini", start,
                "asado familiar la semana pasada",
            ),
            _mem(
                "fin", end,
                "cafe con maria la semana pasada",
            ),
            _mem(
                "mid", _day_back(1),
                "reunion con kanye en el estudio",
            ),
        ]}
        mem = _memory_result(
            search_archive("que hice la semana pasada")
        )
        assert mem is not None
        dates = {
            m["date"] for m in mem["data"]
        }
        assert dates == {start, end}
        assert _day_back(0) not in dates
        assert _day_back(1) not in dates

    @patch("services.archive.get_memories")
    def test_semana_pasada_todo_dentro_rango(
        self, mock_env,
    ):
        start, end = _week_bounds(-1)
        mock_env.return_value = {"memories": [
            _mem("a", start, "solo dentro"),
            _mem("b", end, "dentro tambien"),
            _mem("c", _day_back(0), "fuera"),
        ]}
        mem = _memory_result(
            search_archive("que hice la semana pasada")
        )
        assert mem is not None
        assert all(
            start <= m["date"] <= end
            for m in mem["data"]
        )
        assert _day_back(0) not in {
            m["date"] for m in mem["data"]
        }


class TestRangeEstaSemana:

    @patch("services.archive.get_memories")
    def test_esta_semana_ventana_actual(
        self, mock_env,
    ):
        start, end = _week_bounds(0)
        prev_start, _ = _week_bounds(-1)
        mock_env.return_value = {"memories": [
            _mem(
                "hoy", _day_back(0),
                "terminar decia esta semana",
            ),
            _mem(
                "ayer", _day_back(1),
                "reunion por la tarde",
            ),
            _mem(
                "semanta", prev_start,
                "asado la semana pasada",
            ),
        ]}
        mem = _memory_result(
            search_archive("que hice esta semana")
        )
        assert mem is not None
        dates = {
            m["date"] for m in mem["data"]
        }
        assert _day_back(0) in dates
        assert all(
            start <= d <= end for d in dates
        )
        assert prev_start not in dates


class TestRangeHaceNDias:

    @patch("services.archive.get_memories")
    def test_hace_3_dias_puntual(self, mock_env):
        target = _day_back(3)
        mock_env.return_value = {"memories": [
            _mem(
                "t", target,
                "fueron al cine hace unos dias",
            ),
            _mem(
                "h", _day_back(0),
                "sesion de decia hoy",
            ),
        ]}
        mem = _memory_result(
            search_archive("que hice hace 3 dias")
        )
        assert mem is not None
        dates = {
            m["date"] for m in mem["data"]
        }
        assert dates == {target}

    @patch("services.archive.get_memories")
    def test_hace_7_dias_puntual(self, mock_env):
        target = _day_back(7)
        mock_env.return_value = {"memories": [
            _mem("t", target, "viaje al norte"),
            _mem("h", _day_back(0), "hoy mismo"),
        ]}
        mem = _memory_result(
            search_archive("que hice hace 7 dias")
        )
        assert mem is not None
        dates = {
            m["date"] for m in mem["data"]
        }
        assert dates == {target}


class TestRangeElLunes:

    @patch("services.archive.get_memories")
    def test_el_lunes_recall_dentro_rango(
        self, mock_env,
    ):
        target = _prev_weekday(0)
        mock_env.return_value = {"memories": [
            _mem(
                "lu", target,
                "guardia en el laboratorio",
            ),
            _mem(
                "hk", _day_back(0),
                "reunion kanye hoy",
            ),
        ]}
        mem = _memory_result(
            search_archive("que hice el lunes")
        )
        assert mem is not None
        dates = {
            m["date"] for m in mem["data"]
        }
        assert dates == {target}


class TestRangeMeses:

    @patch("services.archive.get_memories")
    def test_este_mes(self, mock_env):
        start, end = _month_bounds(0)
        prev_last = _iso(
            _today_date().replace(day=1)
            - timedelta(days=1)
        )
        mock_env.return_value = {"memories": [
            _mem(
                "tot", _day_back(0),
                "gasto de este mes",
            ),
            _mem(
                "pm", prev_last,
                "factura del mes pasado",
            ),
            _mem("vd", "2020-01-01", "memoria vieja"),
        ]}
        mem = _memory_result(
            search_archive("que hice este mes")
        )
        assert mem is not None
        dates = {
            m["date"] for m in mem["data"]
        }
        assert _day_back(0) in dates
        assert all(
            start <= d <= end for d in dates
        )
        assert prev_last not in dates

    @patch("services.archive.get_memories")
    def test_mes_pasado(self, mock_env):
        start, end = _month_bounds(-1)
        target = _iso(
            _today_date().replace(day=1)
            - timedelta(days=1)
        )
        mock_env.return_value = {"memories": [
            _mem(
                "pm", target,
                "factura del mes pasado",
            ),
            _mem(
                "tot", _day_back(0),
                "gasto de este mes",
            ),
        ]}
        mem = _memory_result(
            search_archive("que hice el mes pasado")
        )
        assert mem is not None
        dates = {
            m["date"] for m in mem["data"]
        }
        assert target in dates
        assert _day_back(0) not in dates
        assert all(
            start <= d <= end for d in dates
        )


# ==========================================
# B. CLASIFICACIÓN TEMPORAL
# ==========================================


class TestClasificacionTemporal:

    def test_f6_todas_memory_search(self):
        for ask in (
            "que hice la semana pasada",
            "que paso la semana pasada",
            "que hice hace 3 dias",
            "que paso hace 3 dias",
            "que hice el lunes",
            "que paso el lunes",
            "que hice esta semana",
            "que hice el mes pasado",
            "que hice el viernes",
        ):
            r = _classify(ask)
            assert r.intent == MEMORY_SEARCH, ask


# ==========================================
# C. REGRESIÓN SOBRE DATOS REALES
# ==========================================


class TestThinkDatosReales:

    @patch("brain.core.ask_ollama")
    @_seed_clock
    def test_semana_pasada_no_devuelve_hoy(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        r = think(
            "que hice la semana pasada",
            context=ConversationContext(),
        )
        assert (
            "No tengo memorias registradas."
            in r
        )
        assert (
            "terminar decia esta semana"
            not in r
        )
        assert mock_oa.call_count == 0

    @patch("brain.core.ask_ollama")
    @_seed_clock
    def test_esta_semana_determinista(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        r = think(
            "que hice esta semana",
            context=ConversationContext(),
        )
        assert "No tengo memorias registradas." \
            not in r
        assert r != "OLLAMA"
        assert mock_oa.call_count == 0

    @patch("brain.core.ask_ollama")
    @_seed_clock
    def test_hace_3_dias_vacio(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        r = think(
            "que hice hace 3 dias",
            context=ConversationContext(),
        )
        assert "No tengo memorias registradas." in r
        assert mock_oa.call_count == 0

    @patch("brain.core.ask_ollama")
    @_seed_clock
    def test_anteayer_vacio(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        r = think(
            "que hice anteayer",
            context=ConversationContext(),
        )
        assert "No tengo memorias registradas." in r
        assert mock_oa.call_count == 0


# ==========================================
# D. ENTIDAD + FECHA (CONTAMINACIÓN)
# ==========================================


class TestEntidadTemporal:

    @patch("brain.core.ask_ollama")
    @_seed_clock
    def test_sobre_kanye_semana_pasada_no_sirve_ayer(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        r = think(
            "que paso sobre kanye la semana pasada",
            context=ConversationContext(),
        )
        assert "sobre kanye" in r
        assert "kanye la semana pasada" not in r
        assert "me gusta la musica de Kanye" not in r
        assert mock_oa.call_count == 0

    @patch("brain.core.ask_ollama")
    @_seed_clock
    def test_sobre_kanye_sigue_funcionando(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        r = think(
            "que paso sobre kanye",
            context=ConversationContext(),
        )
        assert "Kanye" in r
        assert mock_oa.call_count == 0

    def test_entidad_puramente_temporal_no_filtra(self):
        entity = extract_search_entity(
            "sobre la semana pasada"
        )
        assert entity is None
        result = {
            "field": "memories",
            "data": [
                _mem("a", "2026-08-20", "cualquiera"),
            ],
            "total": 1,
        }
        out = filter_memories_by_entity(
            result, entity,
        )
        assert out is not None
        assert out is result

    def test_entidad_kanye_temporal_filtra_solo_kanye(
        self,
    ):
        kanye = _mem(
            "k", "2026-08-20",
            "me gusta la musica de Kanye",
        )
        semana = _mem(
            "s", "2026-08-20",
            "quiero terminar decia esta semana",
        )
        result = {
            "field": "memories",
            "data": [kanye, semana],
            "total": 2,
        }
        out = filter_memories_by_entity(
            result, "kanye la semana pasada",
        )
        assert out is not None
        assert len(out["data"]) == 1
        assert out["data"][0] is kanye


# ==========================================
# E. FOLLOW-UPS TEMPORALES (MEMORY)
# ==========================================


class TestFollowUpTemporalMemory:

    def test_y_semana_pasada(self):
        r = resolve_follow_up(
            "y la semana pasada", _memory_ctx(),
        )
        assert r == (
            MEMORY_SEARCH,
            "que hice la semana pasada",
        )
        assert _classify(r[1]).intent == MEMORY_SEARCH

    def test_y_hace_3_dias(self):
        r = resolve_follow_up(
            "y hace 3 dias", _memory_ctx(),
        )
        assert r == (
            MEMORY_SEARCH, "que hice hace 3 dias",
        )
        assert _classify(r[1]).intent == MEMORY_SEARCH

    def test_y_el_lunes(self):
        r = resolve_follow_up(
            "y el lunes", _memory_ctx(),
        )
        assert r == (
            MEMORY_SEARCH, "que hice el lunes",
        )
        assert _classify(r[1]).intent == MEMORY_SEARCH

    def test_y_esta_semana(self):
        r = resolve_follow_up(
            "y esta semana", _memory_ctx(),
        )
        assert r == (
            MEMORY_SEARCH, "que hice esta semana",
        )
        assert _classify(r[1]).intent == MEMORY_SEARCH

    def test_y_ayer_igual_que_antes(self):
        r = resolve_follow_up(
            "y ayer", _memory_ctx(),
        )
        assert r == (MEMORY_SEARCH, "que paso ayer")

    @patch("brain.core.ask_ollama")
    @_seed_clock
    def test_followup_semana_pasada_no_hoy(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        ctx = _memory_ctx()
        r = think("y la semana pasada", context=ctx)
        assert "No tengo memorias registradas." in r
        assert "terminar decia esta semana" not in r
        assert mock_oa.call_count == 0
        assert ctx.conversation_mode == "memory"


# ==========================================
# F. INVARIANTES
# ==========================================


class TestInvarianesF6:

    @patch("brain.core.ask_ollama")
    def test_single_pass_una_busqueda(self, mock_oa):
        mock_oa.return_value = "OLLAMA"
        from brain import core as coremod
        calls = {"n": 0}
        orig = coremod.search_deca_memory

        def wrapped(msg, *args, **kwargs):
            calls["n"] += 1
            return orig(msg, *args, **kwargs)

        coremod.search_deca_memory = wrapped
        try:
            think(
                "que hice la semana pasada",
                context=ConversationContext(),
            )
            assert mock_oa.call_count == 0
        finally:
            coremod.search_deca_memory = orig
        assert calls["n"] == 1

    @patch("brain.core.ask_ollama")
    @_seed_clock
    def test_no_cruce_archive(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        ctx = _archive_ctx()
        for ask in (
            "y la semana pasada",
            "y hace 3 dias",
        ):
            r = think(ask, context=ctx)
            assert (
                "No encontré información"
                in r
            )
            assert mock_oa.call_count == 0
            assert (
                ctx.conversation_mode != "memory"
            )

    @patch("brain.core.ask_ollama")
    def test_date_ctx_sin_memoria(self, mock_oa):
        mock_oa.return_value = "OLLAMA"
        ctx = ConversationContext(max_turns=10)
        ctx.set_context(
            intent=DATE,
            mode="time",
            source_message="que dia es",
        )
        r = think("y la semana pasada", context=ctx)
        assert r != ""
        assert ctx.conversation_mode != "memory"
        assert ctx.last_intent != MEMORY_SEARCH
        assert "No tengo memorias" not in r

    @patch("brain.core.ask_ollama")
    def test_gate_field_memories(self, mock_oa):
        mock_oa.return_value = "OLLAMA"
        events_only = [{
            "type": "history",
            "file": "history.json",
            "field": "events",
            "score": 100,
            "data": [{
                "date": "2025-01-01",
                "title": "Hito",
                "description": "evento de prueba",
            }],
        }]
        with patch(
            "brain.handlers.search_archive",
            return_value=events_only,
        ):
            r = think(
                "que hice la semana pasada",
                context=ConversationContext(),
            )
        assert "No tengo memorias registradas." in r
        assert mock_oa.call_count == 0