"""
PHASE 8.18 — GUARDAS DE HARDENING DE RELOJ (solo capa de tests)

Garantiza las invariantes del reloj determinista nuevo:

  1. `@_seed_clock` congela los relojes que consume el código
     ejecutado (services.archive, utils.date_parser y el módulo
     del test) en la fecha semilla 2026-08-27T12:00:00-04:00.
  2. La consulta temporal real bajo `@_seed_clock` es
     determinista y anclada al seed (independiente del
     calendario real del host).
  3. data/archive/memories.json permanece en baseline
     (141 entradas, SHA256 04592D89...) — sin persistencia real.

No modifica producción, thresholds, TIL, clasificación ni datos.
"""
import hashlib
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "app"),
)

from unittest.mock import patch

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent),
)

from _seed_clock import _seed_clock, SEED_NOW

from brain.core import think
from brain.context import ConversationContext

SEED_DATE = SEED_NOW.date()
SEED_MONDAY = SEED_DATE - timedelta(days=SEED_DATE.weekday())

# Fechas de "host" que descorrelacionan la ventana del seed
# (documentación del porqué del freezing; checks estáticos).
# NOTA: 2026-08-29 cae DENTRO de la semana del seed (24..30),
# por lo que no se usa en este chequeo de ventana.
HOST_DATES_INVENTORY = (
    "2026-09-01",
    "2026-06-15",
    "2027-01-15",
)


class TestSeedClockGuards:

    @_seed_clock
    def test_reloj_nucleo_y_modulo_anclados_al_seed(self):
        import services.archive as sa
        import utils.date_parser as dp

        assert sa.datetime.now().date() == SEED_DATE
        assert dp.datetime.now().date() == SEED_DATE
        assert datetime.now().date() == SEED_DATE

        assert SEED_MONDAY.isoformat() == "2026-08-24"
        assert (
            SEED_MONDAY + timedelta(days=6)
        ).isoformat() == "2026-08-30"

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_consulta_temporal_anclada_y_determinista(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        ctx = ConversationContext()
        r1 = think("que hice esta semana", context=ctx)
        assert r1
        assert "No tengo memorias registradas." \
            not in r1
        assert r1 != "OLLAMA"
        assert mock_oa.call_count == 0

        r2 = think(
            "que hice esta semana",
            context=ConversationContext(),
        )
        assert r2 == r1

    def test_fechas_host_del_inventario_fueran_de_la_semana_seed(
        self,
    ):
        semantics_week_end = SEED_MONDAY + timedelta(days=7)
        for host_iso in HOST_DATES_INVENTORY:
            host = datetime.fromisoformat(
                host_iso + "T12:00:00-04:00"
            ).date()
            assert not (
                SEED_MONDAY <= host < semantics_week_end
            ), host_iso


class TestIntegridadMemories:

    def test_memories_en_baseline_sin_persistencia(self):
        path = (
            Path(__file__).resolve().parents[1]
            / "data" / "archive" / "memories.json"
        )
        raw = path.read_bytes()
        doc = json.loads(raw)
        assert len(doc["memories"]) == 141
        digest = hashlib.sha256(raw).hexdigest().upper()
        assert digest == (
            "04592D897665F175E44884926D4F2FC8D2DC4"
            "DD019970F550F77B3C1FDF0F9FE"
        )