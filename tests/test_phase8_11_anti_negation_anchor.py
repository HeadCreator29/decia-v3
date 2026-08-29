"""
PHASE 8.11 — ANTI-NEGATION / EMBEDDED HISTORICAL ANCHOR

Corrige el falso positivo (P3) de Phase 8.10: la consulta
histórica "desnuda" ("que paso" / "q paso") debe ocupar la
TOTALIDAD del mensaje después de normalize_strict. El
patrón MEMORY_SEARCH "que paso" se fijó como EXACT (ya no
casa por substring), por lo que frases embebidas o negadas
("no me digas que paso", "que paso cuando llegue") dejan de
entrar en HISTORY/MEMORY y vuelven a su ruta legítima
(FREE_TALK/OLLAMA o AMBIGUA).

Se conservan intactos: G6 (desnudas -> ARCHIVE/HISTORY),
temporales 8.9A-8.9E, G7 (entidad limpia), con/sobre 8.9E,
ARCHIVE temporal 8.9C, clasificación "que paso" -> MEMORY
(0.60), single-pass y gate field=="memories".
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
    AMBIGUOUS_INPUT,
    ARCHIVE_SEARCH,
    FREE_TALK,
    MEMORY_SEARCH,
)

IL = IntentLayer()

NOW = datetime.now().astimezone()


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


# Válidos: la consulta histórico-desnuda ocupa TODO el
# mensaje (post normalize_strict). Variantes de acento,
# mayúsculas, "q", puntuación y espacios.
BARE_VALIDOS = (
    "que paso",
    "q paso",
    "qué pasó",
    "Que Pasó",
    "QUE PASO",
    "¿Qué pasó?",
    "que paso!",
    "que  paso  ?",
    "q  PASO",
)


# Inválidos: "que paso" embebido o negado NO constituye
# la consulta desnuda. "que paso cuando llegue" se movió
# a near-bare histórico ambiguo (8.12) y ya no se cubre
# aquí.
EMBEDDED = (
    "no me digas que paso",
    "si que paso",
    "dime que paso cuando llegue",
    "que paso manana",
)

PORQUE_PASO = "porque paso"


# ==========================================
# A. HISTORY BARE VÁLIDO (G6) — ANCLAJE TOTAL
# ==========================================


class TestHistoryBareAnclado:

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_consultas_validas_siguen_history(
        self, mock_env, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_env.return_value = {"memories": [
            _mem("r", _day_back(1),
                 "memoria personal real"),
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
            assert "memoria personal real" not in r, ask
            assert "No tengo memorias" not in r, ask
            assert r != "OLLAMA", ask
            assert mock_oa.call_count == 0, ask
            assert calls["n"] == 0, ask
            assert ctx.conversation_mode == "archive", ask

    def test_que_paso_sigue_memory_060(self):
        r = _classify("que paso")
        assert r.intent == MEMORY_SEARCH
        assert r.confidence == 0.60


# ==========================================
# B. NEGACIONES / EMBEBIDAS: FUERA DE
#    HISTORY/MEMORY (ruta legítima)
# ==========================================


class TestNegacionesYEmbedded:

    def test_embedded_no_son_memory_en_til(self):
        for ask in EMBEDDED:
            r = _classify(ask)
            assert r.intent != MEMORY_SEARCH, ask
            assert r.intent == FREE_TALK, ask

    def test_porque_paso_es_ambiguo(self):
        r = _classify(PORQUE_PASO)
        assert r.intent == AMBIGUOUS_INPUT

    @patch("brain.core.ask_ollama")
    def test_embedded_no_entran_en_history_memory(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        for ask in EMBEDDED:
            before = mock_oa.call_count
            ctx = ConversationContext()
            r = think(ask, context=ctx)
            assert r == "OLLAMA", ask
            assert "Inicio de la d" not in r, ask
            assert "Nacimiento de DECIA" not in r, ask
            assert "No tengo memorias" not in r, ask
            assert mock_oa.call_count == before + 1, ask

    @patch("brain.core.ask_ollama")
    def test_no_margin_con_busquedas_ni_memoria(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        for ask in EMBEDDED[:2]:
            calls, orig = _no_memory_search()
            try:
                think(ask, context=ConversationContext())
            finally:
                import brain.core as coremod
                coremod.search_deca_memory = orig
            assert calls["n"] == 0, ask

    @patch("brain.core.ask_ollama")
    def test_porque_paso_es_clarificacion(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        r = think(PORQUE_PASO,
                  context=ConversationContext())
        assert "necesitas" in r
        assert "Inicio de la d" not in r
        assert "No tengo memorias" not in r
        assert mock_oa.call_count == 0


# ==========================================
# C. REGRESIÓN: TEMPORALES, ENTIDAD+SOBRE,
#    ARCHIVE TEMPORAL
# ==========================================


class TestRegresionTemporal:

    def test_memory_temporal_intacto(self):
        for ask in (
            "que paso ayer",
            "que paso anteayer",
            "que paso el lunes",
            "que paso la semana pasada",
            "que paso con kanye ayer",
            "que paso sobre kanye ayer",
        ):
            r = _classify(ask)
            assert r.intent == MEMORY_SEARCH, ask

    def test_archive_temporal_intacto(self):
        r = _classify(
            "que eventos de deca hubo la semana pasada"
        )
        assert r.intent == ARCHIVE_SEARCH
        assert r.confidence >= 0.50

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_que_paso_ayer_ejecuta_memory(
        self, mock_env, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_env.return_value = {"memories": [
            _mem("a", _day_back(1),
                 "recorde algo importante ayer"),
        ]}
        calls, orig = _no_memory_search()
        try:
            ctx = ConversationContext()
            r = think("que paso ayer", context=ctx)
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig
        assert "recorde algo importante ayer" in r
        assert "Inicio de la d" not in r
        assert mock_oa.call_count == 0
        assert calls["n"] == 1
        assert ctx.conversation_mode == "memory"

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_que_paso_con_kanye_ayer(self,
                                     mock_env,
                                     mock_oa):
        mock_oa.return_value = "OLLAMA"
        mock_env.return_value = {"memories": [
            _mem("k", _day_back(1),
                 "Kanye ayer se presento en vivo"),
        ]}
        calls, orig = _no_memory_search()
        try:
            ctx = ConversationContext()
            r = think("que paso con kanye ayer",
                      context=ctx)
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig
        assert "Kanye" in r
        assert "kanye ayer" not in r
        assert r != "OLLAMA"
        assert mock_oa.call_count == 0
        assert calls["n"] == 1

    @patch("brain.core.ask_ollama")
    @_seed_clock
    def test_archive_temporal_determinista(self,
                                           mock_oa):
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
# D. DETERMINISMO Y GATE
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
            ctx = ConversationContext()
            r = think("que paso ayer", context=ctx)
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig
        assert "No tengo memorias registradas." in r
        assert "Inicio de la d" not in r
        assert mock_oa.call_count == 0
        assert calls["n"] == 1

    def test_single_pass_archive(self):
        calls, orig = _no_memory_search()
        try:
            think(
                "que eventos de deca hubo la semana pasada",
                context=ConversationContext(),
            )
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig
        assert calls["n"] == 1