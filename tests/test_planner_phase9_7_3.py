"""
PHASE 9.7.3 - CORRECCION CONTROLADA F5-F8 (planner)

F5: canonicalizacion de la clave de dedup de
    services.planner (_dedup_key): puntuacion
    interior (. , ; : ! ?) y espacios colapsados
    sobre el note normalize existente. La
    descripcion ALMACENADA sigue verbatim.
    "manana" vs "manana" NO se equiparan.
    Hora distinta / sin hora / kind distinto
    NO comparten clave.
F6: utils.date_parser.plan_relative_datetime
    acepta "en un dia" (+1) y "en una semana"
    (+7); "en 0 dias"/"en 0 semanas" -> None
    (invalido para crear -> el handler pide
    aclaracion determinista, 0 OLLAMA).
    parse_relative_date historico intacto.
F7: rama muerta "startswith('y ')" +
    _planner_marker_only eliminadas; el
    comportamiento app "y manana" tras contexto
    planner (consulta) y sin contexto (no inventa)
    queda cubierto por la suite 9.6 y aqui.
F8: core.py B1 conserva la continuidad PLANNER
    tras un turno AMBIGUO: el borrador en dos
    pasos ("recuerdame estudiar" -> aclaracion)
    no se tumba con "no se"; "manana" completa
    el borrador, "y manana" consulta, y un
    marcador pasado ("y ayer") sigue en la ruta
    determinista SIN MEMORY_SEARCH ni OLLAMA.

NOTA: literales no-ASCII con escapes \\u.
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
)

from utils.date_parser import (
    plan_relative_datetime,
    parse_relative_date,
)

import services.planner as sp

IL = IntentLayer()

SEED_DATE = SEED_NOW.date()

S_ACUERDO = "\u00bfPara cu\u00e1ndo? Dime la fecha."
S_SI = "\u00bfS\u00ed? \u00bfQu\u00e9 necesitas?"
S_YA_TENGO_EVENTO = (
    "Ya tengo ese evento registrado para "
    "28 de agosto de 2026."
)
S_EVENTO_UN_DIA = (
    "Perfecto. He registrado el evento para "
    "28 de agosto de 2026."
)
S_EVENTO_UNA_SEMANA = (
    "Perfecto. He registrado el evento para "
    "03 de septiembre de 2026."
)
S_RECORDATORIO_MANANA = (
    "Perfecto. He registrado el recordatorio "
    "para 28 de agosto de 2026."
)
S_SIN_PLANES_UN_DIA = (
    "No tengo planes registrados para "
    "28 de agosto de 2026."
)


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


def _mk_plan(plan_id, kind, due_date, due_time,
             description, status="pending",
             created="2026-08-27T12:00:00-04:00"):
    return {
        "id": plan_id,
        "kind": kind,
        "due_date": due_date,
        "due_time": due_time,
        "description": description,
        "status": status,
        "created_at": created,
    }


# ==========================================
# F5 - DEDUP CANONICALIZADO (servicio)
# ==========================================


class TestF5DedupCanonical:

    @staticmethod
    def _setup(tmp_path):
        planner = tmp_path / "planner.json"
        planner.write_text(
            '{"plans": []}', encoding="utf-8"
        )
        sp.PLANNER_PATH = planner
        return planner

    def test_puntuacion_interior_dup(self, tmp_path):
        self._setup(tmp_path)
        assert sp.save_plan(_mk_plan(
            "p1", "event", "2026-08-29", None,
            "comprar, pan")) == "created"
        assert sp.save_plan(_mk_plan(
            "p2", "event", "2026-08-29", None,
            "comprar pan")) == "duplicate"
        plans = sp.load_plans()["plans"]
        assert len(plans) == 1
        assert plans[0]["id"] == "p1"
        assert plans[0]["description"] == (
            "comprar, pan"
        )

    def test_espacios_multiples_dup(self, tmp_path):
        self._setup(tmp_path)
        assert sp.save_plan(_mk_plan(
            "p1", "event", "2026-08-29", None,
            "comprar   pan")) == "created"
        assert sp.save_plan(_mk_plan(
            "p2", "event", "2026-08-29", None,
            "comprar pan")) == "duplicate"
        assert len(
            sp.load_plans()["plans"]
        ) == 1

    def test_acento_y_punto_final_dup(
        self, tmp_path,
    ):
        self._setup(tmp_path)
        assert sp.save_plan(_mk_plan(
            "p1", "event", "2026-08-29", None,
            "caf\u00e9.")) == "created"
        assert sp.save_plan(_mk_plan(
            "p2", "event", "2026-08-29", None,
            "cafe")) == "duplicate"
        assert len(
            sp.load_plans()["plans"]
        ) == 1

    def test_hora_distinta_no_dup(self, tmp_path):
        self._setup(tmp_path)
        assert sp.save_plan(_mk_plan(
            "p1", "event", "2026-08-29", "09:00",
            "comprar pan")) == "created"
        assert sp.save_plan(_mk_plan(
            "p2", "event", "2026-08-29", None,
            "comprar pan")) == "created"
        assert len(
            sp.load_plans()["plans"]
        ) == 2

    def test_sin_hora_vs_con_hora_no_dup(
        self, tmp_path,
    ):
        self._setup(tmp_path)
        assert sp.save_plan(_mk_plan(
            "p1", "event", "2026-08-29", None,
            "comprar pan")) == "created"
        assert sp.save_plan(_mk_plan(
            "p2", "event", "2026-08-29", "09:00",
            "comprar pan")) == "created"
        assert len(
            sp.load_plans()["plans"]
        ) == 2

    def test_kind_distinto_no_dup(self, tmp_path):
        self._setup(tmp_path)
        assert sp.save_plan(_mk_plan(
            "p1", "event", "2026-08-29", None,
            "comprar pan")) == "created"
        assert sp.save_plan(_mk_plan(
            "p2", "reminder", "2026-08-29", None,
            "comprar pan")) == "created"
        assert len(
            sp.load_plans()["plans"]
        ) == 2

    def test_manana_vs_manana_no_equivale(
        self, tmp_path,
    ):
        self._setup(tmp_path)
        assert sp.save_plan(_mk_plan(
            "p1", "event", "2026-08-29", None,
            "tengo manana")) == "created"
        assert sp.save_plan(_mk_plan(
            "p2", "event", "2026-08-29", None,
            "tengo ma\u00f1ana")) == "created"
        assert len(
            sp.load_plans()["plans"]
        ) == 2


# ==========================================
# F5 - DEDUP POR think (E2E)
# ==========================================


class TestF5DedupThink:

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_crear_dup_con_puntuacion(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        _redirect_planner_file(monkeypatch, tmp_path)
        ctx = ConversationContext()
        resp = think("manana comprar, pan", ctx)
        assert resp == S_EVENTO_UN_DIA
        resp = think("manana comprar pan", ctx)
        assert resp == S_YA_TENGO_EVENTO
        assert mock_oa.call_count == 0
        plans = sp.load_plans()["plans"]
        assert len(plans) == 1
        assert plans[0]["description"] == (
            "comprar, pan"
        )


# ==========================================
# F6 - plan_relative_datetime / marcadores
# ==========================================


class TestF6PlanRelativeDatetime:

    @_seed_clock
    def test_en_un_dia(self):
        assert plan_relative_datetime(
            "en un dia", SEED_NOW
        ) == SEED_DATE + timedelta(days=1)

    @_seed_clock
    def test_en_una_semana(self):
        assert plan_relative_datetime(
            "en una semana", SEED_NOW
        ) == SEED_DATE + timedelta(days=7)

    @_seed_clock
    def test_en_cero_dias_none(self):
        assert plan_relative_datetime(
            "en 0 dias", SEED_NOW
        ) is None

    @_seed_clock
    def test_en_cero_semanas_none(self):
        assert plan_relative_datetime(
            "en 0 semanas", SEED_NOW
        ) is None

    @_seed_clock
    def test_en_tres_dias_intacto(self):
        assert plan_relative_datetime(
            "en 3 dias", SEED_NOW
        ) == SEED_DATE + timedelta(days=3)

    @_seed_clock
    def test_en_dos_semanas_intacto(self):
        assert plan_relative_datetime(
            "en 2 semanas", SEED_NOW
        ) == SEED_DATE + timedelta(weeks=2)

    @_seed_clock
    def test_dentro_de_una_semana_intacto(self):
        assert plan_relative_datetime(
            "dentro de una semana", SEED_NOW
        ) == SEED_DATE + timedelta(days=7)

    @_seed_clock
    def test_parse_relative_date_intacto(self):
        assert parse_relative_date(
            "ayer", SEED_NOW
        ) == SEED_DATE - timedelta(days=1)
        assert parse_relative_date(
            "anteayer", SEED_NOW
        ) == SEED_DATE - timedelta(days=2)


class TestF6Clasificacion:

    def test_en_un_dia_clasifica_create(self):
        r = _classify("en un dia tengo clase")
        assert r.intent == PLANNER_CREATE

    def test_en_una_semana_clasifica_create(self):
        r = _classify("en una semana tengo clase")
        assert r.intent == PLANNER_CREATE

    def test_en_cero_dias_sigue_marcador(self):
        r = _classify("en 0 dias tengo clase")
        assert r.intent == PLANNER_CREATE

    def test_que_tengo_en_un_dia_query(self):
        r = _classify("que tengo en un dia")
        assert r.intent == PLANNER_QUERY


class TestF6E2E:

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_crear_en_un_dia(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        _redirect_planner_file(monkeypatch, tmp_path)
        resp = think(
            "en un dia tengo clase",
            ConversationContext(),
        )
        assert resp == S_EVENTO_UN_DIA
        assert mock_oa.call_count == 0
        plan = sp.load_plans()["plans"][0]
        assert plan["due_date"] == "2026-08-28"
        assert plan["description"] == "tengo clase"

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_crear_en_una_semana(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        _redirect_planner_file(monkeypatch, tmp_path)
        resp = think(
            "en una semana tengo clase",
            ConversationContext(),
        )
        assert resp == S_EVENTO_UNA_SEMANA
        assert mock_oa.call_count == 0
        plan = sp.load_plans()["plans"][0]
        assert plan["due_date"] == "2026-09-03"
        assert plan["description"] == "tengo clase"

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_crear_en_una_semana_desc_verbatim(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        _redirect_planner_file(monkeypatch, tmp_path)
        resp = think(
            "en una semana tengo clase",
            ConversationContext(),
        )
        plan = sp.load_plans()["plans"][0]
        assert "semana" not in plan["description"]
        assert plan["description"] == "tengo clase"
        assert resp == S_EVENTO_UNA_SEMANA
        assert mock_oa.call_count == 0

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_crear_en_cero_dias_aclaracion(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        _redirect_planner_file(monkeypatch, tmp_path)
        resp = think(
            "en 0 dias tengo clase",
            ConversationContext(),
        )
        assert resp == S_ACUERDO
        assert mock_oa.call_count == 0
        assert sp.load_plans()["plans"] == []

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_query_en_un_dia_sin_planes(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        _redirect_planner_file(monkeypatch, tmp_path)
        resp = think(
            "que tengo en un dia",
            ConversationContext(),
        )
        assert resp == S_SIN_PLANES_UN_DIA
        assert mock_oa.call_count == 0


# ==========================================
# F7 - rama muerta eliminada (absorcion)
# ==========================================
#
# La rama "y <marcador>" dentro de
# planner_create nunca era alcanzable desde
# think: "y ..." no clasifica PLANNER_CREATE
# (guarda _PLANNER_QUERY_WORDS_EXCLUDED).
# La cobertura comportamental queda en la
# suite 9.6 (test_y_manana_resuelve_consulta,
# test_y_el_lunes_sin_contexto_no_inventa) y
# en los escenarios F8 de este archivo.


# ==========================================
# F8 - continuidad PLANNER tras AMBIGUO
# ==========================================


class TestF8ContextoTrasAmbiguedad:

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_ambiguedad_conserva_borrador(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        _redirect_planner_file(monkeypatch, tmp_path)
        ctx = ConversationContext()
        resp = think("recu\u00e9rdame estudiar", ctx)
        assert resp == S_ACUERDO
        assert ctx.conversation_mode == "planner"
        assert ctx.last_intent == PLANNER_CREATE
        assert ctx.last_entity == "estudiar"
        resp = think("no se", ctx)
        assert resp == S_SI
        assert mock_oa.call_count == 0
        assert ctx.conversation_mode == "planner"
        assert ctx.last_intent == PLANNER_CREATE
        assert ctx.last_entity == "estudiar"
        assert sp.load_plans()["plans"] == []

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_planner_ambiguo_marcador_futuro(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        # "manana" tras borrador + turno ambiguo
        # completa el borrador (recordatorio
        # "estudiar"), NO deriva a MEMORY_SEARCH
        # ni a OLLAMA.
        _redirect_planner_file(monkeypatch, tmp_path)
        ctx = ConversationContext()
        think("recu\u00e9rdame estudiar", ctx)
        assert think("no se", ctx) == S_SI
        resp = think("manana", ctx)
        assert resp == S_RECORDATORIO_MANANA
        assert mock_oa.call_count == 0
        plans = sp.load_plans()["plans"]
        assert len(plans) == 1
        assert plans[0]["kind"] == "reminder"
        assert plans[0]["description"] == "estudiar"
        assert plans[0]["due_date"] == "2026-08-28"

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_planner_ambiguo_y_manana_consulta(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        # "y manana" tras borrador + turno ambiguo
        # sigue resolviendo como CONSULTA del
        # plan (continuidad de la rama planner).
        _redirect_planner_file(monkeypatch, tmp_path)
        ctx = ConversationContext()
        think("manana tengo clase", ctx)
        assert think("no se", ctx) == S_SI
        resp = think("y manana", ctx)
        assert resp == (
            "28 de agosto de 2026 \u2014 tengo clase"
        )
        assert mock_oa.call_count == 0
        assert len(sp.load_plans()["plans"]) == 1

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_planner_ambiguo_marcador_pasado(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        # "y ayer" tras borrador + turno ambiguo NO
        # fabrica MEMORY_SEARCH ni OLLAMA: queda en
        # la ruta determinista de aclaracion y se
        # conserva el contexto planner.
        _redirect_planner_file(monkeypatch, tmp_path)
        ctx = ConversationContext()
        think("recu\u00e9rdame estudiar", ctx)
        assert think("no se", ctx) == S_SI
        resp = think("y ayer", ctx)
        assert resp == S_SI
        assert mock_oa.call_count == 0
        assert ctx.conversation_mode == "planner"
        assert ctx.last_intent == PLANNER_CREATE
        assert sp.load_plans()["plans"] == []

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_memory_contexto_tras_ambiguedad_intacto(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        # B1 MEMORY (no regresion): un dominio de
        # memoria en curso NO se invalida por un
        # turno ambiguo (comportamiento previo).
        _redirect_planner_file(monkeypatch, tmp_path)
        ctx = ConversationContext()
        think("que recuerdas", ctx)
        assert ctx.conversation_mode == "memory"
        resp = think("no se", ctx)
        assert resp == S_SI
        assert mock_oa.call_count == 0
        assert ctx.conversation_mode == "memory"