"""
PHASE 9.6 - PLANNER N1+N2 (eventos y recordatorios futuros)

Registro y consulta de planes en data/archive/planner.json
(si el test no lo redirige): kind event|reminder, due_date future,
due_time opcional, descripcion verbatim. Rutas 100% deterministas:
0 OLLAMA, 0 escritura en memories.json.

Invariantes del contrato verificadas aqui:
  - intents PLANNER_CREATE / PLANNER_QUERY con pesos estables.
  - plan_relative_datetime: solo futuro ("manana", "pasado manana",
    "en N dias", "dentro de N semanas", dia siguiente estricto,
    fecha absoluta); guarda "la/esta manana" y "el lunes pasado".
  - dedup exacto (kind, fecha, hora o "", desc normalizada).
  - escritura atomica; corrupcion -> backup + vacio.
  - flujo en dos pasos: fecha y hora por separado.
  - coexistencia event + reminder y orden (sin hora antes).
  - no regresion de MEMORY_SEARCH / ARCHIVE / EXIT / MEMORY_CREATE.

NOTA: todos los literales no-ASCII usan escapes \\u para evitar
corrupcion de codificacion en el transporte del archivo.
"""
import json
import sys
from datetime import datetime, timedelta
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
    ARCHIVE_SEARCH,
    FREE_TALK,
    EXIT,
)

from utils.date_parser import (
    plan_relative_datetime,
    parse_relative_time,
)

import services.planner as sp

IL = IntentLayer()

SEED_DATE = SEED_NOW.date()

# literales con acentos / simbolos (a prueba de encoding)
S_ACUERDO = "\u00bfPara cu\u00e1ndo? Dime la fecha."
S_ACUALICE = "Actualic\u00e9 la hora del recordatorio para"
S_MAYUSCULAS = "Ma\u00f1ana tengo Clase de Matem\u00e1ticas"
S_GT = "\u00a1Ma\u00f1ana, tengo clase!"
S_RECORDAR = "recu\u00e9rdame ma\u00f1ana comprar material"
S_PASADO = "recu\u00e9rdame pasado ma\u00f1ana comprar material a las 9"
S_MARIA = "cena con Mar\u00eda"
SEP = "\u2014"


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
# A. CLASIFICACION 9.6
# ==========================================


class TestClassification:

    def test_que_tengo_manana_query(self):
        r = _classify("que tengo manana")
        assert r.intent == PLANNER_QUERY
        assert r.confidence >= 0.50

    def test_que_tengo_pendiente_query(self):
        r = _classify("que tengo pendiente")
        assert r.intent == PLANNER_QUERY

    def test_que_hay_manana_query(self):
        r = _classify("que hay manana")
        assert r.intent == PLANNER_QUERY

    def test_que_debo_hacer_manana_query(self):
        r = _classify("que debo hacer manana")
        assert r.intent == PLANNER_QUERY

    def test_que_tengo_que_hacer_manana_query(self):
        r = _classify("que tengo que hacer manana")
        assert r.intent == PLANNER_QUERY

    def test_que_eventos_tengo_manana_query(self):
        r = _classify("que eventos tengo manana")
        assert r.intent == PLANNER_QUERY

    def test_que_tengo_el_lunes_query(self):
        r = _classify("que tengo el lunes")
        assert r.intent == PLANNER_QUERY

    def test_manana_tengo_clase_create(self):
        r = _classify("manana tengo clase")
        assert r.intent == PLANNER_CREATE

    def test_el_lunes_tengo_examen_create(self):
        r = _classify("el lunes tengo examen")
        assert r.intent == PLANNER_CREATE

    def test_recuerdame_manana_comprar_create(self):
        r = _classify(S_RECORDAR)
        assert r.intent == PLANNER_CREATE

    def test_recuerdame_estudiar_create(self):
        r = _classify("recuerdame estudiar")
        assert r.intent == PLANNER_CREATE

    def test_pasado_manana_create(self):
        r = _classify("pasado manana tengo cita")
        assert r.intent == PLANNER_CREATE


