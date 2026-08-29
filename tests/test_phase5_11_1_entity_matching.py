"""
PHASE 5.11.1 — ENTITY MATCHING FIX
The substring branch of _entity_word_matches() must not match
short words (len < 3) embedded in a longer entity/haystack word.
Broken example (pre-fix): entity "este" version "es" ∈ "mi color
favorito es azul" via "es" in "este".
"""
import sys
import json
import shutil
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from services.archive import ARCHIVE_PATH
from brain.handlers import (
    _entity_word_matches,
    filter_memories_by_entity,
)

MEMORIES_PATH = ARCHIVE_PATH / "memories.json"
BACKUP_PATH = ARCHIVE_PATH / "memories.json.bak"


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


def _mem_dict(desc, date="2026-08-27"):
    return {
        "id": "m_" + desc.replace(" ", "_"),
        "description": desc,
        "title": "Memoria de DECIA",
        "date": date,
        "type": "actividad",
    }


class TestSubstringGuard:

    def test_este_no_matches_memoria_con_es(self):
        assert not _entity_word_matches(
            "este", "mi color favorito es azul memoria de decia 2026-08-26"
        )

    def test_esta_no_false_positivo_con_es(self):
        assert not _entity_word_matches(
            "esta", "mi color favorito es azul"
        )

    def test_substring_legit_3_o_mas(self):
        assert _entity_word_matches(
            "sol", "el sol es brillante"
        )

    def test_exacto_palabra_corta_sigue_funcionando(self):
        assert _entity_word_matches(
            "es", "mi color favorito es azul"
        )


class TestStrategiesIntact:

    def test_lcp_existente_sigue_funcionando(self):
        assert _entity_word_matches(
            "deca", "quiero terminar decia"
        )

    def test_deca_decia_conserva_phase_5_8(self):
        result = filter_memories_by_entity(
            {
                "type": "memory",
                "field": "memories",
                "data": [_mem_dict("quiero terminar DECIA")],
            },
            "deca",
        )
        assert result is not None
        assert len(result["data"]) == 1

    def test_entidad_real_devuelve_sus_memorias(self):
        result = filter_memories_by_entity(
            {
                "type": "memory",
                "field": "memories",
                "data": [
                    _mem_dict("me gusta la musica de Kanye"),
                    _mem_dict("mi perro se llama Max"),
                ],
            },
            "kanye",
        )
        assert result is not None
        descs = [m["description"] for m in result["data"]]
        assert "me gusta la musica de Kanye" in descs
        assert "mi perro se llama Max" not in descs


class TestEndToEndEste:

    def test_sobre_este_no_devuelve_irrelevantes(self):
        memories = [
            _mem_dict("mi color favorito es azul"),
            _mem_dict("mi color favorito es rojo"),
            _mem_dict("quiero terminar decia esta semana"),
            _mem_dict("me gusta la musica de Kanye"),
        ]
        result = filter_memories_by_entity(
            {
                "type": "memory",
                "field": "memories",
                "data": memories,
            },
            "este",
        )
        if result is not None:
            descs = [m["description"] for m in result["data"]]
            assert "mi color favorito es azul" not in descs
            assert "mi color favorito es rojo" not in descs