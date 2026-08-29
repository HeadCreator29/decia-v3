"""
PHASE 8.9A — TEMPORAL HISTORY/MEMORY BRIDGE (G1 + G5 + G2)

G1: las consultas "que paso + temporal" (ayer / anteayer /
    hace N dias, semanas o meses / el <dia> / esta semana /
    semana pasada / este mes / mes pasado) entran a la rama
    MEMORIAS de search_archive y respetan exactamente el
    filtro temporal existente (mismas ventanas y límites).
G5: extracción de entidad con "con X" (además de "sobre X"),
    con entidad real limpia (des-contaminación temporal) y
    aplicación conjunta entidad + rango temporal.
G2: "hace un dia / una semana / un mes" ≡ "hace 1 ...".

Invariantes: 1 sola búsqueda por turno, gate field=="memories",
límites/dedupe actuales, thresholds/confidence, TIL, OLLAMA y
modelo intactos; sin cambios sobre ARCHIVE_EVENTS (G4), G6 ni
G7; sin semántica nueva fuera de los tres puntos.
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
    MEMORY_SEARCH,
)

from services.archive import search_archive

from utils.date_parser import (
    parse_relative_date,
)

IL = IntentLayer()

NOW = datetime.now().astimezone()


def _classify(message):
    return IL.classify(message)


def _today_date():
    return NOW.date()


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


# ==========================================
# G1. "QUE PASO + TEMPORAL" EN MEMORIAS
# ==========================================


class TestG1SearchArchive:

    @patch("services.archive.get_memories")
    def test_paso_hace_3_dias(self, mock_env):
        target = _day_back(3)
        mock_env.return_value = {"memories": [
            _mem(
                "t", target,
                "fueron al cine ese dia",
            ),
            _mem(
                "h", _day_back(0),
                "terminar decia esta semana",
            ),
            _mem(
                "a", _day_back(1),
                "cafe por la tarde",
            ),
        ]}
        mem = _memory_result(
            search_archive("que paso hace 3 dias")
        )
        assert mem is not None
        dates = {
            m["date"] for m in mem["data"]
        }
        assert dates == {target}

    @patch("services.archive.get_memories")
    def test_paso_esta_semana(self, mock_env):
        start, end = _week_bounds(0)
        prev_start, _ = _week_bounds(-1)
        mock_env.return_value = {"memories": [
            _mem(
                "hoy", _day_back(0),
                "terminar decia esta semana",
            ),
            _mem(
                "ayer", _day_back(1),
                "reunion esta semana",
            ),
            _mem(
                "prev", prev_start,
                "asado la semana pasada",
            ),
        ]}
        mem = _memory_result(
            search_archive("que paso esta semana")
        )
        assert mem is not None
        dates = {
            m["date"] for m in mem["data"]
        }
        assert _day_back(0) in dates
        assert _day_back(1) in dates
        assert all(
            start <= d <= end for d in dates
        )
        assert prev_start not in dates

    @patch("services.archive.get_memories")
    def test_paso_semana_pasada(self, mock_env):
        start, end = _week_bounds(-1)
        mock_env.return_value = {"memories": [
            _mem(
                "ini", start,
                "asado familiar la semana pasada",
            ),
            _mem(
                "fin", end,
                "cafe con maria la semana pasada",
            ),
            _mem(
                "hoy", _day_back(0),
                "terminar decia esta semana",
            ),
            _mem(
                "ayer", _day_back(1),
                "reunion con kanye en el estudio",
            ),
        ]}
        mem = _memory_result(
            search_archive("que paso la semana pasada")
        )
        assert mem is not None
        dates = {
            m["date"] for m in mem["data"]
        }
        assert dates == {start, end}
        assert _day_back(0) not in dates
        assert _day_back(1) not in dates

    @patch("services.archive.get_memories")
    def test_paso_el_lunes(self, mock_env):
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
            search_archive("que paso el lunes")
        )
        assert mem is not None
        dates = {
            m["date"] for m in mem["data"]
        }
        assert dates == {target}

    @patch("services.archive.get_memories")
    def test_paso_el_mes_pasado(self, mock_env):
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
            search_archive("que paso el mes pasado")
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

    @patch("services.archive.get_memories")
    def test_paso_anteayer(self, mock_env):
        target = _day_back(2)
        mock_env.return_value = {"memories": [
            _mem(
                "aa", target,
                "viaje de ida y vuelta",
            ),
            _mem(
                "h", _day_back(0),
                "terminar decia esta semana",
            ),
        ]}
        mem = _memory_result(
            search_archive("que paso anteayer")
        )
        assert mem is not None
        dates = {
            m["date"] for m in mem["data"]
        }
        assert dates == {target}


class TestG1Clasificacion:

    def test_paso_temporal_todas_memory_search(self):
        for ask in (
            "que paso hace 3 dias",
            "que paso el lunes",
            "que paso esta semana",
            "que paso la semana pasada",
            "que paso el mes pasado",
            "que paso el viernes",
            "que paso anteayer",
            "que paso hace una semana",
        ):
            r = _classify(ask)
            assert r.intent == MEMORY_SEARCH, ask


class TestG1Think:

    @patch("brain.core.ask_ollama")
    @_seed_clock
    def test_paso_esta_semana_real_determinista(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        ctx = ConversationContext()
        r = think(
            "que paso esta semana", context=ctx,
        )
        assert r
        assert "No tengo memorias registradas." \
            not in r
        assert r != "OLLAMA"
        assert mock_oa.call_count == 0
        assert ctx.conversation_mode == "memory"

    @patch("brain.core.ask_ollama")
    @_seed_clock
    def test_paso_semana_pasada_real_vacio(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        r = think(
            "que paso la semana pasada",
            context=ConversationContext(),
        )
        assert "No tengo memorias registradas." in r
        assert "terminar decia esta semana" not in r
        assert mock_oa.call_count == 0

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_paso_hace_dias_inyectado_think(
        self, mock_env, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        target = _day_back(3)
        mock_env.return_value = {"memories": [
            _mem(
                "t", target,
                "reunion que paso ese dia",
            ),
            _mem(
                "h", _day_back(0),
                "terminar decia esta semana",
            ),
            _mem(
                "a", _day_back(1),
                "cafe por la tarde",
            ),
        ]}
        ctx = ConversationContext()
        r = think(
            "que paso hace 3 dias", context=ctx,
        )
        assert "reunion que paso ese dia" in r
        assert "terminar decia esta semana" not in r
        assert "cafe por la tarde" not in r
        assert mock_oa.call_count == 0
        assert ctx.conversation_mode == "memory"

    @patch("brain.core.ask_ollama")
    def test_paso_temporal_una_busqueda(self, mock_oa):
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
                "que paso esta semana",
                context=ConversationContext(),
            )
            assert mock_oa.call_count == 0
        finally:
            coremod.search_deca_memory = orig
        assert calls["n"] == 1

    @patch("brain.core.ask_ollama")
    def test_gate_field_memories_paso(self, mock_oa):
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
                "que paso esta semana",
                context=ConversationContext(),
            )
        assert "No tengo memorias registradas." in r
        assert mock_oa.call_count == 0


# ==========================================
# G5. ENTIDAD CON "CON X" + RANGO TEMPORAL
# ==========================================


class TestG5Extraccion:

    def test_extract_con_y_sobre(self):
        assert extract_search_entity(
            "que paso con kanye"
        ) == "kanye"
        assert extract_search_entity(
            "que paso sobre kanye"
        ) == "kanye"
        assert extract_search_entity(
            "que recuerdas sobre kanye"
        ) == "kanye"

    def test_extract_con_temporal(self):
        assert extract_search_entity(
            "que paso con kanye el lunes"
        ) == "kanye"
        assert extract_search_entity(
            "que hice con maria hace 3 dias"
        ) == "maria"
        assert extract_search_entity(
            "que paso sobre kanye la semana pasada"
        ) == "kanye"

    def test_filter_con_temporal_limpiada(self):
        kanye = _mem(
            "k", _day_back(3),
            "estudio con kanye ese dia",
        )
        maria = _mem(
            "m", _day_back(3),
            "sesion de maria hace 3 dias",
        )
        result = {
            "field": "memories",
            "data": [kanye, maria],
            "total": 2,
        }
        out = filter_memories_by_entity(
            result, "kanye el lunes",
        )
        assert out is not None
        assert len(out["data"]) == 1
        assert out["data"][0] is kanye

    def test_con_no_extrae_sin_entidad(self):
        assert extract_search_entity(
            "que paso con el lunes"
        ) is None


class TestG5Think:

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_con_kanye_el_lunes_inyectado(
        self, mock_env, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        target = _prev_weekday(0)
        mock_env.return_value = {"memories": [
            _mem(
                "klu", target,
                "estudio con kanye ese lunes",
            ),
            _mem(
                "hoy", _day_back(0),
                "terminar decia esta semana",
            ),
            _mem(
                "ayer", _day_back(1),
                "mi color favorito es azul",
            ),
        ]}
        ctx = ConversationContext()
        r = think(
            "que paso con kanye el lunes",
            context=ctx,
        )
        assert "estudio con kanye ese lunes" in r
        assert "azul" not in r
        assert "terminar decia esta semana" not in r
        assert mock_oa.call_count == 0
        assert ctx.conversation_mode == "memory"

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_con_kanye_inexistente_limpio(
        self, mock_env, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_env.return_value = {"memories": [
            _mem(
                "hoy", _day_back(0),
                "terminar decia esta semana",
            ),
        ]}
        ctx = ConversationContext()
        r = think(
            "que paso con kanye el lunes",
            context=ctx,
        )
        assert "No recuerdo nada" in r
        assert "sobre kanye" in r
        assert "kanye el lunes" not in r
        assert mock_oa.call_count == 0
        assert ctx.conversation_mode == "memory"

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_con_maria_hace_dias_entidad_y_rango(
        self, mock_env, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        target = _day_back(3)
        mock_env.return_value = {"memories": [
            _mem(
                "mk", target,
                "sesion de maria hace 3 dias",
            ),
            _mem(
                "kk", target,
                "reunion de kanye hace 3 dias",
            ),
            _mem(
                "hoy", _day_back(0),
                "terminar decia esta semana",
            ),
            _mem(
                "ayer", _day_back(1),
                "cafe por la tarde",
            ),
        ]}
        ctx = ConversationContext()
        r = think(
            "que hice con maria hace 3 dias",
            context=ctx,
        )
        assert "sesion de maria hace 3 dias" in r
        assert "reunion de kanye" not in r
        assert "terminar decia esta semana" not in r
        assert mock_oa.call_count == 0
        assert ctx.conversation_mode == "memory"

    @patch("brain.core.ask_ollama")
    @_seed_clock
    def test_con_kanye_ayer_real_determinista(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        ctx = ConversationContext()
        r = think(
            "que paso con kanye ayer",
            context=ctx,
        )
        assert r
        assert "Kanye" in r
        assert "favorito" not in r
        assert r != "OLLAMA"
        assert mock_oa.call_count == 0
        assert ctx.conversation_mode == "memory"

    @patch("brain.core.ask_ollama")
    @_seed_clock
    def test_sobre_kanye_sigue_determinista(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        r = think(
            "que paso sobre kanye",
            context=ConversationContext(),
        )
        assert "Kanye" in r
        assert mock_oa.call_count == 0


# ==========================================
# G2. CARDINALES "UN/UNA" ≡ 1
# ==========================================


class TestG2Parser:

    def test_parse_hace_un_dia(self):
        result = parse_relative_date(
            "hace un dia", NOW,
        )
        expected = (
            NOW - timedelta(days=1)
        ).date()
        assert result == expected

    def test_parse_hace_una_semana(self):
        result = parse_relative_date(
            "hace una semana", NOW,
        )
        expected = (
            NOW - timedelta(weeks=1)
        ).date()
        assert result == expected

    def test_parse_hace_un_mes(self):
        result = parse_relative_date(
            "hace un mes", NOW,
        )
        expected = (
            NOW - timedelta(days=30)
        ).date()
        assert result == expected


class TestG2SearchArchive:

    @patch("services.archive.get_memories")
    def test_hace_un_dia(self, mock_env):
        target = _day_back(1)
        mock_env.return_value = {"memories": [
            _mem(
                "t", target,
                "cafe con maria ese dia",
            ),
            _mem(
                "h", _day_back(0),
                "terminar decia esta semana",
            ),
            _mem(
                "aa", _day_back(2),
                "viaje de ida y vuelta",
            ),
        ]}
        mem = _memory_result(
            search_archive("que hice hace un dia")
        )
        assert mem is not None
        dates = {
            m["date"] for m in mem["data"]
        }
        assert dates == {target}

    @patch("services.archive.get_memories")
    def test_hace_una_semana(self, mock_env):
        target = _day_back(7)
        mock_env.return_value = {"memories": [
            _mem(
                "t", target,
                "viaje al norte hace una semana",
            ),
            _mem(
                "h", _day_back(0),
                "terminar decia esta semana",
            ),
        ]}
        mem = _memory_result(
            search_archive("que hice hace una semana")
        )
        assert mem is not None
        dates = {
            m["date"] for m in mem["data"]
        }
        assert dates == {target}
        assert _day_back(0) not in dates

    @patch("services.archive.get_memories")
    def test_paso_hace_una_semana(self, mock_env):
        target = _day_back(7)
        mock_env.return_value = {"memories": [
            _mem(
                "t", target,
                "viaje al norte hace una semana",
            ),
            _mem(
                "h", _day_back(0),
                "terminar decia esta semana",
            ),
        ]}
        mem = _memory_result(
            search_archive("que paso hace una semana")
        )
        assert mem is not None
        dates = {
            m["date"] for m in mem["data"]
        }
        assert dates == {target}


class TestG2ThinkFollowUp:

    @patch("brain.core.ask_ollama")
    def test_hace_una_semana_real_no_hoy(self, mock_oa):
        mock_oa.return_value = "OLLAMA"
        r = think(
            "que hice hace una semana",
            context=ConversationContext(),
        )
        assert "terminar decia esta semana" not in r
        assert r != "OLLAMA"
        assert mock_oa.call_count == 0

    def test_y_hace_una_semana(self):
        r = resolve_follow_up(
            "y hace una semana", _memory_ctx(),
        )
        assert r == (
            MEMORY_SEARCH, "que hice hace una semana",
        )
        assert _classify(r[1]).intent == MEMORY_SEARCH

    def test_clasificacion_hace_una_semana(self):
        assert _classify(
            "que hice hace una semana"
        ).intent == MEMORY_SEARCH
        assert _classify(
            "que paso hace una semana"
        ).intent == MEMORY_SEARCH