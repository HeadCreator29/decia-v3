"""
PHASE 9.1 — EVENTS ENTITY FILTER (cierre de B1)

La ruta EVENTS/ARCHIVE respeta la entidad solicitada:
- "que eventos hubo sobre kanye" filtra por entidad.
- temporal + entidad se aplican SIEMPRE ambos.
- EVENTS + entidad sin coincidencia -> aviso
  determinista de archivo, MEMORY no suplanta EVENTS.
- EVENTS sin entidad conserva el comportamiento de 8.9C.
- MEMORY + entidad no se altera; MEMORY no recibe ni
  suplanta resultados EVENTS (gate field==memories).
- Sin entidad conocida no se inventan coincidencias.

Mecánica (sin duplicar lógica): classification en
Intent Layer (patrón EVENTS + sobre/con X sin temporal),
filtro de entidad reutilizando _entity_word_matches sobre
title+description+date (misma semántica que MEMORY),
aplicado en core sobre el mejor resultado (single-pass).

Invariantes: single-pass, 0 OLLAMA, contexto archive/
memory intacto, G2/G1/G6/G7 intactos, search_archive sin
parámetro de entidad (una sola capa filtra).
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
from brain.handlers import (
    extract_search_entity,
    filter_memories_by_entity,
)

from brain.intent_types import (
    ARCHIVE_SEARCH,
    MEMORY_SEARCH,
    FREE_TALK,
    AMBIGUOUS_INPUT,
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


def _event(eid, date, title, desc="Detalle"):
    return {
        "id": eid,
        "date": date,
        "title": title,
        "description": desc,
    }


def _mem(mid, date, description):
    return {
        "id": mid,
        "date": date,
        "time": "10:00",
        "description": description,
    }


def _events_result(results):
    for r in results:
        if r.get("field") == "events":
            return r
    return None


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
# A. CLASIFICACIÓN: EVENTS + ENTIDAD
# ==========================================


class TestClasificacion:

    def test_eventos_sobre_entidad_sin_temporal(self):
        for ask in (
            "que eventos hubo sobre kanye",
            "que eventos hubo con kanye",
            "que acontecimientos hubo sobre deca",
            "que hechos hubo sobre maria",
            "que evento sucedio sobre el proyecto",
        ):
            r = _classify(ask)
            assert r.intent == ARCHIVE_SEARCH, ask
            assert r.confidence >= 0.50, ask

    def test_formas_desnudas_siguen_g2(self):
        for ask in (
            "que eventos hubo",
            "que acontecimientos hubo",
            "que hechos hubo",
            "que acontecio",
        ):
            r = _classify(ask)
            assert r.intent != ARCHIVE_SEARCH, ask
            assert r.intent in (FREE_TALK, AMBIGUOUS_INPUT), ask

    def test_verbo_generico_sin_temporal_no_archive(self):
        for ask in (
            "que hubo sobre kanye",
            "que sucedio sobre kanye",
        ):
            r = _classify(ask)
            assert r.intent != ARCHIVE_SEARCH, ask
            assert r.intent != MEMORY_SEARCH, ask

    def test_dominios_intactos_9e(self):
        assert _classify(
            "que sucedio sobre kanye ayer"
        ).intent == MEMORY_SEARCH
        assert _classify(
            "que acontecio sobre kanye ayer"
        ).intent == ARCHIVE_SEARCH

    def test_g2_fuera_de_alcance_se_mantiene(self):
        r = _classify(
            "que acontecimientos de deca hubo ayer"
        )
        assert r.intent == FREE_TALK


# ==========================================
# B. FILTRO UNITARIO (field == "events")
# ==========================================


class TestFiltroUnitarioEvents:

    def test_events_filtra_por_entidad(self):
        result = {
            "type": "history",
            "field": "events",
            "data": [
                _event("e1", "2026-08-25", "Show",
                       "kanye toco en vivo"),
                _event("e2", "2026-08-25", "Feria",
                       "feria del libro"),
            ],
        }
        out = filter_memories_by_entity(
            result, "kanye",
        )
        assert out is not None
        assert out["field"] == "events"
        assert len(out["data"]) == 1
        assert out["data"][0]["id"] == "e1"

    def test_events_sin_coincidencia_data_vacia(self):
        result = {
            "type": "history",
            "field": "events",
            "data": [
                _event("e2", "2026-08-25", "Feria",
                       "feria del libro"),
            ],
        }
        out = filter_memories_by_entity(
            result, "wiseau",
        )
        assert out is not None
        assert out["field"] == "events"
        assert out["data"] == []

    def test_events_sin_entidad_mismo_objeto(self):
        result = {
            "type": "history",
            "field": "events",
            "data": [],
        }
        assert filter_memories_by_entity(
            result, None,
        ) is result

    def test_memory_contrato_intacto(self):
        result = {
            "type": "memory",
            "field": "memories",
            "data": [
                _mem("k", "2026-08-20",
                     "me gusta la musica de Kanye"),
                _mem("s", "2026-08-20",
                     "quiero terminar decia"),
            ],
        }
        out = filter_memories_by_entity(
            result, "kanye",
        )
        assert out is not None
        assert len(out["data"]) == 1
        assert out["data"][0]["id"] == "k"
        empty = filter_memories_by_entity(
            {
                "field": "memories",
                "data": [],
            },
            "kanye",
        )
        assert empty is None

    def test_misma_semantica_memory_events(self):
        events = {
            "field": "events",
            "data": [
                _event("e1", "2026-08-25", "Titulo",
                       "descripcion del evento"),
            ],
        }
        memories = {
            "field": "memories",
            "data": [
                _mem("m", "2026-08-25",
                     "descripcion del evento"),
            ],
        }
        for result in (events, memories):
            out = filter_memories_by_entity(
                result, "evento",
            )
            assert out is not None
            assert len(out["data"]) == 1, result["field"]

    def test_search_archive_no_recibe_entidad(self):
        @patch("services.archive.get_history")
        @patch("services.archive.get_memories")
        def _go(mock_env, mock_h):
            mock_env.return_value = {"memories": []}
            mock_h.return_value = {"events": [
                _event("e1", "2026-08-25", "Show",
                       "kanye toco en vivo"),
                _event("e2", "2026-08-25", "Feria",
                       "feria del libro"),
            ]}
            ev = _events_result(
                search_archive(
                    "que eventos hubo sobre kanye"
                )
            )
            return ev
        ev = _go()
        assert ev is not None
        assert len(ev["data"]) == 2


# ==========================================
# C. think: VÍA COMPLETA (A-K)
# ==========================================


class TestThinkEvents:

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_history")
    @patch("services.archive.get_memories")
    def test_a_eventos_sin_entidad_preservado(
        self, mock_env, mock_h, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_env.return_value = {"memories": []}
        target = _prev_weekday(0)
        mock_h.return_value = {"events": [
            _event("e1", target, "Lunes",
                   "evento del lunes"),
            _event("e2", _day_back(0), "Hoy",
                   "evento de hoy"),
            _event("e3", "2025-08-29", "Viejo",
                   "Inicio de la decada"),
        ]}
        calls, orig = _no_memory_search()
        try:
            r = think(
                "que eventos hubo el lunes",
                context=ConversationContext(),
            )
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig
        assert "evento del lunes" in r
        assert "evento de hoy" not in r
        assert "Inicio de la decada" not in r
        assert mock_oa.call_count == 0
        assert calls["n"] == 1

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_history")
    def test_b_eventos_entidad_sin_temporal(
        self, mock_h, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_h.return_value = {"events": [
            _event("e1", "2026-08-25", "Show",
                   "kanye toco en vivo"),
            _event("e2", "2026-08-20", "Directo",
                   "transmision de kanye"),
            _event("e3", "2026-08-25", "Feria",
                   "feria del libro"),
        ]}
        calls, orig = _no_memory_search()
        ctx = ConversationContext()
        r = think(
            "que eventos hubo sobre kanye",
            context=ctx,
        )
        assert "kanye toco en vivo" in r
        assert "transmision de kanye" in r
        assert "feria del libro" not in r
        assert mock_oa.call_count == 0
        assert calls["n"] == 1
        assert ctx.conversation_mode == "archive"
        assert ctx.last_entity == "kanye"

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_history")
    def test_b2_eventos_entidad_con(self, mock_h,
                                     mock_oa):
        mock_oa.return_value = "OLLAMA"
        mock_h.return_value = {"events": [
            _event("e1", "2026-08-25", "Show",
                   "kanye toco en vivo"),
            _event("e2", "2026-08-25", "Feria",
                   "feria del libro"),
        ]}
        calls, orig = _no_memory_search()
        r = think(
            "que eventos hubo con kanye",
            context=ConversationContext(),
        )
        assert "kanye toco en vivo" in r
        assert "feria del libro" not in r
        assert mock_oa.call_count == 0
        assert calls["n"] == 1

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_history")
    def test_c_eventos_entidad_y_temporal(
        self, mock_h, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        target = _prev_weekday(0)
        mock_h.return_value = {"events": [
            _event("e1", target, "Show",
                   "kanye toco en vivo"),
            _event("e2", _day_back(0), "Directo",
                   "transmision de kanye"),
            _event("e3", target, "Feria",
                   "feria del libro"),
        ]}
        calls, orig = _no_memory_search()
        ctx = ConversationContext()
        r = think(
            "que eventos hubo el lunes sobre kanye",
            context=ctx,
        )
        assert "kanye toco en vivo" in r
        assert "transmision de kanye" not in r
        assert "feria del libro" not in r
        assert mock_oa.call_count == 0
        assert calls["n"] == 1
        assert ctx.conversation_mode == "archive"

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_history")
    @patch("services.archive.get_memories")
    def test_d_entidad_sin_coincidencia_aviso(
        self, mock_env, mock_h, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_env.return_value = {"memories": [
            _mem("mk", "2026-08-20",
                 "me gusta la musica de Kanye"),
        ]}
        mock_h.return_value = {"events": [
            _event("e3", "2026-08-25", "Feria",
                   "feria del libro"),
        ]}
        calls, orig = _no_memory_search()
        ctx = ConversationContext()
        r = think(
            "que eventos hubo sobre kanye",
            context=ctx,
        )
        assert (
            "No encontré información registrada "
            "sobre kanye."
            in r
        )
        assert "me gusta la musica de Kanye" not in r
        assert "No recuerdo" not in r
        assert mock_oa.call_count == 0
        assert calls["n"] == 1
        assert ctx.conversation_mode == "archive"
        assert ctx.last_entity == "kanye"

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_history")
    def test_g_entidad_desconocida_no_inventa(
        self, mock_h, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_h.return_value = {"events": [
            _event("e1", "2026-08-25", "Show",
                   "kanye toco en vivo"),
            _event("e2", "2026-08-25", "Feria",
                   "feria del libro"),
        ]}
        calls, orig = _no_memory_search()
        r = think(
            "que eventos hubo sobre el increible",
            context=ConversationContext(),
        )
        assert (
            "No encontré información registrada "
            "sobre el increible."
            in r
        )
        assert "kanye toco en vivo" not in r
        assert mock_oa.call_count == 0
        assert calls["n"] == 1

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_history")
    def test_h_entidad_multipalabra(self, mock_h,
                                    mock_oa):
        mock_oa.return_value = "OLLAMA"
        mock_h.return_value = {"events": [
            _event("e1", "2026-08-25", "Cena",
                   "cocinamos mi hermana y yo"),
            _event("e2", "2026-08-25", "Show",
                   "kanye vino a la cena"),
        ]}
        calls, orig = _no_memory_search()
        r = think(
            "que eventos hubo sobre mi hermana",
            context=ConversationContext(),
        )
        assert "cocinamos mi hermana y yo" in r
        assert "kanye vino a la cena" not in r
        assert mock_oa.call_count == 0
        assert calls["n"] == 1

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_history")
    @patch("services.archive.get_memories")
    def test_e_memory_entidad_no_alterada(
        self, mock_env, mock_h, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        target = _day_back(1)
        mock_env.return_value = {"memories": [
            _mem("mk", target,
                 "estudio con kanye ayer"),
        ]}
        mock_h.return_value = {"events": [
            _event("e1", target, "Show",
                   "kanye toco en vivo ayer"),
        ]}
        calls, orig = _no_memory_search()
        ctx = ConversationContext()
        r = think(
            "que paso con kanye ayer",
            context=ctx,
        )
        assert "estudio con kanye ayer" in r
        assert "kanye toco en vivo ayer" not in r
        assert mock_oa.call_count == 0
        assert calls["n"] == 1
        assert ctx.conversation_mode == "memory"

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_history")
    @patch("services.archive.get_memories")
    def test_f_memory_no_recibe_events(
        self, mock_env, mock_h, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        target = _day_back(1)
        mock_env.return_value = {"memories": []}
        mock_h.return_value = {"events": [
            _event("e1", target, "Show",
                   "kanye toco en vivo ayer"),
        ]}
        calls, orig = _no_memory_search()
        ctx = ConversationContext()
        r = think(
            "que hubo sobre kanye ayer",
            context=ctx,
        )
        assert "No recuerdo nada sobre kanye." in r
        assert "kanye toco en vivo ayer" not in r
        assert mock_oa.call_count == 0
        assert calls["n"] == 1
        assert ctx.conversation_mode == "memory"

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_history")
    def test_k_seguimiento_sobre_mismo_tema(
        self, mock_h, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_h.return_value = {"events": [
            _event("e1", "2026-08-25", "Show",
                   "kanye toco en vivo"),
            _event("e2", "2026-08-25", "Feria",
                   "feria del libro"),
        ]}
        ctx = ConversationContext()
        calls, orig = _no_memory_search()
        try:
            r1 = think(
                "que eventos hubo sobre kanye",
                context=ctx,
            )
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig
        assert "kanye toco en vivo" in r1
        assert mock_oa.call_count == 0
        assert calls["n"] == 1
        assert ctx.conversation_mode == "archive"
        assert ctx.last_intent == ARCHIVE_SEARCH
        assert ctx.last_entity == "kanye"

        calls, orig = _no_memory_search()
        try:
            r2 = think("y que mas", context=ctx)
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig
        assert r2 != "OLLAMA"
        assert "kanye toco en vivo" in r2
        assert mock_oa.call_count == 0
        assert calls["n"] == 1
        assert ctx.conversation_mode == "archive"

    def test_g2_sobre_only_temporal_no_entidad(self):
        assert extract_search_entity(
            "que eventos hubo sobre la semana pasada"
        ) is None

    @patch("brain.core.ask_ollama")
    @_seed_clock
    def test_real_eventos_sobre_kanye_determinista(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        calls, orig = _no_memory_search()
        try:
            ctx = ConversationContext()
            r = think(
                "que eventos hubo sobre kanye",
                context=ctx,
            )
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig
        assert (
            "No encontré información registrada "
            "sobre kanye."
            in r
        )
        assert "me gusta la musica" not in r
        assert mock_oa.call_count == 0
        assert calls["n"] == 1
        assert ctx.conversation_mode == "archive"