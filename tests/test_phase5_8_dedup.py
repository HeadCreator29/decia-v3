"""
PHASE 5.8 — Archive Result Quality & Execution Trace
Covers: deduplication, cap note, no-result rule,
execution trace clarity, and no-ollama guarantee.
"""
import sys
import json
import shutil
import pytest

from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "app"),
)

from unittest.mock import patch

from services.archive import (
    search_archive,
    get_memories,
    ARCHIVE_PATH,
)
from brain.core import think
from brain.handlers import (
    format_archive_response,
)
from brain.context import ConversationContext

from brain.intent_types import (
    ARCHIVE_SEARCH,
)


MEMORIES_PATH = ARCHIVE_PATH / "memories.json"
BACKUP_PATH = ARCHIVE_PATH / "memories.json.bak"


def write_memories(entries):
    MEMORIES_PATH.write_text(
        json.dumps(
            {"memories": entries},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


@pytest.fixture
def memories_env():
    if MEMORIES_PATH.exists():
        shutil.copy2(MEMORIES_PATH, BACKUP_PATH)
    yield
    if BACKUP_PATH.exists():
        shutil.copy2(BACKUP_PATH, MEMORIES_PATH)
        BACKUP_PATH.unlink()


def mem(date, desc, mem_id, time=None):
    return {
        "id": mem_id,
        "timestamp": f"{date}T12:00:00",
        "date": date,
        "time": time,
        "type": "actividad",
        "title": "Memoria de DECIA",
        "description": desc,
    }


# ==========================================
# 1. ARCHIVO CON REGISTROS DUPLICADOS
# ==========================================


class TestDeduplication:

    def test_exact_duplicates_collapse(
        self, memories_env,
    ):
        """5x mismo contenido lógico → 1."""
        write_memories([
            mem("2026-08-27",
                "quiero terminar decia", f"a{i}")
            for i in range(5)
        ])
        results = search_archive("que recuerdas")
        memories = [
            r for r in results
            if r["type"] == "memory"
        ]
        assert memories
        data = memories[0]["data"]
        assert len(data) == 1
        assert data[0]["description"] == (
            "quiero terminar decia"
        )

    def test_file_keeps_original_records(
        self, memories_env,
    ):
        """La deduplicación NO borra del archivo."""
        write_memories([
            mem("2026-08-27",
                "quiero terminar decia", f"a{i}")
            for i in range(5)
        ])
        search_archive("que recuerdas")
        assert len(
            get_memories()["memories"]
        ) == 5

    def test_case_insensitive_dedup(
        self, memories_env,
    ):
        write_memories([
            mem("2026-08-27", "DECIA",
                "a1"),
            mem("2026-08-27", "decia",
                "a2"),
        ])
        results = search_archive("que recuerdas")
        memories = [
            r for r in results
            if r["type"] == "memory"
        ]
        assert len(memories[0]["data"]) == 1

    def test_same_desc_different_dates_kept(
        self, memories_env,
    ):
        """Misma descripción en fechas distintas
        NO es duplicado (línea distinta)."""
        write_memories([
            mem("2026-08-26", "reunion",
                "a1"),
            mem("2026-08-27", "reunion",
                "a2"),
        ])
        results = search_archive("que recuerdas")
        memories = [
            r for r in results
            if r["type"] == "memory"
        ]
        assert len(memories[0]["data"]) == 2

    def test_same_date_different_desc_kept(
        self, memories_env,
    ):
        """Se preserva información legítimamente
        distinta que comparte fecha."""
        write_memories([
            mem("2026-08-27",
                "quiero terminar decia", "a1"),
            mem("2026-08-27",
                "quiero terminar decia esta semana",
                "a2"),
        ])
        results = search_archive("que recuerdas")
        memories = [
            r for r in results
            if r["type"] == "memory"
        ]
        data = memories[0]["data"]
        assert len(data) == 2
        descriptions = {
            m["description"] for m in data
        }
        assert descriptions == {
            "quiero terminar decia",
            "quiero terminar decia esta semana",
        }

    def test_multiple_legitimate_results(
        self, memories_env,
    ):
        write_memories([
            mem("2026-08-27",
                "mi color favorito es azul", "a1"),
            mem("2026-08-27",
                "me gusta la musica de kanye", "a2"),
            mem("2026-08-27",
                "mi perro se llama max", "a3"),
        ])
        results = search_archive("que recuerdas")
        memories = [
            r for r in results
            if r["type"] == "memory"
        ]
        data = memories[0]["data"]
        assert len(data) == 3
        assert {
            m["description"] for m in data
        } == {
            "mi color favorito es azul",
            "me gusta la musica de kanye",
            "mi perro se llama max",
        }


# ==========================================
# 2. LÍMITE DE RESULTADOS
# ==========================================


class TestResultLimit:

    def test_cap_indicates_more_available(
        self, memories_env,
    ):
        write_memories([
            mem("2026-08-27", f"memoria {i}",
                f"a{i}")
            for i in range(25)
        ])
        results = search_archive("que recuerdas")
        memories = [
            r for r in results
            if r["type"] == "memory"
        ]
        data = memories[0]["data"]
        assert len(data) == 20
        assert memories[0]["total"] == 25

    def test_cap_note_in_response(
        self, memories_env,
    ):
        write_memories([
            mem("2026-08-27", f"memoria {i}",
                f"a{i}")
            for i in range(25)
        ])
        results = search_archive("que recuerdas")
        memories = [
            r for r in results
            if r["type"] == "memory"
        ]
        response = format_archive_response(
            memories[0]
        )
        assert "y 5 más." in response
        assert response.startswith("2026-08-27")

    def test_no_note_below_limit(
        self, memories_env,
    ):
        write_memories([
            mem("2026-08-27", "memoria",
                "a0"),
        ])
        results = search_archive("que recuerdas")
        memories = [
            r for r in results
            if r["type"] == "memory"
        ]
        response = format_archive_response(
            memories[0]
        )
        assert "más" not in response


# ==========================================
# 3. ARCHIVE_SEARCH NO TERMINA EN OLLAMA
# ==========================================


class TestNoOllama:

    @patch("brain.core.ask_ollama")
    def test_no_result_no_ollama(self, mock_oa):
        mock_oa.return_value = "OLLAMA"
        ctx = ConversationContext(max_turns=10)
        r = think(
            "que hay registrado sobre zzz",
            context=ctx,
        )
        assert r == (
            "No encontré información "
            "registrada sobre zzz."
        )
        mock_oa.assert_not_called()

    @patch("brain.core.ask_ollama")
    def test_accepted_archive_search_executes(
        self, mock_oa, memories_env,
    ):
        write_memories([
            mem("2026-08-27",
                "quiero terminar decia", "a0"),
        ])
        mock_oa.return_value = "OLLAMA"
        ctx = ConversationContext(max_turns=10)
        r = think(
            "que hay registrado sobre deca",
            context=ctx,
        )
        assert "OLLAMA" not in r
        assert "quiero terminar decia" in r
        mock_oa.assert_not_called()


# ==========================================
# 4. TRAZA DE EJECUCIÓN
# ==========================================


class TestExecutionTrace:

    @patch("brain.core.ask_ollama")
    def test_trace_stages_clear(
        self, mock_oa, capsys,
    ):
        ctx = ConversationContext(max_turns=10)
        think(
            "que hay registrado sobre deca",
            context=ctx,
        )
        output = capsys.readouterr().out

        assert (
            "intent=ARCHIVE_SEARCH" in output
        )
        assert (
            "INTENT ACCEPTED -> "
            "ARCHIVE_SEARCH" in output
        )
        assert "EXECUTOR USED" in output
        assert (
            "Ruta: BÚSQUEDA ARCHIVO/MEMORIA"
            in output
        )

    @patch("brain.core.ask_ollama")
    def test_below_threshold_log_no_executor(
        self, mock_oa, capsys,
    ):
        """'below_threshold' es la decisión del
        clasificador; la traza muestra que el
        executor sí se usó después."""
        ctx = ConversationContext(max_turns=10)
        think(
            "que hay registrado sobre zzz",
            context=ctx,
        )
        output = capsys.readouterr().out

        assert "reason=below_threshold" in output
        assert "EXECUTOR USED" in output
        assert "INTENT ACCEPTED" in output
        mock_oa.assert_not_called()