class TestClassificationBarriers:
    """Las rutas existentes NO cambian (guardas)."""

    def test_recuerdame_lo_que_hablamos_memory(self):
        r = _classify("recuerdame lo que hablamos hoy")
        assert r.intent == MEMORY_SEARCH

    def test_que_te_dije_que_tengo_manana_memory(self):
        r = _classify("que te dije que tengo manana")
        assert r.intent == MEMORY_SEARCH

    def test_hasta_manana_exit(self):
        r = _classify("hasta manana")
        assert r.intent == EXIT

    def test_que_paso_manana_free_talk(self):
        r = _classify("que paso manana")
        assert r.intent == FREE_TALK

    def test_que_sucedio_manana_free_talk(self):
        r = _classify("que sucedio manana")
        assert r.intent == FREE_TALK

    def test_de_la_manana_no_marker(self):
        msg = (
            "hoy me despert\u00e9 a las seis de la manana "
            "y sal\u00ed a caminar al parque"
        )
        assert _classify(msg).intent == FREE_TALK

    def test_lunes_pasado_no_create(self):
        r = _classify("el lunes pasado vi una pelicula")
        assert r.intent != PLANNER_CREATE

    def test_lunes_pasado_no_query(self):
        r = _classify("que tengo el lunes pasado")
        assert r.intent != PLANNER_QUERY

    def test_y_el_lunes_no_create(self):
        # "y <temporal>" sigue siendo seguimiento
        # (continuidad memory/archive, fase 8); no
        # debe clasificar PLANNER_CREATE.
        r = _classify("y el lunes")
        assert r.intent != PLANNER_CREATE
        assert r.intent != PLANNER_QUERY

    def test_anota_que_es_lunes_memory_create(self):
        r = _classify("anota que es lunes")
        assert r.intent == MEMORY_CREATE

    def test_recuerda_que_tengo_clase_manana_create(self):
        r = _classify("recuerda que tengo clase manana")
        assert r.intent == MEMORY_CREATE

    def test_guarda_que_manana_tengo_clase_create(self):
        r = _classify("guarda que manana tengo clase")
        assert r.intent == MEMORY_CREATE

    def test_que_eventos_hubo_semana_pasada_archive(self):
        r = _classify(
            "que eventos de deca hubo la semana pasada"
        )
        assert r.intent == ARCHIVE_SEARCH


# ==========================================
# B. plan_relative_datetime
# ==========================================


class TestPlanRelativeDatetime:

    @_seed_clock
    def test_manana(self):
        assert plan_relative_datetime(
            "manana tengo clase"
        ) == SEED_DATE + timedelta(days=1)

    @_seed_clock
    def test_pasado_manana(self):
        assert plan_relative_datetime(
            "pasado manana"
        ) == SEED_DATE + timedelta(days=2)

    @_seed_clock
    def test_en_tres_dias(self):
        assert plan_relative_datetime(
            "en 3 dias"
        ) == SEED_DATE + timedelta(days=3)

    @_seed_clock
    def test_dentro_de_una_semana(self):
        assert plan_relative_datetime(
            "dentro de una semana"
        ) == SEED_DATE + timedelta(days=7)

    @_seed_clock
    def test_dentro_de_dos_semanas(self):
        assert plan_relative_datetime(
            "dentro de 2 semanas"
        ) == SEED_DATE + timedelta(days=14)

    @_seed_clock
    def test_el_lunes_siguiente(self):
        next_monday = SEED_DATE + timedelta(days=4)
        assert plan_relative_datetime(
            "el lunes tengo examen"
        ) == next_monday

    @_seed_clock
    def test_este_sabado(self):
        assert plan_relative_datetime(
            "este sabado"
        ) == SEED_DATE + timedelta(days=2)

    def test_rollover_weekday_friday(self):
        friday = datetime.fromisoformat(
            "2026-08-28T10:00:00-04:00"
        )
        assert plan_relative_datetime(
            "el lunes", now=friday
        ) == friday.date() + timedelta(days=3)
        assert plan_relative_datetime(
            "manana", now=friday
        ) == friday.date() + timedelta(days=1)

    def test_dia_propio_next_week(self):
        friday = datetime.fromisoformat(
            "2026-08-28T10:00:00-04:00"
        )
        # "el viernes" siendo viernes -> la proxima
        # semana (nunca el mismo dia).
        assert plan_relative_datetime(
            "el viernes", now=friday
        ) == friday.date() + timedelta(days=7)

    @_seed_clock
    def test_fecha_absoluta(self):
        assert plan_relative_datetime(
            "2026/09/01"
        ).isoformat() == "2026-09-01"

    @_seed_clock
    def test_sin_marcador_none(self):
        assert plan_relative_datetime(
            "tengo clase todos los dias"
        ) is None

    @_seed_clock
    def test_la_manana_no_es_futuro(self):
        assert plan_relative_datetime(
            "me levante de la manana"
        ) is None

    @_seed_clock
    def test_lunes_pasado_none(self):
        assert plan_relative_datetime(
            "el lunes pasado"
        ) is None

    @_seed_clock
    def test_fecha_absoluta_invalida_none(self):
        assert plan_relative_datetime(
            "2026-13-45"
        ) is None

    def test_parse_relative_time_intacto(self):
        assert parse_relative_time(
            "a las 9 de la manana"
        ) == "09:00"


