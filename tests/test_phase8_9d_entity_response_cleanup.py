"""
PHASE 8.9D — TEMPORAL ENTITY RESPONSE CLEANUP (G7)

La entidad de búsqueda extraída de "sobre X"/"con X"
no debe arrastrar la expresión temporal de la consulta:
"que paso con kanye la semana pasada" -> entidad "kanye"
(temporal "la semana pasada" por separado). El filtro
temporal queda intacto; solo cambia la PRESENTACIÓN de
la entidad (mensajes deterministas y contexto).

Invariantes: 0 OLLAMA, single-pass, filtro temporal
intacto, consultas genéricas temporales sin entidad
conservan su respuesta, temporales no se convierten en
entidad, MEMORY_SEARCH / ARCHIVE / core intactos.
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
from brain.handlers import (
    extract_search_entity,
)

NOW = datetime.now().astimezone()


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


def _mem(mid, date, description):
    return {
        "id": mid,
        "date": date,
        "time": "10:00",
        "description": description,
    }


TEMPORALES = (
    "hoy",
    "ayer",
    "anteayer",
    "el lunes",
    "la semana pasada",
    "esta semana",
    "el mes pasado",
    "hace 3 dias",
    "hace una semana",
)


# ==========================================
# A. EXTRACCIÓN: ENTIDAD LIMPIA
# ==========================================


class TestG7Extraccion:

    def test_con_y_sobre_con_temporal(self):
        for temporal in TEMPORALES:
            ask_con = (
                f"que paso con kanye {temporal}"
            )
            assert extract_search_entity(
                ask_con
            ) == "kanye", ask_con
            ask_sobre = (
                f"que paso sobre kanye {temporal}"
            )
            assert extract_search_entity(
                ask_sobre
            ) == "kanye", ask_sobre

    def test_variantes_verbos(self):
        assert extract_search_entity(
            "que sucedio con kanye hace 3 dias"
        ) == "kanye"
        assert extract_search_entity(
            "que acontecio sobre kanye ayer"
        ) == "kanye"
        assert extract_search_entity(
            "que acontecimientos hubo "
            "con kanye el lunes"
        ) == "kanye"
        assert extract_search_entity(
            "que hice sobre kanye la semana pasada"
        ) == "kanye"
        assert extract_search_entity(
            "que hiciste con maria hace una semana"
        ) == "maria"

    def test_entidad_multipalabra_limpia(self):
        assert extract_search_entity(
            "que paso sobre mi hermana "
            "la semana pasada"
        ) == "mi hermana"
        assert extract_search_entity(
            "que paso con la seleccion el lunes"
        ) == "la seleccion"

    def test_sin_temporal_no_cambia(self):
        assert extract_search_entity(
            "que recuerdas sobre kanye"
        ) == "kanye"
        assert extract_search_entity(
            "que paso con los vengadores"
        ) == "los vengadores"


# ==========================================
# B. TEMPORAL NO ES ENTIDAD
# ==========================================


class TestG7TemporalNoEntidad:

    def test_puramente_temporal_es_none(self):
        for ask in (
            "sobre la semana pasada",
            "con el lunes",
            "sobre el mes pasado",
            "con hace una semana",
            "con hace 3 dias",
            "con hoy",
            "con esta semana",
        ):
            assert extract_search_entity(
                ask
            ) is None, ask

    def test_sin_sobre_ni_con(self):
        assert extract_search_entity(
            "que hice la semana pasada"
        ) is None
        assert extract_search_entity(
            "que paso ayer"
        ) is None

    def test_temporal_no_encabeza_entidad(self):
        assert extract_search_entity(
            "que paso con la semana pasada en canada"
        ) == "la semana pasada en canada"
        assert extract_search_entity(
            "que paso sobre el lunes de las novedades"
        ) == "el lunes de las novedades"


# ==========================================
# C. think: MENSAJES LIMPIOS + FILTRO INTACTO
# ==========================================


class TestG7Think:

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_inyectado_entidad_matcheada(
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
        ]}
        ctx = ConversationContext()
        r = think(
            "que paso con kanye el lunes",
            context=ctx,
        )
        assert "estudio con kanye ese lunes" in r
        assert "terminar decia esta semana" not in r
        assert "No recuerdo" not in r
        assert mock_oa.call_count == 0
        assert ctx.conversation_mode == "memory"

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_entidad_sin_resultado_mensaje_limpio(
        self, mock_env, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_env.return_value = {"memories": [
            _mem(
                "hoy", _day_back(0),
                "terminar decia esta semana",
            ),
        ]}
        for ask in (
            "que paso con kanye la semana pasada",
            "que sucedio con kanye hace 3 dias",
            "que hubo con kanye ayer",
            "que paso sobre kanye el lunes",
        ):
            r = think(
                ask,
                context=ConversationContext(),
            )
            assert "No recuerdo nada sobre kanye." in r, ask
            assert "kanye la semana pasada" not in r
            assert "kanye hace 3 dias" not in r
            assert "kanye ayer" not in r
            assert "kanye el lunes" not in r
            assert mock_oa.call_count == 0

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_filtro_temporal_intacto(
        self, mock_env, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        target = _prev_weekday(0)
        mock_env.return_value = {"memories": [
            _mem(
                "otro", _day_back(1),
                "cafe con maria ese dia",
            ),
            _mem(
                "lunes_k", _iso(_today_date()),
                "reunion de kanye hoy",
            ),
        ]}
        r = think(
            "que paso con kanye el lunes",
            context=ConversationContext(),
        )
        assert "No recuerdo nada sobre kanye." in r
        assert "cafe con maria ese dia" not in r
        assert "reunion de kanye hoy" not in r
        assert mock_oa.call_count == 0

    @patch("brain.core.ask_ollama")
    @_seed_clock
    def test_sin_entidad_generico_temporal(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        r = think(
            "que hice la semana pasada",
            context=ConversationContext(),
        )
        assert "No tengo memorias registradas." in r
        assert mock_oa.call_count == 0

    @patch("brain.core.ask_ollama")
    @_seed_clock
    def test_real_kanye_ayer_respuesta_entidad(
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
        assert "kanye ayer" not in r
        assert r != "OLLAMA"
        assert mock_oa.call_count == 0
        assert ctx.conversation_mode == "memory"

    @patch("brain.core.ask_ollama")
    def test_una_sola_busqueda(self, mock_oa):
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
                "que paso con kanye la semana pasada",
                context=ConversationContext(),
            )
            assert mock_oa.call_count == 0
        finally:
            coremod.search_deca_memory = orig
        assert calls["n"] == 1