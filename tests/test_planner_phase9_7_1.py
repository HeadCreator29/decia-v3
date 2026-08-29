"""
PHASE 9.7.1 - PLANNER HARDENING FIXES (F1-F4)

Correcciones quirurgicas sobre PHASE 9.6 (baseline 2615 passed):

  F1  "de la mañana" con ñ: "a las 7 de la mañana" -> 07:00
      (antes 19:00) y la hora no contamina la descripcion.
      Acepta "mañana" y "manana" (ma[nñ]ana).
  F2  Fecha absoluta > weekday en plan_relative_datetime:
      "2026-08-30 lunes" -> 2026-08-30 (antes 08-31).
  F3  PLANNER_CREATE ya no roba MEMORY_SEARCH en frases de
      recuperacion ("recuerdame algo sobre mañana", "lo de",
      "que te dije", "memorias", "recuerdos", ...).
  F4  Prefijos "el"/"para" en PLANNER_QUERY ("que tengo el
      manana", "que tengo para 2026-08-30", ...).

Invariantes: 0 llamadas OLLAMA en rutas planner; persistencia
solo via tmp_path + monkeypatch (PLANNER_PATH); no se tocan
memories/user/history; planning dedicado fase 9.6 intacto.

NOTA: todos los literales no-ASCII usan escapes \\u para evitar
corrupcion de codificacion en el transporte del archivo.
"""
import sys
from datetime import timedelta
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent

sys.path.insert(0, str(TEST_DIR.parent / "app"))
sys.path.insert(0, str(TEST_DIR))

from unittest.mock import patch

from _seed_clock import _seed_clock, SEED_NOW

from brain.intent_layer import IntentLayer
from brain.core import think
from brain.context import ConversationContext

from brain.intent_types import (
    PLANNER_CREATE,
    PLANNER_QUERY,
    MEMORY_SEARCH,
    MEMORY_CREATE,
)

from utils.date_parser import (
    plan_relative_datetime,
    parse_relative_time,
)

import services.planner as sp

IL = IntentLayer()

SEED_DATE = SEED_NOW.date()

S_ACUERDO = "\u00bfPara cu\u00e1ndo? Dime la fecha."


def _classify(message):
    return IL.classify(message)


def _redirect_planner_file(monkeypatch, tmp_path):
    planner = tmp_path / "planner.json"
    planner.write_text(
        '{"plans": []}', encoding="utf-8"
    )
    monkeypatch.setattr(
        "services.planner.PLANNER_PATH", planner
    )
    monkeypatch.setattr(
        "services.planner._PLANNER_BACKUP",
        tmp_path / "planner.corrupt.backup.json",
    )
    return planner


# ==========================================
# F1 - "DE LA MAÑANA" CON Ñ
# ==========================================


class TestF1ParseRelativeTime:

    def test_fn_siete_de_la_manana(self):
        assert parse_relative_time(
            "ma\u00f1ana a las 7 de la "
            "ma\u00f1ana llamar al m\u00e9dico"
        ) == "07:00"

    def test_ascii_siete_de_la_manana(self):
        assert parse_relative_time(
            "manana a las 7 de la manana "
            "llamar al medico"
        ) == "07:00"

    def test_fn_siete_de_la_tarde(self):
        assert parse_relative_time(
            "ma\u00f1ana a las 7 de la "
            "tarde llamar al m\u00e9dico"
        ) == "19:00"

    def test_fn_siete_de_la_noche(self):
        assert parse_relative_time(
            "ma\u00f1ana a las 7 de la "
            "noche llamar al m\u00e9dico"
        ) == "19:00"

    def test_fn_nueve_de_la_manana(self):
        assert parse_relative_time(
            "ma\u00f1ana a las 9 de la ma\u00f1ana"
        ) == "09:00"

    def test_fn_nueve_de_la_tarde(self):
        assert parse_relative_time(
            "ma\u00f1ana a las 9 de la tarde"
        ) == "21:00"

    def test_paridad_trece_de_la_manana_fold(self):
        # 12 de la manana (ñ) == 12 de la manana (n):
        # ambos colapsan a medianoche (00:00).
        assert parse_relative_time(
            "a las 12 de la ma\u00f1ana"
        ) == parse_relative_time(
            "a las 12 de la manana"
        ) == "00:00"

    def test_old_semantica_intacta(self):
        # "a las 9" desnudo mantiene la regla
        # historica (1-7 -> pm).
        assert parse_relative_time("a las 9") \
            == "09:00"
        assert parse_relative_time("a las 3") \
            == "15:00"


