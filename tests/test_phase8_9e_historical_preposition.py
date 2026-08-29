"""
PHASE 8.9E — HISTORICAL ENTITY PREPOSITION COVERAGE

Los patrones históricos (G3) que aceptan "con X" deben
aceptar también "sobre X" cuando hay referencia temporal
explícita:
"que sucedio sobre kanye ayer" ahora es MEMORY_SEARCH
determinista (antes FREE_TALK -> OLLAMA); la familia
EVENTS "que acontecio sobre kanye ayer" es dominio
ARCHIVE (G1, events), también determinista.

Sin el cambio, dicha consulta es una inconsistencia
detectada en 8.9D. Se mantienen: sin temporal -> no
MEMORY, "eventos de deca" -> ARCHIVE, G6 intacto
("que paso" desnudo), entidad limpia (8.9A/8.9D),
filtro temporal + entidad simultáneos, single-pass,
0 OLLAMA.
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


def _mem(mid, date, description):
    return {
        "id": mid,
        "date": date,
        "time": "10:00",
        "description": description,
    }


SOBRE_CON_TEMPORAL = (
    "que sucedio sobre kanye ayer",
    "que ocurrio sobre kanye el lunes",
    "que paso sobre kanye la semana pasada",
    "que hubo sobre kanye hace 3 dias",
    "que hubo sobre kanye hace una semana",
)

ACONTECIO_SOBRE_TEMPORAL = (
    "que acontecio sobre kanye ayer",
    "que acontecio sobre kanye esta semana",
    "que acontecio sobre maria hace 3 dias",
)


# ==========================================
# A. CLASIFICACIÓN: SOBRE X + TEMPORAL
# ==========================================


class TestSobreTemporalMemoria:

    def test_sobre_x_temporal_memory(self):
        for ask in SOBRE_CON_TEMPORAL:
            r = _classify(ask)
            assert r.intent == MEMORY_SEARCH, ask
            assert r.confidence >= 0.50, ask

    def test_acontecio_sobre_x_temporal_archive(self):
        for ask in ACONTECIO_SOBRE_TEMPORAL:
            r = _classify(ask)
            assert r.intent == ARCHIVE_SEARCH, ask
            assert r.confidence >= 0.50, ask

    def test_patron_b_sobre_x(self):
        for ask in (
            "que acontecimientos hubo sobre deca "
            "esta semana",
            "que eventos sucedieron sobre kanye ayer",
            "que hechos hubo sobre maria "
            "la semana pasada",
        ):
            r = _classify(ask)
            assert r.intent == ARCHIVE_SEARCH, ask


# ==========================================
# B. REGRESIÓN: CON X (8.9A/8.9B)
# ==========================================


class TestConXRegresion:

    def test_con_x_sigue_memory(self):
        for ask in (
            "que sucedio con kanye ayer",
            "que ocurrio con kanye el lunes",
            "que hice con maria hace 3 dias",
        ):
            r = _classify(ask)
            assert r.intent == MEMORY_SEARCH, ask

    def test_acontecio_con_x_es_archive(self):
        for ask in (
            "que acontecio con kanye ayer",
            "que acontecio con maria hace 3 dias",
        ):
            r = _classify(ask)
            assert r.intent == ARCHIVE_SEARCH, ask

    def test_g5_semanal_con_x(self):
        for ask in (
            "que paso con kanye la semana pasada",
            "que hice con maria hace 3 dias",
        ):
            r = _classify(ask)
            assert r.intent == MEMORY_SEARCH, ask


# ==========================================
# C. NEGATIVOS: SIN TEMPORAL / OTROS DOMINIOS
# ==========================================


class TestNegativos:

    def test_sin_temporal_no_memory(self):
        for ask in (
            "que acontecio sobre kanye",
            "que hubo sobre deca",
            "que sucedio sobre maria",
            "que acontecimientos sobre deca",
        ):
            r = _classify(ask)
            assert r.intent != MEMORY_SEARCH, ask

    def test_eventos_de_deca_sigue_archive(self):
        r = _classify(
            "que eventos de deca hubo la semana pasada"
        )
        assert r.intent == ARCHIVE_SEARCH
        assert r.confidence >= 0.50

    def test_g6_paso_desnudo_intacto(self):
        r = _classify("que paso")
        assert r.intent == MEMORY_SEARCH
        assert r.confidence == 0.60
        r2 = _classify("que paso la semana pasada")
        assert r2.intent == MEMORY_SEARCH


# ==========================================
# D. EXTRACCIÓN: ENTIDAD LIMPIA
# ==========================================


class TestEntidadLimpia:

    def test_sobre_x_entidad_limpia(self):
        for ask in SOBRE_CON_TEMPORAL:
            entity = extract_search_entity(ask)
            assert entity is not None, ask
            assert entity == "kanye", ask

    def test_entidad_multipalabra(self):
        assert extract_search_entity(
            "que acontecio sobre mi hermana "
            "la semana pasada"
        ) == "mi hermana"
        assert extract_search_entity(
            "que hubo sobre la seleccion el lunes"
        ) == "la seleccion"

    def test_temporal_puro_es_none(self):
        assert extract_search_entity(
            "que acontecio sobre hace 3 dias"
        ) is None
        assert extract_search_entity(
            "que hubo sobre ayer"
        ) is None


# ==========================================
# E. think: FILTRO + ENTIDAD EN PARALELO
# ==========================================


class TestThink:

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_filtro_y_entidad_simultaneos(
        self, mock_env, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        target = _day_back(3)
        mock_env.return_value = {"memories": [
            _mem(
                "tk", target,
                "estudio muy duro con kanye ese dia",
            ),
            _mem(
                "hk", _day_back(0),
                "kanye me llamo hoy",
            ),
            _mem(
                "tm", target,
                "sesion con maria ese dia",
            ),
        ]}
        ctx = ConversationContext()
        r = think(
            "que hubo sobre kanye hace 3 dias",
            context=ctx,
        )
        assert "estudio muy duro con kanye ese dia" in r
        assert "kanye me llamo hoy" not in r
        assert "sesion con maria ese dia" not in r
        assert mock_oa.call_count == 0
        assert ctx.conversation_mode == "memory"

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_history")
    def test_acontecio_sobre_determinista(
        self, mock_h, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        target = _day_back(1)
        mock_h.return_value = {"events": [
            {"id": "e", "date": target, "title": "Show",
             "description": "kanye toco en vivo"},
        ]}
        from brain import core as coremod
        calls = {"n": 0}
        orig = coremod.search_deca_memory

        def wrapped(msg, *args, **kwargs):
            calls["n"] += 1
            return orig(msg, *args, **kwargs)

        coremod.search_deca_memory = wrapped
        try:
            ctx = ConversationContext()
            r = think(
                "que acontecio sobre kanye ayer",
                context=ctx,
            )
            assert "kanye toco en vivo" in r
            assert mock_oa.call_count == 0
            assert ctx.conversation_mode == "archive"
        finally:
            coremod.search_deca_memory = orig
        assert calls["n"] == 1

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_entidad_multipalabra_think(
        self, mock_env, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        target = _day_back(7)
        mock_env.return_value = {"memories": [
            _mem(
                "hs", target,
                "cocinamos mi hermana y yo",
            ),
            _mem(
                "hk", target,
                "kanye vino a la cena",
            ),
        ]}
        r = think(
            "que hubo sobre mi hermana hace una semana",
            context=ConversationContext(),
        )
        assert "cocinamos mi hermana y yo" in r
        assert "kanye vino a la cena" not in r
        assert mock_oa.call_count == 0

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_history")
    def test_real_acontecio_sobre_kanye_ayer(
        self, mock_h, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        target = _day_back(1)
        mock_h.return_value = {"events": [
            {"id": "e", "date": target, "title": "Recital",
             "description": "Kanye dio un show en la plaza"},
        ]}
        ctx = ConversationContext()
        r = think(
            "que acontecio sobre kanye ayer",
            context=ctx,
        )
        assert r
        assert "Kanye" in r
        assert "kanye ayer" not in r
        assert r != "OLLAMA"
        assert mock_oa.call_count == 0
        assert ctx.conversation_mode == "archive"

    @patch("brain.core.ask_ollama")
    @_seed_clock
    def test_real_paso_sobre_kanye_semana(self,
                                          mock_oa):
        mock_oa.return_value = "OLLAMA"
        r = think(
            "que paso sobre kanye la semana pasada",
            context=ConversationContext(),
        )
        assert "No recuerdo nada sobre kanye." in r
        assert "kanye la semana pasada" not in r
        assert mock_oa.call_count == 0