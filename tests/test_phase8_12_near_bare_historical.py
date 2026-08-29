"""
PHASE 8.12 — NEAR-BARE HISTORICAL QUERY BEHAVIOR

Consulta histórico-desnuda ("que paso", "que sucedio"...)
y temporal ("que paso ayer", ...) mantienen sus rutas
deterministas (G6/HISTORY y MEMORY temporal resp. 8.9A-F).
Las "near-bare" ambiguas e incompletas ("que hubo algo",
"que paso cuando llegue", "que paso despues", ...) NO se
convierten en HISTORY: reciben clarificación determinista
("¿Sí? ¿Qué necesitas?") vía whitelist explícita en
ambiguous_input_response, con 0 búsquedas y 0 OLLAMA.

Se conservan: ARCHIVE temporal (8.9C), entidad con/sobre
(G7/8.9E), anti-regresión 8.11 (negaciones/embebidas ->
FREE_TALK/OLLAMA legítimo), single-pass, TIL intacto.
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

from brain.intent_types import (
    ARCHIVE_SEARCH,
    FREE_TALK,
    MEMORY_SEARCH,
)

IL = IntentLayer()

NOW = datetime.now().astimezone()

BARE_VALIDOS = (
    "que paso",
    "qué pasó",
    "que sucedio",
    "qué sucedió",
    "que ocurrio",
    "qué ocurrió",
    "que hubo",
    "Que Sucedió?",
    "QUE HUBO",
)

TEMPORALES = (
    "que paso ayer",
    "que paso el lunes",
    "que paso esta semana",
    "que hubo ayer",
    "que sucedio hace una semana",
)

NEAR_BARE = (
    "que hubo algo",
    "que hubo alguien",
    "que paso cuando llegue",
    "que paso despues",
    "que paso luego",
    "que sucedio cuando llegue",
)

NEGADAS_EMBEBIDAS = (
    "no me digas que paso",
    "si que paso",
    "dime que paso cuando llegue",
    "que paso manana",
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
# A. HISTORY BARE (G6) DETERMINISTA
# ==========================================


class TestHistoryBare:

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_desnudas_siguen_history(self,
                                     mock_env,
                                     mock_oa):
        mock_oa.return_value = "OLLAMA"
        mock_env.return_value = {"memories": [
            _mem("r", _day_back(1), "memoria personal"),
        ]}
        for ask in BARE_VALIDOS:
            calls, orig = _no_memory_search()
            try:
                ctx = ConversationContext()
                r = think(ask, context=ctx)
            finally:
                import brain.core as coremod
                coremod.search_deca_memory = orig
            assert "Inicio de la d" in r, ask
            assert "Nacimiento de DECIA" in r, ask
            assert "memoria personal" not in r, ask
            assert "No tengo memorias" not in r, ask
            assert r != "OLLAMA", ask
            assert mock_oa.call_count == 0, ask
            assert calls["n"] == 0, ask
            assert ctx.conversation_mode == "archive", ask


# ==========================================
# B. MEMORY TEMPORAL (8.9A–8.9E)
# ==========================================


class TestMemoryTemporal:

    def test_temporales_son_memory(self):
        for ask in TEMPORALES:
            r = _classify(ask)
            assert r.intent == MEMORY_SEARCH, ask

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_que_hubo_ayer_determinista(self,
                                        mock_env,
                                        mock_oa):
        mock_oa.return_value = "OLLAMA"
        mock_env.return_value = {"memories": [
            _mem("a", _day_back(1),
                 "que hubo ayer tercer ensayo"),
        ]}
        calls, orig = _no_memory_search()
        try:
            ctx = ConversationContext()
            r = think("que hubo ayer", context=ctx)
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig
        assert "tercer ensayo" in r
        assert mock_oa.call_count == 0
        assert calls["n"] == 1
        assert ctx.conversation_mode == "memory"


# ==========================================
# C. NEAR-BARE AMBIGUAS -> CLARIFICACIÓN
#    DETERMINISTA (0 búsquedas, 0 OLLAMA)
# ==========================================


class TestNearBareAmbiguas:

    def test_clasificacion_sigue_free_talk(self):
        for ask in NEAR_BARE:
            r = _classify(ask)
            assert r.intent == FREE_TALK, ask

    @patch("brain.core.ask_ollama")
    def test_clarificacion_determinista(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        for ask in NEAR_BARE:
            calls, orig = _no_memory_search()
            try:
                ctx = ConversationContext()
                r = think(ask, context=ctx)
            finally:
                import brain.core as coremod
                coremod.search_deca_memory = orig
            assert "necesitas" in r, ask
            assert "Inicio de la d" not in r, ask
            assert "Nacimiento de DECIA" not in r, ask
            assert "No tengo memorias" not in r, ask
            assert mock_oa.call_count == 0, ask
            assert calls["n"] == 0, ask

    @patch("brain.core.ask_ollama")
    def test_no_contamina_contexto(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        ctx = ConversationContext()
        think("que hubo algo", context=ctx)
        assert ctx.conversation_mode is None
        assert ctx.last_intent is None

    def test_variantes_normalizadas(self):
        from brain.handlers import (
            ambiguous_input_response,
        )
        for ask in (
            "qué hubo algo!",
            "Que pasó luego",
            "que sucedió cuando llegué",
            "QUE HUBO ALGUIEN",
        ):
            r = ambiguous_input_response(ask)
            assert r is not None, ask
            assert "necesitas" in r, ask


# ==========================================
# D. ARCHIVE TEMPORAL (8.9C)
# ==========================================


class TestArchiveTemporal:

    def test_archive_temporal_clasifica(self):
        r = _classify(
            "que eventos de deca hubo la semana pasada"
        )
        assert r.intent == ARCHIVE_SEARCH
        assert r.confidence >= 0.50

    @patch("brain.core.ask_ollama")
    @_seed_clock
    def test_archive_temporal_determinista(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        calls, orig = _no_memory_search()
        try:
            ctx = ConversationContext()
            r = think(
                "que eventos de deca hubo la semana pasada",
                context=ctx,
            )
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig
        assert (
            "No encontré información "
            "registrada en el archivo."
            in r
        )
        assert mock_oa.call_count == 0
        assert calls["n"] == 1


# ==========================================
# E. ENTIDADES (G7, 8.9E)
# ==========================================


class TestEntidades:

    def test_con_sobre_memory(self):
        for ask in (
            "que paso con kanye ayer",
            "que paso sobre kanye ayer",
            "que hubo con kanye ayer",
        ):
            r = _classify(ask)
            assert r.intent == MEMORY_SEARCH, ask

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_que_hubo_con_kanye_ayer(
        self, mock_env, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_env.return_value = {"memories": [
            _mem("k", _day_back(1),
                 "Kanye ayer dio un show"),
        ]}
        calls, orig = _no_memory_search()
        try:
            ctx = ConversationContext()
            r = think("que hubo con kanye ayer",
                      context=ctx)
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig
        assert "Kanye" in r
        assert r != "OLLAMA"
        assert mock_oa.call_count == 0
        assert calls["n"] == 1


# ==========================================
# F. ANTI-REGRESIÓN 8.11 (negadas/embebidas)
# ==========================================


class TestAntiRegresion811:

    def test_negadas_no_historia_no_memoria(self):
        for ask in NEGADAS_EMBEBIDAS:
            r = _classify(ask)
            assert r.intent == FREE_TALK, ask

    @patch("brain.core.ask_ollama")
    def test_negadas_siguen_ollama_legitimo(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        for ask in NEGADAS_EMBEBIDAS:
            before = mock_oa.call_count
            ctx = ConversationContext()
            r = think(ask, context=ctx)
            assert r == "OLLAMA", ask
            assert "Inicio de la d" not in r, ask
            assert "No tengo memorias" not in r, ask
            assert mock_oa.call_count == before + 1, ask


# ==========================================
# G. DETERMINISMO / SINGLE-PASS / GATE
# ==========================================


class TestDeterminismo:

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_gate_memory_no_sirve_events(
        self, mock_env, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_env.return_value = {"memories": [
            _mem("m", _day_back(6),
                 "algo de hace 6 dias"),
        ]}
        calls, orig = _no_memory_search()
        try:
            r = think("que paso ayer",
                      context=ConversationContext())
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig
        assert "No tengo memorias registradas." in r
        assert "Inicio de la d" not in r
        assert mock_oa.call_count == 0
        assert calls["n"] == 1