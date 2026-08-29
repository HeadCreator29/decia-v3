import json
import os
import re
import tempfile

from pathlib import Path

from utils.normalizer import (
    normalize as _normalize,
)

BASE_DIR = Path(__file__).resolve().parents[2]

ARCHIVE_PATH = BASE_DIR / "data" / "archive"

PLANNER_PATH = ARCHIVE_PATH / "planner.json"

_PLANNER_BACKUP = ARCHIVE_PATH / "planner.corrupt.backup.json"

_VALID_KINDS = ("event", "reminder")

_VALID_STATUSES = ("pending", "done")

_PLAN_KEYS = (
    "id",
    "kind",
    "due_date",
    "due_time",
    "description",
    "status",
    "created_at",
)

# ==========================================
# CARGAR PLANES
# ==========================================
#
# Contrato 9.6:
#   - archivo inexistente -> {"plans": []}
#   - vacío -> {"plans": []}
#   - corrupto (JSON roto / top-level no dict
#     / "plans" no lista) -> backup + vacío
#   - entradas inválidas -> se descartan,
#     se conservan las válidas
# ==========================================


def _read_raw():

    if not PLANNER_PATH.exists():

        return None

    return PLANNER_PATH.read_text(encoding="utf-8")


def _is_valid_plan(plan):

    if not isinstance(plan, dict):

        return False

    for key in _PLAN_KEYS:

        if key not in plan:

            return False

    if not isinstance(plan["id"], str) \
            or not plan["id"]:

        return False

    if plan["kind"] not in _VALID_KINDS:

        return False

    due_date = plan["due_date"]

    if (
        not isinstance(due_date, str)
        or not due_date
    ):

        return False

    due_time = plan["due_time"]

    if (
        due_time is not None
        and not isinstance(due_time, str)
    ):

        return False

    if not isinstance(plan["description"], str):

        return False

    if plan["status"] not in _VALID_STATUSES:

        return False

    if not isinstance(plan["created_at"], str):

        return False

    return True


def load_plans():

    try:

        content = _read_raw()

    except OSError:

        print(
            "[DECIA PLANNER] "
            "Error léxico al leer planner.json"
        )

        return {"plans": []}

    if content is None:

        return {"plans": []}

    if not content.strip():

        return {"plans": []}

    try:

        parsed = json.loads(content)

    except (json.JSONDecodeError, ValueError):

        print(
            "[DECIA PLANNER] "
            "planner.json corrupto, "
            "haciendo backup..."
        )

        _backup_corrupted()

        return {"plans": []}

    if not isinstance(parsed, dict):

        print(
            "[DECIA PLANNER] "
            "planner.json tipo invalido, "
            "haciendo backup..."
        )

        _backup_corrupted()

        return {"plans": []}

    raw_plans = parsed.get("plans")

    if not isinstance(raw_plans, list):

        print(
            "[DECIA PLANNER] "
            "planner.json sin lista de planes, "
            "haciendo backup..."
        )

        _backup_corrupted()

        return {"plans": []}

    valid = [
        p for p in raw_plans if _is_valid_plan(p)
    ]

    return {"plans": valid}


# ==========================================
# DEDUP (clave exacta del contrato 9.6)
# ==========================================
#
# (kind, due_date, due_time o "",
#  descripcion canonicalizada)
#
# F5 (9.7.3): la canonicalizacion de la
# descripcion usa utils.normalizer.normalize
# (nunca strict) y ADEMAS retira puntuacion
# interior (. , ; : ! ?) y colapsa espacios,
# de modo que variantes escritas equivalentes
# ("comprar, pan" / "comprar  pan" / "comprar
# pan", acentos) comparten clave. La descripcion
# ALMACENADA sigue siendo verbatim (este bloque
# solo construye la clave). "ma\u00f1ana" vs
# "manana" NO se equiparan (no se mapea
# n\u00f1->n fuera de los marcadores temporales).
# ==========================================

_DEDUP_STRIP_RE = re.compile(r"[.,;:!?]+")


def _dedup_canonical(text):

    text = _normalize(text)

    text = _DEDUP_STRIP_RE.sub("", text)

    return " ".join(text.split())


def _dedup_key(plan):

    return (
        plan.get("kind"),
        str(plan.get("due_date", "") or ""),
        plan.get("due_time") or "",
        _dedup_canonical(
            plan.get("description", "") or ""
        ),
    )


# ==========================================
# ESCRITURA ATÓMICA
# ==========================================


def _write_plans(data):

    try:

        fd, tmp = tempfile.mkstemp(
            dir=str(PLANNER_PATH.parent),
            prefix="planner.",
            suffix=".tmp",
        )

        try:

            with os.fdopen(
                fd, "w", encoding="utf-8"
            ) as file:

                json.dump(
                    data,
                    file,
                    ensure_ascii=False,
                    indent=2,
                )

            os.replace(tmp, PLANNER_PATH)

        finally:

            if os.path.exists(tmp):

                os.remove(tmp)

        return True

    except Exception as error:

        print(
            f"[DECIA PLANNER] "
            f"Error al guardar planner: {error}"
        )

        return False


def _backup_corrupted():

    try:

        content = _read_raw()

        if content is None:

            return False

        _PLANNER_BACKUP.write_text(
            content, encoding="utf-8"
        )

        print(
            "[DECIA PLANNER] "
            "Backup corrupto guardado: "
            "planner.corrupt.backup.json"
        )

        return True

    except Exception:

        return False


# ==========================================
# GUARDAR PLAN
# ==========================================


def save_plan(plan):

    data = load_plans()

    new_key = _dedup_key(plan)

    for existing in data["plans"]:

        if new_key == _dedup_key(existing):

            return "duplicate"

    data["plans"].append(plan)

    if _write_plans(data):

        return "created"

    return "error"


# ==========================================
# CONSULTAR PLANES
# ==========================================
#
# Orden del contrato:
#   due_date ASC, due_time ASC (sin hora
#   ANTES que con hora del mismo día),
#   created_at ASC, id ASC.
# ==========================================


def query_plans(due_date=None, since_date=None,
                status=None, kind=None):

    data = load_plans()

    plans = data["plans"]

    if kind is not None:

        plans = [
            p for p in plans
            if p.get("kind") == kind
        ]

    if due_date is not None:

        plans = [
            p for p in plans
            if (p.get("due_date") or "") == due_date
        ]

    if since_date is not None:

        plans = [
            p for p in plans
            if (p.get("due_date") or "") >= since_date
        ]

    if status is not None:

        plans = [
            p for p in plans
            if (p.get("status") or "") == status
        ]

    def _sort_key(p):

        return (
            p.get("due_date", ""),
            p.get("due_time") or "",
            p.get("created_at", ""),
            p.get("id", ""),
        )

    plans.sort(key=_sort_key)

    return plans


# ==========================================
# ACTUALIZAR PLAN
# ==========================================


def update_plan_status(plan_id, status):

    if status not in _VALID_STATUSES:

        return False

    data = load_plans()

    found = False

    for plan in data["plans"]:

        if plan.get("id") == plan_id:

            plan["status"] = status

            found = True

    if not found:

        return False

    return _write_plans(data)


def update_plan_time(plan_id, due_time):
    # 9.6 follow-up: "a las 9" completa la hora
    # de un plan pendiente creado sin hora.

    if due_time is not None and not isinstance(due_time, str):

        return False

    data = load_plans()

    found = False

    for plan in data["plans"]:

        if plan.get("id") == plan_id:

            plan["due_time"] = due_time

            found = True

    if not found:

        return False

    return _write_plans(data)