# ==========================================
# CREACION POR think (flujo completo)
# ==========================================


class TestCreateThink:

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_crear_evento(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        planner = _redirect_planner_file(
            monkeypatch, tmp_path
        )
        ctx = ConversationContext()
        resp = think("manana tengo clase", ctx)
        assert resp == (
            "Perfecto. He registrado el evento "
            "para 28 de agosto de 2026."
        )
        assert mock_oa.call_count == 0
        data = sp.load_plans()
        assert len(data["plans"]) == 1
        plan = data["plans"][0]
        assert plan["kind"] == "event"
        assert plan["due_date"] == "2026-08-28"
        assert plan["due_time"] is None
        assert plan["description"] == "tengo clase"
        assert plan["status"] == "pending"
        assert plan["id"].startswith("plan_")
        assert "T" in plan["created_at"]

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_crear_evento_con_hora(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        _redirect_planner_file(monkeypatch, tmp_path)
        resp = think(
            "manana a las 9 tengo clase",
            ConversationContext(),
        )
        assert resp == (
            "Perfecto. He registrado el evento "
            "para 28 de agosto de 2026 a las 09:00."
        )
        assert mock_oa.call_count == 0
        plan = sp.load_plans()["plans"][0]
        assert plan["due_time"] == "09:00"

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_crear_recordatorio(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        _redirect_planner_file(monkeypatch, tmp_path)
        resp = think(S_RECORDAR, ConversationContext())
        assert resp == (
            "Perfecto. He registrado el recordatorio "
            "para 28 de agosto de 2026."
        )
        assert mock_oa.call_count == 0
        plan = sp.load_plans()["plans"][0]
        assert plan["kind"] == "reminder"
        assert plan["description"] == "comprar material"

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_descripcion_verbatim(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        _redirect_planner_file(monkeypatch, tmp_path)
        think(S_MAYUSCULAS, ConversationContext())
        plan = sp.load_plans()["plans"][0]
        assert plan["description"] == (
            "tengo Clase de Matem\u00e1ticas"
        )
        assert mock_oa.call_count == 0

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_descripcion_con_puntuacion(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        _redirect_planner_file(monkeypatch, tmp_path)
        think(S_GT, ConversationContext())
        plan = sp.load_plans()["plans"][0]
        assert plan["description"] == "tengo clase"
        assert mock_oa.call_count == 0

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_fecha_pasada_rechazada(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        _redirect_planner_file(monkeypatch, tmp_path)
        resp = think(
            "2020-01-01 vacaciones",
            ConversationContext(),
        )
        assert resp == (
            "Esa fecha ya pas\u00f3. No puedo "
            "registrarla."
        )
        assert mock_oa.call_count == 0
        assert sp.load_plans()["plans"] == []

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_sin_fecha_aclaracion(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        _redirect_planner_file(monkeypatch, tmp_path)
        resp = think(
            "recuerdame estudiar",
            ConversationContext(),
        )
        assert resp == S_ACUERDO
        assert mock_oa.call_count == 0
        assert sp.load_plans()["plans"] == []

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_duplicado_rechazado(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        _redirect_planner_file(monkeypatch, tmp_path)
        resp = None
        for _ in range(2):
            resp = think(
                "manana tengo clase",
                ConversationContext(),
            )
        assert resp == (
            "Ya tengo ese evento registrado "
            "para 28 de agosto de 2026."
        )
        assert mock_oa.call_count == 0
        assert len(sp.load_plans()["plans"]) == 1


# ==========================================
# CONSULTAS POR think
# ==========================================


class TestQueryThink:

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_consulta_vacia(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        _redirect_planner_file(monkeypatch, tmp_path)
        resp = think(
            "que tengo manana",
            ConversationContext(),
        )
        assert resp == (
            "No tengo planes registrados "
            "para 28 de agosto de 2026."
        )
        assert mock_oa.call_count == 0

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_consulta_por_fecha(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        _redirect_planner_file(monkeypatch, tmp_path)
        think("manana tengo clase", \
              ConversationContext())
        resp = think(
            "que tengo manana",
            ConversationContext(),
        )
        assert resp == (
            "28 de agosto de 2026 " + SEP + " tengo clase"
        )
        assert mock_oa.call_count == 0

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_consulta_pendiente_multi_fecha(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        _redirect_planner_file(monkeypatch, tmp_path)
        think("manana tengo clase", \
              ConversationContext())
        think(S_PASADO, ConversationContext())
        resp = think(
            "que tengo pendiente",
            ConversationContext(),
        )
        assert (
            "28 de agosto de 2026 " + SEP + " tengo clase"
        ) in resp
        assert (
            "29 de agosto de 2026 a las 09:00 "
            + SEP + " comprar material"
        ) in resp
        assert (
            resp.index("28 de agosto")
            < resp.index("29 de agosto")
        )
        assert mock_oa.call_count == 0

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_y_manana_resuelve_consulta(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        _redirect_planner_file(monkeypatch, tmp_path)
        # contexto planner ya establecido
        ctx = ConversationContext()
        think("manana tengo clase", ctx)
        resp = think("y manana", ctx)
        assert resp == (
            "28 de agosto de 2026 " + SEP + " tengo clase"
        )
        assert mock_oa.call_count == 0

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_y_el_lunes_sin_contexto_no_inventa(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        _redirect_planner_file(monkeypatch, tmp_path)
        # sin contexto previo: "y el lunes" NO
        # fabrica un plan (va a OLLAMA).
        mock_oa.return_value = "OLLAMA"
        resp = think("y el lunes", \
                     ConversationContext())
        assert resp == "OLLAMA"
        assert mock_oa.call_count == 1
        assert sp.load_plans()["plans"] == []


# ==========================================
# FLUJO EN DOS PASOS (fecha / hora)
# ==========================================


class TestTwoStepFlow:

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_completar_fecha_en_dos_pasos(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        _redirect_planner_file(monkeypatch, tmp_path)
        ctx = ConversationContext()
        think("recuerdame estudiar", ctx)
        resp = think("manana a las 9", ctx)
        assert resp == (
            "Perfecto. He registrado el recordatorio "
            "para 28 de agosto de 2026 a las 09:00."
        )
        plan = sp.load_plans()["plans"][0]
        assert plan["kind"] == "reminder"
        assert plan["description"] == "estudiar"
        assert plan["due_date"] == "2026-08-28"
        assert plan["due_time"] == "09:00"
        assert mock_oa.call_count == 0

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_completar_hora_tras_fecha(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        _redirect_planner_file(monkeypatch, tmp_path)
        ctx = ConversationContext()
        think("recuerdame estudiar", ctx)
        think("manana", ctx)
        resp = think("a las 9", ctx)
        assert resp == (
            "Perfecto. " + S_ACUALICE
            + " 28 de agosto de 2026 a las 09:00."
        )
        assert mock_oa.call_count == 0
        plans = sp.load_plans()["plans"]
        assert len(plans) == 1
        assert plans[0]["due_time"] == "09:00"

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_determinismo_sin_ollama(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        _redirect_planner_file(monkeypatch, tmp_path)
        think("manana tengo clase", \
              ConversationContext())
        r1 = think("que tengo manana", \
                   ConversationContext())
        r2 = think("que tengo manana", \
                   ConversationContext())
        assert r1 == r2
        assert mock_oa.call_count == 0


# ==========================================
# NO ESCRIBE EN MEMORIES
# ==========================================


class TestMemoryIsolation:

    @_seed_clock
    @patch("brain.core.ask_ollama")
    def test_planner_no_toca_memories(
        self, mock_oa, monkeypatch, tmp_path,
    ):
        _redirect_planner_file(monkeypatch, tmp_path)
        calls = []

        real_save_memory = __import__(
            "brain.handlers", fromlist=["save_memory"]
        ).save_memory

        def recorder(memory):
            calls.append(memory)
            return real_save_memory(memory)

        monkeypatch.setattr(
            "brain.handlers.save_memory", recorder
        )
        think("manana tengo clase", \
              ConversationContext())
        think("recu\u00e9rdame ma\u00f1ana comprar", \
              ConversationContext())
        assert calls == []
        assert mock_oa.call_count == 0


# ==========================================
# SERVICIO: PERSISTENCIA, ORDEN Y CORRUPCION
# ==========================================


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


class TestPlannerService:

    def test_save_y_reload(self, tmp_path):
        planner = tmp_path / "planner.json"
        planner.write_text('{"plans": []}',
                           encoding="utf-8")
        sp.PLANNER_PATH = planner
        plan = _mk_plan(
            "p1", "event", "2026-08-29", None,
            "tengo clase",
        )
        assert sp.save_plan(plan) == "created"
        assert sp.load_plans()["plans"] == [plan]

    def test_dedup_exacto(self, tmp_path):
        planner = tmp_path / "planner.json"
        planner.write_text('{"plans": []}',
                           encoding="utf-8")
        sp.PLANNER_PATH = planner
        p = _mk_plan("p1", "event", "2026-08-29",
                     None, "tengo Clase")
        assert sp.save_plan(p) == "created"
        # Misma clave (normalize quita acentos/case).
        p2 = _mk_plan("p2", "event", "2026-08-29",
                      None, "tengo clase")
        assert sp.save_plan(p2) == "duplicate"
        assert len(sp.load_plans()["plans"]) == 1

    def test_orden_sin_hora_antes(self, tmp_path):
        planner = tmp_path / "planner.json"
        planner.write_text('{"plans": []}',
                           encoding="utf-8")
        sp.PLANNER_PATH = planner
        for p in [
            _mk_plan("b", "reminder", "2026-08-29",
                     "09:00", "con hora"),
            _mk_plan("a", "event", "2026-08-29",
                     None, "sin hora"),
            _mk_plan("c", "event", "2026-08-28",
                     "08:00", "dia antes"),
        ]:
            sp.save_plan(p)
        rows = sp.query_plans(status="pending")
        assert [r["id"] for r in rows] == [
            "c", "a", "b",
        ]

    def test_filtros(self, tmp_path):
        planner = tmp_path / "planner.json"
        planner.write_text('{"plans": []}',
                           encoding="utf-8")
        sp.PLANNER_PATH = planner
        sp.save_plan(_mk_plan(
            "e1", "event", "2026-08-29", None,
            "evento 1"))
        sp.save_plan(_mk_plan(
            "r1", "reminder", "2026-08-30", "10:00",
            "recordatorio 1"))
        assert len(
            sp.query_plans(kind="event")
        ) == 1
        assert len(
            sp.query_plans(due_date="2026-08-29")
        ) == 1
        assert len(
            sp.query_plans(since_date="2026-08-30")
        ) == 1
        assert sp.query_plans(
            due_date="2026-08-28"
        ) == []

    def test_update_plan_status_y_time(self, tmp_path):
        planner = tmp_path / "planner.json"
        planner.write_text('{"plans": []}',
                           encoding="utf-8")
        sp.PLANNER_PATH = planner
        sp.save_plan(_mk_plan(
            "p1", "reminder", "2026-08-29", None,
            "estudiar"))
        assert sp.update_plan_time("p1", "09:00")
        assert sp.update_plan_status("p1", "done")
        rows = sp.query_plans(status="done")
        assert len(rows) == 1
        assert rows[0]["due_time"] == "09:00"
        assert sp.update_plan_status(
            "nope", "done"
        ) is False
        assert sp.update_plan_time(
            "p1", 12345
        ) is False

    def test_corrupcion_backup_y_vacio(
        self, tmp_path,
    ):
        planner = tmp_path / "planner.json"
        planner.write_text("{no valid json",
                           encoding="utf-8")
        backup = tmp_path / "planner.corrupt.backup.json"
        sp.PLANNER_PATH = planner
        sp._PLANNER_BACKUP = backup
        assert sp.load_plans() == {"plans": []}
        assert backup.exists()

    def test_tipo_invalido_backup(self, tmp_path):
        planner = tmp_path / "planner.json"
        planner.write_text("[1,2,3]", encoding="utf-8")
        backup = tmp_path / "backup.json"
        sp.PLANNER_PATH = planner
        sp._PLANNER_BACKUP = backup
        assert sp.load_plans() == {"plans": []}
        assert backup.exists()

    def test_entradas_invalidas_se_filtran(
        self, tmp_path,
    ):
        planner = tmp_path / "planner.json"
        valid = _mk_plan(
            "ok", "event", "2026-08-30", None,
            "valido",
        )
        planner.write_text(
            json.dumps({
                "plans": [
                    valid,
                    {"id": "roto"},
                    "basura",
                    {},
                ]
            }, ensure_ascii=False),
            encoding="utf-8",
        )
        sp.PLANNER_PATH = planner
        plans = sp.load_plans()["plans"]
        assert len(plans) == 1
        assert plans[0]["id"] == "ok"

    def test_ensure_ascii_false(self, tmp_path):
        planner = tmp_path / "planner.json"
        planner.write_text('{"plans": []}',
                           encoding="utf-8")
        sp.PLANNER_PATH = planner
        sp.save_plan(_mk_plan(
            "p1", "reminder", "2026-08-30", None,
            S_MARIA))
        raw = planner.read_text(encoding="utf-8")
        assert "Mar\u00eda" in raw

    def test_inexistente_vacio(self, tmp_path):
        planner = tmp_path / "planner.json"
        sp.PLANNER_PATH = planner
        assert sp.load_plans() == {"plans": []}