"""
PHASE 8.9B — HISTORICAL VERB TEMPORAL COVERAGE (G3)

Consultas con verbo histórico (sucedio / ocurrio /
ha pasado / hubo / ha habido ...) + referencia temporal
explícita → MEMORY_SEARCH determinista, reutilizando el
filtro temporal de 8.7B-2/8.9A. Sin referencia temporal
NO se clasifica MEMORY_SEARCH (evitar falsos positivos);
"eventos de deca" sigue siendo ARCHIVE (G4 intacto).
La familia EVENTS (acontecimientos / acontecio / hechos /
eventos + temporal) es dominio ARCHIVE (G1): se verifica
en test_familia_events_es_archive.

Preserva: 1 sola búsqueda, gate field=="memories",
hoy/ayer/anteayer, entidad + temporal (G1/G5), límites/
dedupe, thresholds/confidence, TIL/modelo/prompt/OLLAMA.
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
    ARCHIVE_SEARCH,
    FREE_TALK,
    AMBIGUOUS_INPUT,
    MEMORY_SEARCH,
)

from services.archive import search_archive

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


# ==========================================
# A. CLASIFICACIÓN: POSITIVOS
# ==========================================


class TestG3ClasificacionPositivos:

    def test_verbos_temporales_memory_search(self):
        for ask in (
            "que sucedio ayer",
            "que ocurrio ayer",
            "que ha pasado hoy",
            "que habia pasado ayer",
            "que paso hoy",
            "que hubo esta semana",
            "que hubo ayer",
            "que ha habido esta semana",
            "que sucedio anteayer",
            "que sucedio el lunes",
            "que hubo el mes pasado",
            "que sucedio con kanye ayer",
        ):
            r = _classify(ask)
            assert r.intent == MEMORY_SEARCH, ask
            assert r.confidence >= 0.50, ask

    def test_familia_events_es_archive(self):
        for ask in (
            "que acontecio ayer",
            "que acontecio hace una semana",
            "que acontecio con maria hace 3 dias",
            "que acontecimientos hubo "
            "la semana pasada",
            "que eventos hubo esta semana",
            "que eventos sucedieron ayer",
            "que acontecimientos acontecieron "
            "el lunes",
            "que hechos hubo hace 3 dias",
        ):
            r = _classify(ask)
            assert r.intent == ARCHIVE_SEARCH, ask
            assert r.confidence >= 0.50, ask

    def test_paso_el_viernes_sigue(self):
        for ask in (
            "que paso el viernes",
            "que paso esta semana",
            "que paso el mes pasado",
        ):
            r = _classify(ask)
            assert r.intent == MEMORY_SEARCH, ask


# ==========================================
# B. CLASIFICACIÓN: NEGATIVOS / FALSOS
# ==========================================


class TestG3ClasificacionNegativos:

    def test_sin_temporal_no_memory(self):
        for ask in (
            "que sucedio",
            "que acontecio",
            "que ocurrio",
            "que hubo",
            "que eventos hubo",
            "que acontecimientos hubo",
            "que ha pasado",
            "que sucedio manana",
            "que acontecimientos hubo despues",
            "que hubo algo",
        ):
            r = _classify(ask)
            assert r.intent != MEMORY_SEARCH, ask
            assert r.intent in (
                FREE_TALK, AMBIGUOUS_INPUT,
            ), ask

    def test_eventos_de_deca_sigue_archive(self):
        r = _classify(
            "que eventos de deca hubo "
            "la semana pasada"
        )
        assert r.intent == ARCHIVE_SEARCH
        assert r.confidence >= 0.50


# ==========================================
# C. search_archive POR VERBO (inyectado)
# ==========================================


class TestG3SearchArchive:

    @patch("services.archive.get_memories")
    def test_sucedio_ayer(self, mock_env):
        target = _day_back(1)
        mock_env.return_value = {"memories": [
            _mem("t", target, "concierto esa noche"),
            _mem("h", _day_back(0), "terminar hoy"),
            _mem("aa", _day_back(2), "viaje viejo"),
        ]}
        mem = _memory_result(
            search_archive("que sucedio ayer")
        )
        assert mem is not None
        dates = {m["date"] for m in mem["data"]}
        assert dates == {target}

    @patch("services.archive.get_memories")
    def test_acontecio_ayer(self, mock_env):
        target = _day_back(1)
        mock_env.return_value = {"memories": [
            _mem("t", target, "concierto esa noche"),
            _mem("h", _day_back(0), "terminar hoy"),
        ]}
        mem = _memory_result(
            search_archive("que acontecio ayer")
        )
        assert mem is not None
        dates = {m["date"] for m in mem["data"]}
        assert dates == {target}

    @patch("services.archive.get_memories")
    def test_ha_pasado_hoy(self, mock_env):
        target = _day_back(0)
        mock_env.return_value = {"memories": [
            _mem("t", target, "sesion de decia hoy"),
            _mem("a", _day_back(1), "cafe por la tarde"),
        ]}
        mem = _memory_result(
            search_archive("que ha pasado hoy")
        )
        assert mem is not None
        dates = {m["date"] for m in mem["data"]}
        assert dates == {target}

    @patch("services.archive.get_memories")
    def test_hubo_esta_semana(self, mock_env):
        start, end = _week_bounds(0)
        prev_start, _ = _week_bounds(-1)
        mock_env.return_value = {"memories": [
            _mem("h", _day_back(0), "terminar hoy"),
            _mem("a", _day_back(1), "reunion ayer"),
            _mem("p", prev_start, "asado viejo"),
        ]}
        mem = _memory_result(
            search_archive("que hubo esta semana")
        )
        assert mem is not None
        dates = {m["date"] for m in mem["data"]}
        assert _day_back(0) in dates
        assert _day_back(1) in dates
        assert all(start <= d <= end for d in dates)
        assert prev_start not in dates

    @patch("services.archive.get_memories")
    def test_eventos_hubo_esta_semana(self, mock_env):
        prev_start, _ = _week_bounds(-1)
        mock_env.return_value = {"memories": [
            _mem("h", _day_back(0), "terminar hoy"),
            _mem("a", _day_back(1), "reunion ayer"),
            _mem("p", prev_start, "asado viejo"),
        ]}
        mem = _memory_result(
            search_archive("que eventos hubo esta semana")
        )
        assert mem is not None
        dates = {m["date"] for m in mem["data"]}
        assert _day_back(0) in dates
        assert _day_back(1) in dates
        assert prev_start not in dates

    @patch("services.archive.get_memories")
    def test_acontecimientos_semana_pasada(
        self, mock_env,
    ):
        start, end = _week_bounds(-1)
        mock_env.return_value = {"memories": [
            _mem("ini", start, "asado familiar"),
            _mem("fin", end, "cafe con maria"),
            _mem("hoy", _day_back(0), "terminar hoy"),
        ]}
        mem = _memory_result(
            search_archive(
                "que acontecimientos hubo "
                "la semana pasada"
            )
        )
        assert mem is not None
        dates = {m["date"] for m in mem["data"]}
        assert dates == {start, end}
        assert _day_back(0) not in dates

    @patch("services.archive.get_memories")
    def test_sucedio_hace_3_dias(self, mock_env):
        target = _day_back(3)
        mock_env.return_value = {"memories": [
            _mem("t", target, "fueron al cine"),
            _mem("h", _day_back(0), "terminar hoy"),
        ]}
        mem = _memory_result(
            search_archive("que sucedio hace 3 dias")
        )
        assert mem is not None
        dates = {m["date"] for m in mem["data"]}
        assert dates == {target}

    @patch("services.archive.get_memories")
    def test_hubo_el_lunes(self, mock_env):
        target = _prev_weekday(0)
        mock_env.return_value = {"memories": [
            _mem("lu", target, "guardia laboratorio"),
            _mem("hk", _day_back(0), "reunion kanye hoy"),
        ]}
        mem = _memory_result(
            search_archive("que hubo el lunes")
        )
        assert mem is not None
        dates = {m["date"] for m in mem["data"]}
        assert dates == {target}

    @patch("services.archive.get_memories")
    def test_hubo_el_mes_pasado(self, mock_env):
        target = _iso(
            _today_date().replace(day=1)
            - timedelta(days=1)
        )
        mock_env.return_value = {"memories": [
            _mem("pm", target, "factura vencida"),
            _mem("tot", _day_back(0), "gasto actual"),
        ]}
        mem = _memory_result(
            search_archive("que hubo el mes pasado")
        )
        assert mem is not None
        dates = {m["date"] for m in mem["data"]}
        assert target in dates
        assert _day_back(0) not in dates

    @patch("services.archive.get_memories")
    def test_acontecio_hace_una_semana(self, mock_env):
        target = _day_back(7)
        mock_env.return_value = {"memories": [
            _mem("t", target, "viaje al norte"),
            _mem("h", _day_back(0), "terminar hoy"),
        ]}
        mem = _memory_result(
            search_archive("que acontecio hace una semana")
        )
        assert mem is not None
        dates = {m["date"] for m in mem["data"]}
        assert dates == {target}


# ==========================================
# D. think END-TO-END (inyectado + reales)
# ==========================================


class TestG3Think:

    @patch("brain.core.ask_ollama")
    @_seed_clock
    def test_ha_pasado_hoy_real(self, mock_oa):
        mock_oa.return_value = "OLLAMA"
        ctx = ConversationContext()
        r = think("que ha pasado hoy", context=ctx)
        assert r
        assert "No tengo memorias registradas." \
            not in r
        assert r != "OLLAMA"
        assert mock_oa.call_count == 0
        assert ctx.conversation_mode == "memory"

    @patch("brain.core.ask_ollama")
    @_seed_clock
    def test_sucedio_ayer_real(self, mock_oa):
        mock_oa.return_value = "OLLAMA"
        ctx = ConversationContext()
        r = think("que sucedio ayer", context=ctx)
        assert r
        assert r != "OLLAMA"
        assert mock_oa.call_count == 0
        assert ctx.conversation_mode == "memory"

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_history")
    def test_acontecimientos_semana_pasada_vacio(
        self, mock_h, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_h.return_value = {"events": []}
        r = think(
            "que acontecimientos hubo "
            "la semana pasada",
            context=ConversationContext(),
        )
        assert (
            "No encontré información "
            "registrada en el archivo."
            in r
        )
        assert "terminar decia esta semana" not in r
        assert "No tengo memorias" not in r
        assert mock_oa.call_count == 0

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_sucedio_ayer_inyectado(
        self, mock_env, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        target = _day_back(1)
        mock_env.return_value = {"memories": [
            _mem("t", target, "concierto esa noche"),
            _mem("h", _day_back(0), "terminar hoy"),
        ]}
        ctx = ConversationContext()
        r = think("que sucedio ayer", context=ctx)
        assert "concierto esa noche" in r
        assert "terminar hoy" not in r
        assert mock_oa.call_count == 0
        assert ctx.conversation_mode == "memory"

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_history")
    def test_acontecio_con_kanye_ayer_entidad(
        self, mock_h, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        target = _day_back(1)
        mock_h.return_value = {"events": [
            {"id": "e1", "date": target, "title": "Show",
             "description": "estudio con kanye en vivo"},
            {"id": "e2", "date": _day_back(0), "title": "Hoy",
             "description": "reunion de kanye hoy"},
        ]}
        ctx = ConversationContext()
        r = think("que acontecio con kanye ayer",
                  context=ctx)
        assert "estudio con kanye" in r
        assert "reunion de kanye hoy" not in r
        assert mock_oa.call_count == 0
        assert ctx.conversation_mode == "archive"

    @patch("brain.core.ask_ollama")
    def test_sucedio_ayer_una_busqueda(self, mock_oa):
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
                "que sucedio ayer",
                context=ConversationContext(),
            )
            assert mock_oa.call_count == 0
        finally:
            coremod.search_deca_memory = orig
        assert calls["n"] == 1

    @patch("brain.core.ask_ollama")
    def test_gate_field_memories_verbo(self, mock_oa):
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
                "que sucedio ayer",
                context=ConversationContext(),
            )
        assert "No tengo memorias registradas." in r
        assert mock_oa.call_count == 0


# ==========================================
# E. REGRESIONES G1 / G5 / G2
# ==========================================


class TestRegresionesG1G5G2:

    @patch("services.archive.get_memories")
    def test_paso_el_lunes_g1_inalterado(
        self, mock_env,
    ):
        target = _prev_weekday(0)
        mock_env.return_value = {"memories": [
            _mem("lu", target, "guardia laboratorio"),
            _mem("hk", _day_back(0), "reunion kanye hoy"),
        ]}
        mem = _memory_result(
            search_archive("que paso el lunes")
        )
        assert mem is not None
        dates = {m["date"] for m in mem["data"]}
        assert dates == {target}

    @patch("services.archive.get_memories")
    def test_hace_una_semana_g2_inalterado(
        self, mock_env,
    ):
        target = _day_back(7)
        mock_env.return_value = {"memories": [
            _mem("t", target, "viaje al norte"),
            _mem("h", _day_back(0), "terminar hoy"),
        ]}
        mem = _memory_result(
            search_archive("que hice hace una semana")
        )
        assert mem is not None
        dates = {m["date"] for m in mem["data"]}
        assert dates == {target}

    def test_extract_con_verbo_nuevo(self):
        assert extract_search_entity(
            "que acontecimientos hubo con kanye ayer"
        ) == "kanye"
        assert extract_search_entity(
            "que acontecio con kanye ayer"
        ) == "kanye"

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_con_kanye_el_lunes_g5_inalterado(
        self, mock_env, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        target = _prev_weekday(0)
        mock_env.return_value = {"memories": [
            _mem("klu", target, "estudio con kanye"),
            _mem("hoy", _day_back(0), "terminar decia"),
        ]}
        ctx = ConversationContext()
        r = think("que paso con kanye el lunes",
                  context=ctx)
        assert "estudio con kanye" in r
        assert "terminar decia" not in r
        assert mock_oa.call_count == 0

    @patch("brain.core.ask_ollama")
    @_seed_clock
    def test_sobre_kanye_sigue(self, mock_oa):
        mock_oa.return_value = "OLLAMA"
        r = think(
            "que paso sobre kanye",
            context=ConversationContext(),
        )
        assert "Kanye" in r
        assert mock_oa.call_count == 0