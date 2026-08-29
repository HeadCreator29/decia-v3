"""
PHASE 8.15 — B1 + G1 (correcciones P3 auditadas en 8.14)

B1: la clarificación determinista ("¿Sí? ¿Qué necesitas?")
NO debe borrar un tema HISTORY/MEMORY/ARCHIVE en curso.
Con contexto de búsqueda activo (un tema histórico),
tras "que hubo algo" / "y ayer" el usuario continúa con
follow-ups ("y el lunes", "y que mas") que deben resolver
deterministas sobre el mismo dominio (antes -> OLLAMA
por invalidación del contexto). Con contexto NO-búsqueda
(TIME/DATE/frío) la invalidación se mantiene.

G1: la familia EVENTS ("acontecio", "acontecimientos",
"hechos", "eventos" + entidad/temporal) es dominio
ARCHIVE (section HISTORIA de search_archive), no MEMORY.
Antes el intent layer la clasificaba MEMORY_SEARCH y el
gate field=="memories" descartaba los eventos ->
falso negativo ("No tengo memorias registradas.") pese
a existir eventos. G6 ("que acontecio" desnudo) también
es HISTORY determinista.

Fuera de alcance (G2/G4, se conservan): "que acontecimientos
de deca hubo ayer" (FREE_TALK -> OLLAMA legítimo) y la
familia EVENTS sin referencia temporal ("que acontecimientos
hubo" -> FREE_TALK/AMBIGUOUS).

Verifica: single-pass, 0 OLLAMA en las rutas deterministas,
EVENTS no suplanta MEMORY, MEMORY no suplanta EVENTS,
G1-G7 intactas, cold/warm, hashes e invariantes intactos.
"""
import sys

from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "app"),
)

from unittest.mock import patch

from datetime import datetime, timedelta

from brain.core import think
from brain.context import ConversationContext
from brain.intent_layer import IntentLayer

from brain.intent_types import (
    ARCHIVE_SEARCH,
    DATE,
    FREE_TALK,
    AMBIGUOUS_INPUT,
    MEMORY_SEARCH,
)

IL = IntentLayer()

NOW = datetime.now().astimezone()

EVENTS_FAMILY_ARCHIVE = (
    "que acontecio ayer",
    "que acontecio hace una semana",
    "que acontecio con maria hace 3 dias",
    "que acontecio sobre kanye ayer",
    "que acontecimientos hubo la semana pasada",
    "que acontecimientos acontecieron el lunes",
    "que eventos sucedieron ayer",
    "que eventos hubo esta semana",
    "que hechos hubo hace 3 dias",
)

EVENTS_FAMILY_SIN_TEMPORAL = (
    "que acontecio",
    "que acontecimientos hubo",
    "que eventos hubo",
    "que hechos hubo",
)

VERBOS_GENERICOS_MEMORY = (
    "que sucedio ayer",
    "que ocurrio ayer",
    "que paso ayer",
    "que hubo ayer",
    "que sucedio con kanye ayer",
)


def _classify(message):
    return IL.classify(message)


def _today_date():
    return NOW.date()


def _iso(day):
    return day.isoformat()


def _week_bounds(week_offset):
    today = _today_date()
    monday = (
        today - timedelta(days=today.weekday())
        + timedelta(weeks=week_offset)
    )
    return (
        monday.isoformat(),
        (monday + timedelta(days=6)).isoformat(),
    )


def _day_back(days):
    return _iso(
        _today_date() - timedelta(days=days)
    )


def _prev_weekday(target_wd):
    today = _today_date()
    back = (today.weekday() - target_wd) % 7
    if back == 0:
        back = 7
    return _iso(today - timedelta(days=back))


def _mem(mid, date, description):
    return {
        "id": mid,
        "date": date,
        "description": description,
    }


def _event(eid, date, title, description):
    return {
        "id": eid,
        "date": date,
        "title": title,
        "description": description,
    }


def _no_memory_search():
    from brain import core as coremod
    calls = {"n": 0}
    orig = coremod.search_deca_memory

    def wrapped(msg, *args, **kwargs):
        calls["n"] += 1
        return orig(msg, *args, **kwargs)

    coremod.search_deca_memory = wrapped
    return calls, orig


# ==========================================
# A. B1: CASCADA DE CLARIFICACIÓN -> NO
#    INVALIDAR TEMA HISTORY/MEMORY/ARCHIVE
# ==========================================


