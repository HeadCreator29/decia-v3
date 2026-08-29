"""
PHASE 8.13 — CONTEXTO G6 (HISTORIA GENERAL)

La ruta HISTORIA GENERAL (G6) responde desde ARCHIVE/HISTORY
con mode="archive"; el contexto interno ahora queda coherente:
last_intent=ARCHIVE_SEARCH junto a conversation_mode="archive"
(en lugar de la señal mixta last_intent=MEMORY_SEARCH). Así,
"y ayer" después de una desnuda NO hereda MEMORY por accidente.

Se preservan intactos: MEMORY temporal (contexto memory),
entidad kanye + temporal, ARCHIVE temporal/directo, follow-up
tras MEMORY ("y ayer", "y el lunes", "y la semana pasada"),
single-pass y 0 OLLAMA en rutas deterministas.
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
    ARCHIVE_DIRECT,
    ARCHIVE_SEARCH,
    MEMORY_SEARCH,
)

IL = IntentLayer()

NOW = datetime.now().astimezone()


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


def _search_wrap():
    from brain import core as coremod
    calls = {"n": 0}
    orig = coremod.search_deca_memory
    orig_search = orig

    def wrapped(msg, *args, **kwargs):
        calls["n"] += 1
        return orig_search(msg, *args, **kwargs)

    return calls, wrapped, coremod, orig


def _think_ctx(ctx, ask, memories=None, oa_ret="OLLAMA"):
    from unittest.mock import patch
    from unittest.mock import MagicMock
    oa = MagicMock(return_value=oa_ret)
    calls, wrapped, coremod, orig = _search_wrap()
    patches = [patch("brain.core.ask_ollama", oa)]
    if memories is not None:
        patches.append(
            patch("services.archive.get_memories",
                  return_value={"memories": memories})
        )
    for p in patches:
        p.start()
    coremod.search_deca_memory = wrapped
    try:
        r = think(ask, context=ctx)
        n_oa = oa.call_count
    finally:
        coremod.search_deca_memory = orig
        for p in patches:
            p.stop()
    return r, calls["n"], n_oa, ctx


ARCHIVE_SEARCH_VERBS = (
    "que paso",
    "que sucedio",
    "que ocurrio",
    "que hubo",
)


# ==========================================
# A. G6 BARE -> CONTEXTO COHERENTE CON
#    ARCHIVE (last_intent=ARCHIVE_SEARCH)
# ==========================================


class TestG6ContextoSemantico:

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_desnudas_contexto_archive(
        self, mock_env, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_env.return_value = {"memories": [
            _mem("r", _day_back(1),
                 "memoria personal"),
        ]}
        for ask in ARCHIVE_SEARCH_VERBS:
            calls, wrapped, coremod, orig = _search_wrap()
            with patch(
                "brain.core.ask_ollama", mock_oa
            ):
                coremod.search_deca_memory = wrapped
                ctx = ConversationContext()
                try:
                    r = think(ask, context=ctx)
                finally:
                    coremod.search_deca_memory = orig
            assert "Inicio de la d" in r, ask
            assert ctx.last_intent == ARCHIVE_SEARCH, ask
            assert ctx.conversation_mode == "archive", ask
            assert ctx.last_entity is None, ask
            assert calls["n"] == 0, ask
            assert mock_oa.call_count == 0, ask


# ==========================================
# B. MEMORY TEMPORAL -> CONTEXTO MEMORY
# ==========================================


class TestMemoryContexto:

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_que_paso_ayer_contexto_memory(
        self, mock_env, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_env.return_value = {"memories": [
            _mem("a", _day_back(1),
                 "record poderosa para seguir"),
        ]}
        r, n, oa_n, ctx = _think_ctx(
            ConversationContext(), "que paso ayer",
            memories=mock_env.return_value["memories"],
        )
        assert "record poderosa" in r
        assert ctx.last_intent == MEMORY_SEARCH
        assert ctx.conversation_mode == "memory"
        assert ctx.last_entity is None
        assert n == 1
        assert oa_n == 0


# ==========================================
# C. ENTIDAD + TEMPORAL (G7)
# ==========================================


class TestEntidadContexto:

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_con_kanye_ayer_entity_kanye(
        self, mock_env, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_env.return_value = {"memories": [
            _mem("k", _day_back(1),
                 "conversacion con kanye"),
        ]}
        r, n, oa_n, ctx = _think_ctx(
            ConversationContext(), "que paso con kanye ayer",
            memories=mock_env.return_value["memories"],
        )
        assert "kanye" in r.lower()
        assert ctx.last_intent == MEMORY_SEARCH
        assert ctx.conversation_mode == "memory"
        assert ctx.last_entity == "kanye"
        assert n == 1
        assert oa_n == 0


# ==========================================
# D. ARCHIVE TEMPORAL -> CONTEXTO ARCHIVE
# ==========================================


class TestArchiveContexto:

    @patch("brain.core.ask_ollama")
    def test_eventos_deca_ayer_contexto_archive(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        r, n, oa_n, ctx = _think_ctx(
            ConversationContext(),
            "que eventos de deca hubo ayer",
        )
        assert ctx.last_intent == ARCHIVE_SEARCH
        assert ctx.conversation_mode == "archive"
        assert ctx.last_entity is None
        assert n == 1
        assert oa_n == 0

    @patch("brain.core.ask_ollama")
    def test_archivo_directo_conserva_intent(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        r, n, oa_n, ctx = _think_ctx(
            ConversationContext(), "que es deca",
        )
        assert r
        assert ctx.last_intent == ARCHIVE_DIRECT
        assert ctx.conversation_mode == "archive"
        assert n == 0
        assert oa_n == 0


# ==========================================
# E. FOLLOW-UP TRAS MEMORY (intacto)
# ==========================================


class TestFollowUpMemory:

    FOLS = ("y el lunes", "y la semana pasada")

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_follow_up_temporales_siguen_memory(
        self, mock_env, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_env.return_value = {"memories": [
            _mem("a", _day_back(1),
                 "mi color favorito fue amarillo"),
        ]}
        for fu in ("y ayer",) + self.FOLS:
            ctx = ConversationContext()
            _think_ctx(
                ctx, "que paso ayer",
                memories=mock_env.return_value["memories"],
            )
            r, n, oa_n, ctx = _think_ctx(ctx, fu)
            assert r, fu
            assert r != "OLLAMA", fu
            assert n == 1, fu
            assert oa_n == 0, fu

    @patch("brain.core.ask_ollama")
    @_seed_clock
    def test_follow_up_y_ayer_tras_memory_responde(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        ctx = ConversationContext()
        _think_ctx(
            ctx, "que paso ayer",
            memories=[_mem("a", _day_back(1),
                           "mi color favorito")],
        )
        r, n, oa_n, ctx = _think_ctx(ctx, "y ayer")
        assert "color favorito" in r
        assert ctx.conversation_mode == "memory"
        assert n == 1


# ==========================================
# F. FOLLOW-UP TRAS HISTORY: NO HEREDA
#    MEMORY POR ACCIDENTE
# ==========================================


class TestFollowUpHistory:

    @patch("brain.core.ask_ollama")
    def test_no_hereda_memory_tras_desnuda(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        ctx = ConversationContext()
        r0, n0, oa0, ctx = _think_ctx(ctx, "que paso")
        assert ctx.last_intent == ARCHIVE_SEARCH
        assert ctx.conversation_mode == "archive"
        r, n, oa_n, ctx = _think_ctx(ctx, "y ayer")
        assert "necesitas" in r
        assert "color favorito" not in r
        assert "Inicio de la d" not in r
        assert n == 0
        assert oa_n == 0

    @patch("brain.core.ask_ollama")
    def test_y_el_lunes_no_hereda_memoria(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        ctx = ConversationContext()
        _think_ctx(ctx, "que paso")
        r, n, oa_n, ctx = _think_ctx(ctx, "y el lunes")
        assert "No tengo memorias" not in r
        assert "color favorito" not in r
        assert "Inicio de la d" not in r
        assert ctx.conversation_mode != "memory"
        assert oa_n == 0


# ==========================================
# G. SINGLE-PASS / 0 OLLAMA (verificado en
#    secciones A-D vía _think_ctx)
# ==========================================