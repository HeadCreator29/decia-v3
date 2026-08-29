"""
PHASE 5.10 — MEMORY_CREATE EXECUTION AUDIT
Ensures MEMORY_CREATE reaches its executor even when the
voice transcription prepends the assistant name
(e.g. "Desee, recuerda que ..."), and never falls to OLLAMA.
"""
import sys
import io
import json
import shutil
import contextlib
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from services.archive import (
    ARCHIVE_PATH,
    save_memory,
    get_memories,
)
from brain.intent_layer import IntentLayer
from brain.context import ConversationContext
from brain.core import think

MEMORIES_PATH = ARCHIVE_PATH / "memories.json"
BACKUP_PATH = ARCHIVE_PATH / "memories.json.bak"

_TRIGGER_PHRASE = (
    "Desee, recuerda que quiero terminar DECIA esta semana"
)
_ENTITY_TEXT = "quiero terminar decia esta semana"


@pytest.fixture(autouse=True)
def memories_env():
    if MEMORIES_PATH.exists():
        shutil.copy2(MEMORIES_PATH, BACKUP_PATH)
    yield
    if BACKUP_PATH.exists():
        shutil.copy2(BACKUP_PATH, MEMORIES_PATH)
        BACKUP_PATH.unlink()
    elif MEMORIES_PATH.exists():
        MEMORIES_PATH.unlink()


def write_memories(entries):
    MEMORIES_PATH.write_text(
        json.dumps({"memories": entries}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def run_think(message):
    ctx = ConversationContext(max_turns=10)
    buf = io.StringIO()
    with patch(
        "brain.core.ask_ollama",
        return_value="OLLAMA_REPLY",
    ) as m, contextlib.redirect_stdout(buf):
        response = think(message, context=ctx)
    return response, buf.getvalue(), m


def _count(desc):
    result = get_memories()
    return sum(
        1 for m in result.get("memories", [])
        if m.get("description") == desc
    )


class TestIntentDetection:

    def test_memory_create_detectado(self):
        il = IntentLayer()
        r = il.classify(_TRIGGER_PHRASE)
        assert r.intent == "MEMORY_CREATE"
        assert r.confidence == 1.0
        assert r.matched_pattern == "recuerda que"
        assert r.entities.get("memory") == _ENTITY_TEXT


class TestExecutionReachesExecutor:

    def test_memory_create_aceptado(self):
        _, out, _ = run_think(_TRIGGER_PHRASE)
        assert "INTENT ACCEPTED -> MEMORY_CREATE" in out
        assert "EXECUTOR USED" in out
        assert "Ruta: NUEVA MEMORIA" in out

    def test_create_memory_ejecutado(self):
        _, out, _ = run_think(_TRIGGER_PHRASE)
        assert "CREATE_MEMORY" in out
        assert f"description=\"{_ENTITY_TEXT}\"" in out

    def test_save_memory_ejecutado(self):
        write_memories([])
        _, out, _ = run_think(_TRIGGER_PHRASE)
        assert "SAVE_MEMORY | result=created" in out

    def test_no_llega_a_ollama(self):
        write_memories([])
        response, _, mocked = run_think(_TRIGGER_PHRASE)
        assert not mocked.called
        assert "Lo recordaré." in response

    def test_memoria_nueva_persistida(self):
        write_memories([])
        run_think(_TRIGGER_PHRASE)
        assert _count(_ENTITY_TEXT) == 1

    def test_traza_completa(self):
        write_memories([])
        _, out, _ = run_think(_TRIGGER_PHRASE)
        assert "intent=MEMORY_CREATE" in out
        assert "INTENT ACCEPTED -> MEMORY_CREATE" in out
        assert "EXECUTOR USED | Ruta: NUEVA MEMORIA" in out
        assert "CREATE_MEMORY" in out
        assert "SAVE_MEMORY | result=created" in out

    def test_invalidates_context(self):
        ctx = ConversationContext(max_turns=10)
        buf = io.StringIO()
        with patch(
            "brain.core.ask_ollama",
            return_value="OLLAMA_REPLY",
        ), contextlib.redirect_stdout(buf):
            think(_TRIGGER_PHRASE, context=ctx)
        assert ctx.last_intent is None


class TestDuplicateBehaviour:

    def test_duplicado_mismo_dia_rechazado(self):
        write_memories([])
        response_1, out_1, _ = run_think(_TRIGGER_PHRASE)
        response_2, out_2, mocked = run_think(_TRIGGER_PHRASE)
        assert "Lo recordaré." in response_1
        assert "Ya tengo esa memoria registrada" in response_2
        assert "SAVE_MEMORY | result=duplicate" in out_2
        assert not mocked.called
        assert _count(_ENTITY_TEXT) == 1

    def test_no_doble_escritura(self):
        write_memories([])
        run_think(_TRIGGER_PHRASE)
        run_think(_TRIGGER_PHRASE)
        assert _count(_ENTITY_TEXT) == 1

    def test_misma_descripcion_fecha_diferente_permitida(self):
        write_memories([])
        r1 = save_memory({
            "id": "p510_d1",
            "description": _ENTITY_TEXT,
            "date": "2026-08-26",
            "type": "actividad",
        })
        r2 = save_memory({
            "id": "p510_d2",
            "description": _ENTITY_TEXT,
            "date": "2026-08-27",
            "type": "actividad",
        })
        assert r1 is True
        assert r2 is True
        assert _count(_ENTITY_TEXT) == 2