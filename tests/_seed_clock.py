"""
PHASE 8.18 — TEST CLOCK HARDENING (decorador local opt-in)

Reloj determinista LOCAL por test (`@_seed_clock`), sin conftest
global y sin tocar producción.

¿Qué hace?
  - Congela `services.archive.datetime` y
    `utils.date_parser.datetime` en la fecha semilla
    2026-08-27T12:00:00-04:00 (los WINDOWS temporales del código
    ejecutado se anclan al seed, no al calendario real).
  - Congela el símbolo `datetime` y el `NOW` capturado del MÓDULO
    del test (los helpers _day_back/_week_bounds/_month_bounds que
    derivan fechas esperadas quedan anclados al mismo seed).

No hace:
  - no congela `brain.handlers.datetime` (evita colisiones de id
    en create_memory por microsegundos=0),
  - no toca `sys.modules['datetime']` (prohibido: freeze global),
  - no modifica data/archive ni producción.
"""
import functools
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "app"),
)

SEED_NOW = datetime.fromisoformat(
    "2026-08-27T12:00:00-04:00"
)


def _make_frozen(fixed):

    class _FrozenDatetime(datetime):

        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return fixed
            return fixed.astimezone(tz)

    _FrozenDatetime.__name__ = "FrozenDatetime"
    return _FrozenDatetime


def seed_clock(fixed=SEED_NOW):
    """Contexto: congela los relojes del NÚCLEO + los del módulo
    que invoca al seed indicado. Uso local (with)."""

    class _Scope:

        def __init__(self):
            import services.archive
            import utils.date_parser
            self.targets = []
            for obj in (services.archive, utils.date_parser):
                self.targets.append(
                    (obj, "datetime", getattr(obj, "datetime"))
                )

        def __enter__(self):
            import services.archive
            import utils.date_parser
            for obj in (services.archive, utils.date_parser):
                setattr(obj, "datetime", _make_frozen(fixed))

        def __exit__(self, *_exc):
            for obj, name, original in self.targets:
                setattr(obj, name, original)
            return False

    return _Scope()


def _seed_clock(func):
    """Decorador de test: ejecuta el test con reloj congelado al
    seed (2026-08-27T12:00:00-04:00). OPT-IN por test."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        import services.archive
        import utils.date_parser

        module = sys.modules.get(func.__module__)
        frozen_cls = _make_frozen(SEED_NOW)

        saved = []
        for obj in (services.archive, utils.date_parser):
            saved.append(
                (obj, "datetime", getattr(obj, "datetime"))
            )
            setattr(obj, "datetime", frozen_cls)

        if module is not None:
            for name in ("datetime", "NOW"):
                if hasattr(module, name):
                    saved.append(
                        (module, name, getattr(module, name))
                    )
                    value = frozen_cls if name == "datetime" else SEED_NOW
                    setattr(module, name, value)

        try:
            return func(*args, **kwargs)
        finally:
            for obj, name, original in saved:
                setattr(obj, name, original)

    return wrapper