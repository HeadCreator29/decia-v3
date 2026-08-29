"""
PHASE 8.9C — TEMPORAL HISTORY/EVENTS FILTER (G4)

Las consultas ARCHIVE/EVENTS con referencia temporal
explícita (hoy, ayer, anteayer, esta semana, la semana
pasada, este mes, el mes pasado, el lunes..domingo,
hace N dias/semanas/meses, hace un/una ...) filtran los
eventos por la misma ventana temporal que usa MEMORY,
reutilizando _resolve_temporal_filter (sin duplicar
fechas). Sin referencia temporal el archivo es idéntico.

Invariantes: single-pass, gate field=="memories",
"que paso la semana pasada" sigue siendo MEMORY,
"que eventos de deca hubo la semana pasada" es
ARCHIVE/EVENTS con filtro (sin eventos de otras fechas),
el dominio archive no es ocupado por memorias (item 7),
MEMORY_SEARCH / search_deca_memory / core intactos.
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


def _event(date, title, desc="Detalle"):
    return {
        "date": date,
        "title": title,
        "description": desc,
    }


def _events_result(results):
    for r in results:
        if r.get("field") == "events":
            return r
    return None


# ==========================================
# A. CLASIFICACIÓN: DOMINIO CONSERVADO
# ==========================================


class TestG4Clasificacion:

    def test_distincion_memory_vs_archivo(self):
        r_mem = _classify("que paso la semana pasada")
        assert r_mem.intent == MEMORY_SEARCH
        r_arch = _classify(
            "que eventos de deca hubo la semana pasada"
        )
        assert r_arch.intent == ARCHIVE_SEARCH
        assert r_arch.confidence >= 0.50

    def test_variantes_temporales_archivo(self):
        for temporal in (
            "ayer", "hoy", "anteayer",
            "esta semana", "la semana pasada",
            "el lunes", "el viernes",
            "el mes pasado", "este mes",
            "hace 3 dias", "hace una semana",
        ):
            ask = (
                f"que eventos de deca hubo {temporal}"
            )
            r = _classify(ask)
            assert r.intent == ARCHIVE_SEARCH, ask


# ==========================================
# B. search_archive: FILTRO TEMPORAL EVENTS
# ==========================================


class TestG4SearchArchive:

    @patch("services.archive.get_history")
    def test_semana_pasada_solo_rango(
        self, mock_h,
    ):
        start, end = _week_bounds(-1)
        mock_h.return_value = {"events": [
            _event("2025-08-29", "Inicio viejo"),
            _event(_day_back(0), "Hoy"),
            _event(start, "Evento ini"),
            _event(end, "Evento fin"),
        ]}
        ev = _events_result(
            search_archive(
                "que eventos de deca hubo "
                "la semana pasada"
            )
        )
        assert ev is not None
        dates = {e["date"] for e in ev["data"]}
        assert dates == {start, end}
        assert "2025-08-29" not in dates
        assert _day_back(0) not in dates

    @patch("services.archive.get_history")
    def test_esta_semana_no_otra_fechas(
        self, mock_h,
    ):
        start, end = _week_bounds(0)
        prev_start, _ = _week_bounds(-1)
        mock_h.return_value = {"events": [
            _event("2025-08-29", "Viejo"),
            _event(prev_start, "Semana anterior"),
            _event(_day_back(0), "Hoy"),
            _event(_day_back(1), "Ayer"),
        ]}
        ev = _events_result(
            search_archive(
                "que eventos de deca hubo esta semana"
            )
        )
        assert ev is not None
        dates = {e["date"] for e in ev["data"]}
        assert _day_back(0) in dates
        assert _day_back(1) in dates
        assert all(start <= d <= end for d in dates)
        assert prev_start not in dates
        assert "2025-08-29" not in dates

    @patch("services.archive.get_history")
    def test_ayer_exacto(self, mock_h):
        mock_h.return_value = {"events": [
            _event(_day_back(1), "Ayer"),
            _event(_day_back(0), "Hoy"),
            _event("2025-08-29", "Viejo"),
        ]}
        ev = _events_result(
            search_archive(
                "que eventos de deca hubo ayer"
            )
        )
        assert ev is not None
        dates = {e["date"] for e in ev["data"]}
        assert dates == {_day_back(1)}

    @patch("services.archive.get_history")
    def test_hoy_exacto(self, mock_h):
        mock_h.return_value = {"events": [
            _event(_day_back(0), "Hoy"),
            _event(_day_back(1), "Ayer"),
        ]}
        ev = _events_result(
            search_archive(
                "que eventos de deca hubo hoy"
            )
        )
        assert ev is not None
        dates = {e["date"] for e in ev["data"]}
        assert dates == {_day_back(0)}

    @patch("services.archive.get_history")
    def test_anteayer_exacto(self, mock_h):
        mock_h.return_value = {"events": [
            _event(_day_back(2), "Anteayer"),
            _event(_day_back(1), "Ayer"),
        ]}
        ev = _events_result(
            search_archive(
                "que eventos de deca hubo anteayer"
            )
        )
        assert ev is not None
        dates = {e["date"] for e in ev["data"]}
        assert dates == {_day_back(2)}

    @patch("services.archive.get_history")
    def test_el_lunes_exacto(self, mock_h):
        target = _prev_weekday(0)
        mock_h.return_value = {"events": [
            _event(target, "Lunes"),
            _event(_day_back(0), "Hoy"),
        ]}
        ev = _events_result(
            search_archive(
                "que eventos de deca hubo el lunes"
            )
        )
        assert ev is not None
        dates = {e["date"] for e in ev["data"]}
        assert dates == {target}

    @patch("services.archive.get_history")
    def test_el_mes_pasado_exacto(self, mock_h):
        target = _iso(
            _today_date().replace(day=1)
            - timedelta(days=1)
        )
        mock_h.return_value = {"events": [
            _event(target, "Mes pasado"),
            _event(_day_back(0), "Hoy"),
        ]}
        ev = _events_result(
            search_archive(
                "que eventos de deca hubo "
                "el mes pasado"
            )
        )
        assert ev is not None
        dates = {e["date"] for e in ev["data"]}
        assert target in dates
        assert _day_back(0) not in dates

    @patch("services.archive.get_history")
    def test_hace_3_dias_exacto(self, mock_h):
        target = _day_back(3)
        mock_h.return_value = {"events": [
            _event(target, "Tres dias"),
            _event(_day_back(0), "Hoy"),
        ]}
        ev = _events_result(
            search_archive(
                "que eventos de deca hubo hace 3 dias"
            )
        )
        assert ev is not None
        dates = {e["date"] for e in ev["data"]}
        assert dates == {target}

    @patch("services.archive.get_history")
    def test_hace_una_semana_exacto(self, mock_h):
        target = _day_back(7)
        mock_h.return_value = {"events": [
            _event(target, "Una semana"),
            _event(_day_back(0), "Hoy"),
        ]}
        ev = _events_result(
            search_archive(
                "que eventos de deca hubo "
                "hace una semana"
            )
        )
        assert ev is not None
        dates = {e["date"] for e in ev["data"]}
        assert dates == {target}

    @patch("services.archive.get_history")
    def test_sin_temporal_todos(self, mock_h):
        mock_h.return_value = {"events": [
            _event("2025-08-29", "Viejo"),
            _event(_day_back(0), "Hoy"),
        ]}
        ev = _events_result(
            search_archive("que eventos de deca")
        )
        assert ev is not None
        dates = {e["date"] for e in ev["data"]}
        assert dates == {"2025-08-29", _day_back(0)}

    @patch("services.archive.get_history")
    def test_historia_sin_temporal_todos(self, mock_h):
        mock_h.return_value = {"events": [
            _event("2025-08-29", "Viejo"),
            _event(_day_back(0), "Hoy"),
        ]}
        ev = _events_result(
            search_archive("historia de deca")
        )
        assert ev is not None
        dates = {e["date"] for e in ev["data"]}
        assert dates == {"2025-08-29", _day_back(0)}

    @patch("services.archive.get_history")
    def test_temporal_sin_eventos_dominio_archivo(
        self, mock_h,
    ):
        mock_h.return_value = {"events": [
            _event("2025-08-29", "Viejo"),
            _event(_day_back(0), "Hoy"),
        ]}
        ev = _events_result(
            search_archive(
                "que eventos de deca hubo hace 3 dias"
            )
        )
        assert ev is not None
        assert ev["data"] == []


# ==========================================
# C. think (reales + inyectados + single-pass)
# ==========================================


class TestG4Think:

    @patch("brain.core.ask_ollama")
    @_seed_clock
    def test_eventos_esta_semana_real_solo_ventana(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        ctx = ConversationContext()
        r = think(
            "que eventos de deca hubo esta semana",
            context=ctx,
        )
        assert r
        assert "Nacimiento de DECIA" in r
        assert "Inicio de la d" not in r
        assert r != "OLLAMA"
        assert mock_oa.call_count == 0
        assert ctx.conversation_mode == "archive"

    @patch("brain.core.ask_ollama")
    @_seed_clock
    def test_eventos_ayer_real_vacio(self, mock_oa):
        mock_oa.return_value = "OLLAMA"
        ctx = ConversationContext()
        r = think(
            "que eventos de deca hubo ayer",
            context=ctx,
        )
        assert (
            "No encontré información registrada "
            "en el archivo."
            in r
        )
        assert "favorito" not in r
        assert "2025" not in r
        assert mock_oa.call_count == 0
        assert ctx.conversation_mode == "archive"

    @patch("brain.core.ask_ollama")
    @_seed_clock
    def test_eventos_semana_pasada_real_vacio(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        r = think(
            "que eventos de deca hubo la semana pasada",
            context=ConversationContext(),
        )
        assert (
            "No encontré información registrada "
            "en el archivo."
            in r
        )
        assert "Inicio de la d" not in r
        assert mock_oa.call_count == 0

    @patch("brain.core.ask_ollama")
    def test_historia_sin_temporal_total(self, mock_oa):
        mock_oa.return_value = "OLLAMA"
        r = think(
            "historia de deca",
            context=ConversationContext(),
        )
        assert "Inicio de la d" in r
        assert "Nacimiento de DECIA" in r
        assert mock_oa.call_count == 0

    @patch("brain.core.ask_ollama")
    @_seed_clock
    def test_paso_semana_pasada_sigue_memory(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        ctx = ConversationContext()
        r = think(
            "que paso la semana pasada",
            context=ctx,
        )
        assert "No tengo memorias registradas." in r
        assert mock_oa.call_count == 0
        assert ctx.conversation_mode == "memory"

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_history")
    def test_inyectado_solo_ventana(self, mock_h,
                                    mock_oa):
        mock_oa.return_value = "OLLAMA"
        start, end = _week_bounds(-1)
        mock_h.return_value = {"events": [
            _event("2025-08-29", "Inicio viejo"),
            _event(start, "Evento ini"),
            _event(end, "Evento fin"),
        ]}
        ctx = ConversationContext()
        r = think(
            "que eventos de deca hubo la semana pasada",
            context=ctx,
        )
        assert "Evento ini" in r
        assert "Evento fin" in r
        assert "Inicio viejo" not in r
        assert mock_oa.call_count == 0
        assert ctx.conversation_mode == "archive"

    @patch("brain.core.ask_ollama")
    def test_eventos_una_busqueda(self, mock_oa):
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
                "que eventos de deca hubo la semana pasada",
                context=ConversationContext(),
            )
            assert mock_oa.call_count == 0
        finally:
            coremod.search_deca_memory = orig
        assert calls["n"] == 1