class TestB1CascadaInvalidacion:

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_near_bare_preserva_tema_y_sigue(
        self, mock_env, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_env.return_value = {"memories": []}
        ctx = ConversationContext()

        calls, orig = _no_memory_search()
        try:
            r1 = think("que paso", context=ctx)
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig

        assert "Inicio de la d" in r1
        assert mock_oa.call_count == 0
        assert calls["n"] == 0
        assert ctx.conversation_mode == "archive"
        assert ctx.last_intent == ARCHIVE_SEARCH
        assert ctx.previous_user_input == "que paso"

        calls, orig = _no_memory_search()
        try:
            r2 = think("que hubo algo", context=ctx)
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig

        assert "necesitas" in r2
        assert mock_oa.call_count == 0
        assert calls["n"] == 0
        assert ctx.conversation_mode == "archive"
        assert ctx.last_intent == ARCHIVE_SEARCH
        assert ctx.previous_user_input == "que paso"

        calls, orig = _no_memory_search()
        try:
            r3 = think("y el lunes", context=ctx)
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig

        assert r3 != "OLLAMA"
        assert mock_oa.call_count == 0, r3
        assert calls["n"] == 1
        assert ctx.conversation_mode == "archive"

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_y_ayer_sigue_y_el_lunes(
        self, mock_env, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_env.return_value = {"memories": []}
        ctx = ConversationContext()

        calls, orig = _no_memory_search()
        try:
            r1 = think("que paso", context=ctx)
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig

        assert "Inicio de la d" in r1
        assert calls["n"] == 0
        assert mock_oa.call_count == 0
        assert ctx.conversation_mode == "archive"

        calls, orig = _no_memory_search()
        try:
            r2 = think("y ayer", context=ctx)
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig

        assert "necesitas" in r2
        assert mock_oa.call_count == 0
        assert calls["n"] == 0
        assert ctx.conversation_mode == "archive"
        assert ctx.last_intent == ARCHIVE_SEARCH

        calls, orig = _no_memory_search()
        try:
            r3 = think("y el lunes", context=ctx)
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig

        assert r3 != "OLLAMA"
        assert mock_oa.call_count == 0
        assert calls["n"] == 1
        assert ctx.conversation_mode == "archive"

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_archivo_tema_doble_clarificacion(
        self, mock_env, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_env.return_value = {"memories": []}
        ctx = ConversationContext()

        calls, orig = _no_memory_search()
        try:
            think(
                "que eventos de deca hubo ayer",
                context=ctx,
            )
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig
        assert calls["n"] == 1
        assert mock_oa.call_count == 0
        assert ctx.conversation_mode == "archive"
        assert ctx.previous_user_input == (
            "que eventos de deca hubo ayer"
        )

        for ask in ("que hubo algo", "que hubo alguien"):
            with patch(
                "brain.core.ask_ollama",
                return_value="OLLAMA",
            ):
                r = think(ask, context=ctx)
            assert "necesitas" in r
            assert ctx.previous_user_input == (
                "que eventos de deca hubo ayer"
            )
            assert ctx.conversation_mode == "archive"

        calls, orig = _no_memory_search()
        try:
            r = think("y que mas", context=ctx)
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig
        assert r != "OLLAMA"
        assert calls["n"] == 1
        assert mock_oa.call_count == 0
        assert ctx.conversation_mode == "archive"

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_memoria_tema_preservado(
        self, mock_env, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_env.return_value = {"memories": []}
        ctx = ConversationContext()

        calls, orig = _no_memory_search()
        try:
            think("que paso ayer", context=ctx)
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig
        assert calls["n"] == 1
        assert ctx.conversation_mode == "memory"

        with patch(
            "brain.core.ask_ollama",
            return_value="OLLAMA",
        ):
            r = think("que hubo algo", context=ctx)
        assert "necesitas" in r
        assert ctx.conversation_mode == "memory"
        assert ctx.last_intent == MEMORY_SEARCH

        calls, orig = _no_memory_search()
        try:
            r = think("y el lunes", context=ctx)
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig
        assert r != "OLLAMA"
        assert calls["n"] == 1
        assert mock_oa.call_count == 0
        assert ctx.conversation_mode == "memory"

    @patch("brain.core.ask_ollama")
    def test_tiempo_fecha_se_sigue_invalidando(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        ctx = ConversationContext()
        ctx.last_intent = DATE
        ctx.conversation_mode = "time"
        ctx.last_search_query = None

        r = think("y ayer", context=ctx)

        assert "necesitas" in r
        assert ctx.last_intent is None
        assert ctx.conversation_mode is None
        assert mock_oa.call_count == 0

    @patch("brain.core.ask_ollama")
    def test_frio_no_inventa_contexto(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        ctx = ConversationContext()
        r1 = think("que hubo algo", context=ctx)
        assert "necesitas" in r1
        assert ctx.last_intent is None
        assert ctx.conversation_mode is None

        r2 = think("y el lunes", context=ctx)
        assert r2 == "OLLAMA"
        assert mock_oa.call_count == 1


# ==========================================
# B. G1: FAMILIA EVENTS ES DOMINIO ARCHIVE
# ==========================================


class TestG1FamiliaEvents:

    def test_familia_events_classification_archive(
        self,
    ):
        for ask in EVENTS_FAMILY_ARCHIVE:
            r = _classify(ask)
            assert r.intent == ARCHIVE_SEARCH, ask
            assert r.confidence >= 0.50, ask

    def test_familia_events_sin_temporal_no_archive(
        self,
    ):
        for ask in EVENTS_FAMILY_SIN_TEMPORAL:
            r = _classify(ask)
            assert r.intent != ARCHIVE_SEARCH, ask
            assert r.intent in (
                FREE_TALK, AMBIGUOUS_INPUT,
            ), ask

    def test_verbos_genericos_siguen_memory(self):
        for ask in VERBOS_GENERICOS_MEMORY:
            r = _classify(ask)
            assert r.intent == MEMORY_SEARCH, ask

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_history")
    @patch("services.archive.get_memories")
    def test_memory_no_suplanta_events(
        self, mock_env, mock_h, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_env.return_value = {"memories": [
            _mem("m", _day_back(1),
                 "memoria personal de ayer"),
        ]}
        mock_h.return_value = {"events": [
            _event("e1", _day_back(1), "Lanzamiento",
                   "evento historico de ayer"),
            _event("e2", _day_back(0), "Hoy",
                   "evento del dia de hoy"),
        ]}
        calls, orig = _no_memory_search()
        try:
            ctx = ConversationContext()
            r = think("que acontecio ayer", context=ctx)
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig
        assert "evento historico de ayer" in r
        assert "evento del dia de hoy" not in r
        assert "memoria personal de ayer" not in r
        assert "No tengo memorias" not in r
        assert mock_oa.call_count == 0
        assert calls["n"] == 1
        assert ctx.conversation_mode == "archive"

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_history")
    @patch("services.archive.get_memories")
    def test_events_no_suplantan_memory(
        self, mock_env, mock_h, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_env.return_value = {"memories": [
            _mem("m", _day_back(1),
                 "memoria personal de ayer"),
        ]}
        mock_h.return_value = {"events": [
            _event("e1", _day_back(1), "Lanzamiento",
                   "evento historico de ayer"),
        ]}
        calls, orig = _no_memory_search()
        try:
            ctx = ConversationContext()
            r = think("que paso ayer", context=ctx)
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig
        assert "memoria personal de ayer" in r
        assert "evento historico de ayer" not in r
        assert mock_oa.call_count == 0
        assert calls["n"] == 1
        assert ctx.conversation_mode == "memory"

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_history")
    @patch("services.archive.get_memories")
    def test_events_vacio_falso_negativo_corregido(
        self, mock_env, mock_h, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_env.return_value = {"memories": [
            _mem("v", _day_back(5),
                 "recuerdo fuera de la ventana"),
        ]}
        mock_h.return_value = {"events": [
            _event("e1", _day_back(5), "Viejo",
                   "evento fuera de la ventana"),
        ]}
        calls, orig = _no_memory_search()
        try:
            ctx = ConversationContext()
            r = think("que acontecio ayer", context=ctx)
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig
        assert (
            "No encontré información "
            "registrada en el archivo."
            in r
        )
        assert "No tengo memorias" not in r
        assert "recuerdo fuera de la ventana" not in r
        assert mock_oa.call_count == 0
        assert calls["n"] == 1
        assert ctx.conversation_mode == "archive"

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_acontecio_desnudo_g6(
        self, mock_env, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_env.return_value = {"memories": [
            _mem("r", _day_back(1), "memoria personal"),
        ]}
        calls, orig = _no_memory_search()
        try:
            ctx = ConversationContext()
            r = think("que acontecio", context=ctx)
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig
        assert "Inicio de la d" in r
        assert "memoria personal" not in r
        assert "No tengo memorias" not in r
        assert r != "OLLAMA"
        assert mock_oa.call_count == 0
        assert calls["n"] == 0
        assert ctx.conversation_mode == "archive"
        assert ctx.last_intent == ARCHIVE_SEARCH

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_history")
    @patch("services.archive.get_memories")
    def test_acontecio_sobre_kanye_ayer(
        self, mock_env, mock_h, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_env.return_value = {"memories": []}
        target = _day_back(1)
        mock_h.return_value = {"events": [
            _event("e1", target, "Show",
                   "kanye toco en vivo en la plaza"),
            _event("e2", _day_back(0), "Hoy",
                   "reunion de kanye hoy"),
        ]}
        calls, orig = _no_memory_search()
        try:
            ctx = ConversationContext()
            r = think(
                "que acontecio sobre kanye ayer",
                context=ctx,
            )
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig
        assert "kanye toco en vivo" in r
        assert "reunion de kanye hoy" not in r
        assert mock_oa.call_count == 0
        assert calls["n"] == 1
        assert ctx.conversation_mode == "archive"

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_history")
    @patch("services.archive.get_memories")
    def test_acontecimientos_semana_pasada(
        self, mock_env, mock_h, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        start, _ = _week_bounds(-1)
        mock_env.return_value = {"memories": [
            _mem("m", start, "guardia de laboratorio"),
        ]}
        mock_h.return_value = {"events": [
            _event("e1", start, "Jornada",
                   "evento de la semana pasada"),
            _event("e2", _day_back(0), "Hoy",
                   "evento de esta semana"),
        ]}
        calls, orig = _no_memory_search()
        try:
            ctx = ConversationContext()
            r = think(
                "que acontecimientos hubo "
                "la semana pasada",
                context=ctx,
            )
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig
        assert "evento de la semana pasada" in r
        assert "evento de esta semana" not in r
        assert mock_oa.call_count == 0
        assert calls["n"] == 1
        assert ctx.conversation_mode == "archive"

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_history")
    @patch("services.archive.get_memories")
    def test_acontecio_con_maria_hace_3_dias(
        self, mock_env, mock_h, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_env.return_value = {"memories": []}
        target = _day_back(3)
        mock_h.return_value = {"events": [
            _event("e1", target, "Taller",
                   "sesion con maria hace 3 dias"),
            _event("e2", _day_back(0), "Hoy",
                   "reunion de maria hoy"),
        ]}
        calls, orig = _no_memory_search()
        try:
            ctx = ConversationContext()
            r = think(
                "que acontecio con maria hace 3 dias",
                context=ctx,
            )
        finally:
            import brain.core as coremod
            coremod.search_deca_memory = orig
        assert "sesion con maria hace 3 dias" in r
        assert "reunion de maria hoy" not in r
        assert mock_oa.call_count == 0
        assert calls["n"] == 1
        assert ctx.conversation_mode == "archive"

    @patch("brain.core.ask_ollama")
    def test_g2_fuera_de_alcance_se_mantiene(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        r = think(
            "que acontecimientos de deca hubo ayer",
            context=ConversationContext(),
        )
        assert r == "OLLAMA"
        assert mock_oa.call_count == 1

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_g6_restantes_intactas(
        self, mock_env, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_env.return_value = {"memories": []}
        for ask in (
            "que paso",
            "que sucedio",
            "que ocurrio",
            "que hubo",
        ):
            calls, orig = _no_memory_search()
            try:
                ctx = ConversationContext()
                r = think(ask, context=ctx)
            finally:
                import brain.core as coremod
                coremod.search_deca_memory = orig
            assert "Inicio de la d" in r, ask
            assert mock_oa.call_count == 0, ask
            assert calls["n"] == 0, ask
            assert ctx.conversation_mode == "archive", ask

    @patch("brain.core.ask_ollama")
    @patch("services.archive.get_memories")
    def test_g7_memory_no_recuerdo_intacta(
        self, mock_env, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        mock_env.return_value = {"memories": [
            _mem("hoy", _day_back(0), "terminar decia"),
        ]}
        r = think(
            "que paso sobre kanye la semana pasada",
            context=ConversationContext(),
        )
        assert "No recuerdo nada sobre kanye." in r
        assert mock_oa.call_count == 0