class TestF1CreateThink:
    """Caso A end-to-end: hora + descripcion limpias."""

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_caso_a_reminder_fechayhora(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        _redirect_planner_file(monkeypatch, tmp_path)
        resp = think(
            "recu\u00e9rdame ma\u00f1ana a las 7 "
            "de la ma\u00f1ana llamar al "
            "m\u00e9dico",
            ConversationContext(),
        )
        assert resp == (
            "Perfecto. He registrado el "
            "recordatorio para 28 de agosto "
            "de 2026 a las 07:00."
        )
        assert mock_oa.call_count == 0
        plan = sp.load_plans()["plans"][0]
        assert plan["kind"] == "reminder"
        assert plan["due_date"] == "2026-08-28"
        assert plan["due_time"] == "07:00"
        assert plan["description"] == (
            "llamar al m\u00e9dico"
        )

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_ascii_variante(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        _redirect_planner_file(monkeypatch, tmp_path)
        resp = think(
            "manana a las 7 de la manana "
            "llamar al medico",
            ConversationContext(),
        )
        assert resp == (
            "Perfecto. He registrado el "
            "evento para 28 de agosto de 2026 "
            "a las 07:00."
        )
        assert mock_oa.call_count == 0
        plan = sp.load_plans()["plans"][0]
        assert plan["due_time"] == "07:00"
        assert plan["description"] == (
            "llamar al medico"
        )

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_nombre_ana_conservado(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        _redirect_planner_file(monkeypatch, tmp_path)
        resp = think(
            "llamar a Ana ma\u00f1ana a las 7 de "
            "la ma\u00f1ana",
            ConversationContext(),
        )
        assert resp == (
            "Perfecto. He registrado el "
            "evento para 28 de agosto de 2026 "
            "a las 07:00."
        )
        assert mock_oa.call_count == 0
        plan = sp.load_plans()["plans"][0]
        assert plan["description"] == (
            "llamar a Ana"
        )
        assert plan["due_time"] == "07:00"

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_tarde_noche(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        _redirect_planner_file(monkeypatch, tmp_path)
        think(
            "ma\u00f1ana a las 7 de la tarde "
            "reunion",
            ConversationContext(),
        )
        p1 = sp.load_plans()["plans"][0]
        assert p1["due_time"] == "19:00"
        assert p1["description"] == "reunion"
        think(
            "ma\u00f1ana a las 7 de la noche "
            "cena",
            ConversationContext(),
        )
        p2 = sp.load_plans()["plans"][-1]
        assert p2["due_time"] == "19:00"
        assert p2["description"] == "cena"
        assert mock_oa.call_count == 0


class TestF1FollowupTimeOnly:
    """F1-7: "a las 7 de la mañana" es time-only."""

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_followup_hora_de_la_manana(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        _redirect_planner_file(monkeypatch, tmp_path)
        ctx = ConversationContext()
        think("recu\u00e9rdame estudiar", ctx)
        think("manana", ctx)
        resp = think("a las 7 de la ma\u00f1ana", ctx)
        assert resp == (
            "Perfecto. Actualic\u00e9 la hora "
            "del recordatorio para 28 de "
            "agosto de 2026 a las 07:00."
        )
        assert mock_oa.call_count == 0
        plans = sp.load_plans()["plans"]
        assert len(plans) == 1
        assert plans[0]["description"] == "estudiar"
        assert plans[0]["due_time"] == "07:00"


# ==========================================
# F2 - FECHA ABSOLUTA > WEEKDAY
# ==========================================


class TestF2AbsoluteWins:

    @_seed_clock
    def test_absoluta_guion_despues_weekday(self):
        assert plan_relative_datetime(
            "tengo cita el 2026-08-30 lunes"
        ).isoformat() == "2026-08-30"

    @_seed_clock
    def test_absoluta_guion_antes_weekday(self):
        assert plan_relative_datetime(
            "lunes 2026-08-30"
        ).isoformat() == "2026-08-30"

    @_seed_clock
    def test_absoluta_barras(self):
        assert plan_relative_datetime(
            "2026/08/30 lunes"
        ).isoformat() == "2026-08-30"

    @_seed_clock
    def test_absoluta_compacta(self):
        assert plan_relative_datetime(
            "20260830 lunes"
        ).isoformat() == "2026-08-30"

    @_seed_clock
    def test_absoluta_contradice_weekday(self):
        # "2026-08-30" es domingo; "viernes" choca.
        # La fecha explicita SIEMPRE gana.
        assert plan_relative_datetime(
            "2026-08-30 viernes"
        ).isoformat() == "2026-08-30"

    @_seed_clock
    def test_viernes_regresion(self):
        # SEED = jueves 2026-08-27 -> viernes 28.
        expected = SEED_DATE + timedelta(days=1)
        assert plan_relative_datetime(
            "viernes"
        ) == expected
        assert plan_relative_datetime(
            "este viernes"
        ) == expected
        assert plan_relative_datetime(
            "el viernes"
        ) == expected

    @_seed_clock
    def test_viernes_pasado_regresion(self):
        assert plan_relative_datetime(
            "el viernes pasado"
        ) is None


class TestF2CasoBThink:

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_caso_b_absoluta_despues_weekday(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        _redirect_planner_file(monkeypatch, tmp_path)
        resp = think(
            "tengo cita el 2026-08-30 lunes",
            ConversationContext(),
        )
        assert resp == (
            "Perfecto. He registrado el evento "
            "para 30 de agosto de 2026."
        )
        assert mock_oa.call_count == 0
        plan = sp.load_plans()["plans"][0]
        assert plan["due_date"] == "2026-08-30"
        assert plan["due_time"] is None
        assert plan["description"] == "tengo cita el"


# ==========================================
# F3 - PLANNER_CREATE NO ROBA MEMORY_SEARCH
# ==========================================


class TestF3NoRobaMemory:

    def test_recuerdame_algo_sobre_memory(self):
        assert _classify(
            "recu\u00e9rdame algo sobre ma\u00f1ana"
        ).intent == MEMORY_SEARCH

    def test_recuerdame_lo_de_memory(self):
        assert _classify(
            "recu\u00e9rdame lo de ma\u00f1ana"
        ).intent == MEMORY_SEARCH

    def test_recuerdame_memorias_memory(self):
        assert _classify(
            "recu\u00e9rdame memorias de "
            "ma\u00f1ana"
        ).intent == MEMORY_SEARCH

    def test_recuerdame_que_te_dije_memory(self):
        assert _classify(
            "recu\u00e9rdame que te dije que "
            "tengo ma\u00f1ana"
        ).intent == MEMORY_SEARCH

    def test_recuerdame_lo_que_dije_memory(self):
        assert _classify(
            "recu\u00e9rdame lo que dije ma\u00f1ana"
        ).intent == MEMORY_SEARCH

    def test_recuerdame_que_me_dijiste_memory(
        self,
    ):
        assert _classify(
            "recu\u00e9rdame que me dijiste "
            "ma\u00f1ana comprar pan"
        ).intent == MEMORY_SEARCH

    def test_recuerdame_recuerdos_memory(self):
        # "recuerdos" es construccion protegida.
        assert _classify(
            "recu\u00e9rdame recuerdos de "
            "ma\u00f1ana"
        ).intent == MEMORY_SEARCH


class TestF3PositivosIntactos:

    def test_manana_tengo_clase_create(self):
        assert _classify(
            "ma\u00f1ana tengo clase"
        ).intent == PLANNER_CREATE

    def test_manana_estudiar_decia_create(self):
        assert _classify(
            "ma\u00f1ana estudiar DECIA"
        ).intent == PLANNER_CREATE

    def test_recuerdame_manana_estudiar_create(
        self,
    ):
        assert _classify(
            "recu\u00e9rdame ma\u00f1ana estudiar"
        ).intent == PLANNER_CREATE

    def test_recuerdame_manana_comprar_create(
        self,
    ):
        assert _classify(
            "recu\u00e9rdame ma\u00f1ana comprar "
            "material"
        ).intent == PLANNER_CREATE


class TestF3ContratosPreExistentes:

    def test_recuerdame_lo_que_hablamos_memory(
        self,
    ):
        assert _classify(
            "recu\u00e9rdame lo que hablamos hoy"
        ).intent == MEMORY_SEARCH

    def test_recuerda_ayer_fue_memory_create(
        self,
    ):
        assert _classify(
            "recuerda que ayer tuve clase"
        ).intent == MEMORY_CREATE

    def test_que_recuerdas_sobre_ayer_memory(
        self,
    ):
        assert _classify(
            "qu\u00e9 recuerdas sobre ayer"
        ).intent == MEMORY_SEARCH


# ==========================================
# F4 - PREFIJOS "EL" / "PARA" EN PLANNER_QUERY
# ==========================================


class TestF4QueryPrefijos:

    def test_que_tengo_manana(self):
        assert _classify(
            "qu\u00e9 tengo ma\u00f1ana"
        ).intent == PLANNER_QUERY

    def test_que_tengo_el_manana(self):
        assert _classify(
            "qu\u00e9 tengo el ma\u00f1ana"
        ).intent == PLANNER_QUERY

    def test_que_tengo_para_manana(self):
        assert _classify(
            "qu\u00e9 tengo para ma\u00f1ana"
        ).intent == PLANNER_QUERY

    def test_que_tengo_absoluta(self):
        assert _classify(
            "qu\u00e9 tengo 2026-08-30"
        ).intent == PLANNER_QUERY

    def test_que_tengo_el_absoluta(self):
        assert _classify(
            "qu\u00e9 tengo el 2026-08-30"
        ).intent == PLANNER_QUERY

    def test_que_tengo_para_absoluta(self):
        assert _classify(
            "qu\u00e9 tengo para 2026-08-30"
        ).intent == PLANNER_QUERY

    def test_que_hay_para_manana(self):
        assert _classify(
            "qu\u00e9 hay para ma\u00f1ana"
        ).intent == PLANNER_QUERY

    def test_que_tengo_el_lunes(self):
        assert _classify(
            "qu\u00e9 tengo el lunes"
        ).intent == PLANNER_QUERY


class TestF4NoRobo:

    def test_que_tengo_el_lunes_pasado_no_query(
        self,
    ):
        assert _classify(
            "qu\u00e9 tengo el lunes pasado"
        ).intent != PLANNER_QUERY

    def test_que_paso_el_lunes_no_planner(self):
        assert _classify(
            "qu\u00e9 pas\u00f3 el lunes"
        ).intent != PLANNER_QUERY
        assert _classify(
            "qu\u00e9 pas\u00f3 el lunes"
        ).intent != PLANNER_CREATE

    def test_que_hice_ayer_no_planner(self):
        assert _classify(
            "qu\u00e9 hice ayer"
        ).intent != PLANNER_QUERY
        assert _classify(
            "qu\u00e9 hice ayer"
        ).intent != PLANNER_CREATE

    def test_que_recuerdo_de_manana_memory(
        self,
    ):
        assert _classify(
            "qu\u00e9 recuerdo de ma\u00f1ana"
        ).intent == MEMORY_SEARCH


class TestF4CasoDThink:
    """Caso D end-to-end: determinista, 0 OLLAMA."""

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_que_tengo_para_manana_determinista(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        _redirect_planner_file(monkeypatch, tmp_path)
        ctx = ConversationContext()
        think("manana tengo clase", ctx)
        r1 = think("qu\u00e9 tengo para "
                   "ma\u00f1ana", ctx)
        r2 = think("qu\u00e9 tengo para "
                   "ma\u00f1ana", ctx)
        assert r1 == r2
        assert "tengo clase" in r1
        assert mock_oa.call_count == 0

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_que_tengo_para_absoluta_vacia(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        _redirect_planner_file(monkeypatch, tmp_path)
        resp = think(
            "qu\u00e9 tengo para 2026-08-30",
            ConversationContext(),
        )
        assert resp == (
            "No tengo planes registrados "
            "para 30 de agosto de 2026."
        )
        assert mock_oa.call_count == 0