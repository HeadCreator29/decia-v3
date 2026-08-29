"""
PHASE 7.2 — CONTEXT SAFETY & REFERENCE RESOLUTION
"""
import sys

from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "app"),
)

from unittest.mock import patch

import pytest

from brain.core import think
from brain.context import ConversationContext
from brain.followup import (
    resolve_follow_up,
    CONTEXT_CLARIFY,
)
from brain.handlers import (
    filter_memories_by_entity,
    is_deictic_entity,
)

from brain.intent_types import (
    ARCHIVE_SEARCH,
    MEMORY_SEARCH,
    DATE,
    TIME,
)


DUMP_MARKERS = [
    "mi color favorito es azul",
    "mi perro se llama Max",
    "quiero terminar decia esta semana",
    "manana tengo clase",
]


def new_context():
    return ConversationContext(max_turns=10)


def _mem_result():
    return {
        "type": "memory",
        "field": "memories",
        "data": [
            {
                "id": "m1",
                "description": "mi color favorito es azul",
                "date": "2026-08-27",
            },
            {
                "id": "m2",
                "description": "me gusta la musica de Kanye",
                "date": "2026-08-27",
            },
        ],
    }


class TestIsDeicticEntity:

    def test_pronombres_deicticos(self):
        for p in ["este", "esta", "esto", "ese", "esa",
                  "eso", "aquello", "el", "ella",
                  "lo mismo"]:
            assert is_deictic_entity(p), p

    def test_el_con_acento(self):
        assert is_deictic_entity("él")

    def test_entidad_real_no_deictica(self):
        assert not is_deictic_entity("kanye")
        assert not is_deictic_entity("deca")

    def test_frase_no_deictica(self):
        assert not is_deictic_entity("este lunes")
        assert not is_deictic_entity("esa cancion")
        assert not is_deictic_entity("el coche")

    def test_vacio_no_deictico(self):
        assert not is_deictic_entity("")
        assert not is_deictic_entity(None)


class TestA_NoDumpConEntidadVacia:

    def test_filtro_devuelve_none_si_solo_stopwords(self):
        for e in ["el", "la", "los", "las", "del", "lo"]:
            assert filter_memories_by_entity(
                _mem_result(), e,
            ) is None, e

    def test_filtro_entidad_real_intacto(self):
        result = filter_memories_by_entity(
            _mem_result(), "kanye",
        )
        assert result is not None
        descs = [
            m["description"]
            for m in result["data"]
        ]
        assert "me gusta la musica de Kanye" in descs
        assert "mi color favorito es azul" not in descs

    @patch("brain.core.ask_ollama")
    def test_que_recuerdas_sobre_el_no_dump(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        ctx = new_context()
        r = think("que recuerdas sobre el",
                  context=ctx)
        for marker in DUMP_MARKERS:
            assert marker not in r, marker
        mock_oa.assert_not_called()

    @patch("brain.core.ask_ollama")
    def test_que_hay_registrado_sobre_el_no_dump(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        ctx = new_context()
        r = think("que hay registrado sobre el",
                  context=ctx)
        for marker in DUMP_MARKERS:
            assert marker not in r, marker
        mock_oa.assert_not_called()


class TestB_PronombresSinReferente_Aclaracion:

    @pytest.mark.parametrize("ask", [
        "que recuerdas sobre este",
        "que recuerdas sobre eso",
        "que recuerdas sobre el",
        "que recuerdas sobre ella",
        "que recuerdas sobre lo mismo",
        "que hay registrado sobre eso",
    ])
    def test_pronombre_frio_aclaracion(self, ask):
        r = think(ask, context=new_context())
        assert r == "¿Sobre qué?", ask

    @pytest.mark.parametrize("ask", [
        "y sobre eso",
        "y este",
        "y esto",
        "sobre eso",
        "y lo mismo",
        "y sobre el",
    ])
    def test_followup_frio_aclaracion(self, ask):
        r = think(ask, context=new_context())
        assert r == "¿Sobre qué?", ask

    def test_aclaracion_no_persiste_entidad(self):
        ctx = new_context()
        think("y sobre eso", context=ctx)
        assert ctx.last_entity is None


class TestB_PronombreConReferente:

    def _kanye_ctx(self):
        ctx = new_context()
        with patch("brain.core.ask_ollama",
                   return_value="OLLAMA"):
            think("que recuerdas sobre kanye",
                  context=ctx)
        return ctx

    @pytest.mark.parametrize("ask", [
        "y sobre eso",
        "y este",
        "y esto",
        "y sobre el",
        "y lo mismo",
        "y aquello",
        "que recuerdas sobre este",
    ])
    def test_memoria_pronombre_redirige_a_kanye(
        self, ask,
    ):
        ctx = self._kanye_ctx()
        with patch("brain.core.ask_ollama",
                   return_value="OLLAMA") as mo:
            r = think(ask, context=ctx)
        assert "kanye" in r.lower(), (ask, r)
        assert "mi color favorito es azul" not in r
        assert ctx.last_entity == "kanye"
        mo.assert_not_called()

    def test_archivo_pronombre_redirige_a_deca(self):
        ctx = new_context()
        with patch("brain.core.ask_ollama",
                   return_value="OLLAMA"):
            think("que hay registrado sobre deca",
                  context=ctx)
        with patch("brain.core.ask_ollama",
                   return_value="OLLAMA") as mo:
            r = think("y sobre eso", context=ctx)
        assert "OLLAMA" not in r
        assert ctx.last_entity == "deca"
        mo.assert_not_called()

    def test_archivo_pronombre_usa_antecedente(self):
        ctx = new_context()
        ctx.set_context(ARCHIVE_SEARCH,
                        mode="archive",
                        entity="deca",
                        source_message="que hay registrado")
        intent, message = resolve_follow_up(
            "y sobre eso", ctx,
        )
        assert intent == ARCHIVE_SEARCH
        assert "sobre deca" in message
        assert "eso" not in message

    def test_no_se_guarda_el_pronombre(self):
        resolved = resolve_follow_up(
            "y sobre eso", self._kanye_ctx(),
        )
        assert resolved is not None
        intent, message = resolved
        assert intent == MEMORY_SEARCH
        assert "kanye" in message
        assert "eso" not in message


class TestC_GateDeDominio:

    @patch("brain.core.ask_ollama")
    def test_memoria_y_valores_no_sirve_archivo(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        ctx = new_context()
        with patch("brain.core.ask_ollama",
                   return_value="OLLAMA"):
            think("que recuerdas sobre kanye",
                  context=ctx)
        r = think("y valores", context=ctx)
        assert r == "No recuerdo nada sobre valores."
        assert "autenticidad" not in r
        mock_oa.assert_not_called()

    @patch("brain.core.ask_ollama")
    def test_archivo_y_valores_si_sirve_archivo(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        ctx = new_context()
        with patch("brain.core.ask_ollama",
                   return_value="OLLAMA"):
            think("que hay registrado sobre deca",
                  context=ctx)
        r = think("y valores", context=ctx)
        assert "valores fundamentales de DECA" in r
        mock_oa.assert_not_called()

    @patch("brain.core.ask_ollama")
    def test_cambio_explicito_entidad_mantiene_tema(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        ctx = new_context()
        with patch("brain.core.ask_ollama",
                   return_value="OLLAMA"):
            think("que recuerdas sobre kanye",
                  context=ctx)
        r = think("y sobre maria", context=ctx)
        assert r == "No recuerdo nada sobre maria."
        assert ctx.last_entity == "maria"
        mock_oa.assert_not_called()


class TestD_FollowUpTemporalMinimo:

    @patch("brain.core.ask_ollama")
    def test_date_y_la_hora_time(self, mock_oa):
        mock_oa.return_value = "OLLAMA"
        ctx = new_context()
        think("que dia es", context=ctx)
        r = think("y la hora", context=ctx)
        assert r.startswith("Son las") or r.startswith(
            "Es la"
        )
        mock_oa.assert_not_called()

    @patch("brain.core.ask_ollama")
    def test_time_y_el_dia_date(self, mock_oa):
        mock_oa.return_value = "OLLAMA"
        ctx = new_context()
        think("que hora es", context=ctx)
        r = think("y el dia", context=ctx)
        assert r.startswith("Hoy es")
        mock_oa.assert_not_called()

    @patch("brain.core.ask_ollama")
    def test_time_y_la_fecha_date(self, mock_oa):
        mock_oa.return_value = "OLLAMA"
        ctx = new_context()
        think("que hora es", context=ctx)
        r = think("y la fecha", context=ctx)
        assert r.startswith("Hoy es")
        mock_oa.assert_not_called()

    @patch("brain.core.ask_ollama")
    def test_date_y_la_hora_sin_ollama_persiste(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        ctx = new_context()
        think("que dia es", context=ctx)
        r = think("y la hora", context=ctx)
        assert ctx.last_intent == TIME
        mock_oa.assert_not_called()

    def test_resolver_unitario(self):
        ctx = new_context()
        ctx.set_context(DATE, mode="time",
                        source_message="que dia es")
        intent, msg = resolve_follow_up(
            "y la hora", ctx,
        )
        assert intent == TIME
        assert msg == "que hora es"

        ctx = new_context()
        ctx.set_context(TIME, mode="time",
                        source_message="que hora es")
        intent, msg = resolve_follow_up(
            "y el dia", ctx,
        )
        assert intent == DATE
        assert msg == "que dia es hoy"

        intent, msg = resolve_follow_up(
            "y la fecha", ctx,
        )
        assert intent == DATE

    def test_patrones_previos_intactos(self):
        ctx = new_context()
        ctx.set_context(TIME, mode="time",
                        source_message="que hora es")
        intent, msg = resolve_follow_up(
            "y que dia", ctx,
        )
        assert intent == DATE

        ctx = new_context()
        ctx.set_context(DATE, mode="time",
                        source_message="que dia es")
        intent, msg = resolve_follow_up(
            "y que hora", ctx,
        )
        assert intent == TIME

    def test_y_ayer_despues_time_no_inventa(self):
        ctx = new_context()
        ctx.set_context(DATE, mode="time",
                        source_message="que dia es")
        assert (
            resolve_follow_up("y ayer", ctx)
            is None
        )


class TestYQueMasYCambiosDeTema:

    @patch("brain.core.ask_ollama")
    def test_y_que_mas_memoria_repite(self, mock_oa):
        mock_oa.return_value = "OLLAMA"
        ctx = new_context()
        with patch("brain.core.ask_ollama",
                   return_value="OLLAMA"):
            think("que recuerdas sobre kanye",
                  context=ctx)
        r = think("y que mas", context=ctx)
        assert "kanye" in r.lower()
        assert ctx.last_entity == "kanye"
        mock_oa.assert_not_called()

    @patch("brain.core.ask_ollama")
    def test_cambio_modo_memory_a_archive(self,
                                          mock_oa):
        mock_oa.return_value = "OLLAMA"
        ctx = new_context()
        with patch("brain.core.ask_ollama",
                   return_value="OLLAMA"):
            think("que recuerdas sobre kanye",
                  context=ctx)
        with patch("brain.core.ask_ollama",
                   return_value="OLLAMA"):
            think("que hay registrado sobre eventos",
                  context=ctx)
        assert ctx.last_intent == ARCHIVE_SEARCH
        assert ctx.last_entity == "eventos"
        r = think("y valores", context=ctx)
        assert "valores fundamentales de DECA" in r

    @patch("brain.core.ask_ollama")
    def test_cambio_tema_temporal_a_memoria(
        self, mock_oa,
    ):
        mock_oa.return_value = "OLLAMA"
        ctx = new_context()
        think("que dia es", context=ctx)
        with patch("brain.core.ask_ollama",
                   return_value="OLLAMA"):
            think("que recuerdas sobre kanye",
                  context=ctx)
        assert ctx.last_intent == MEMORY_SEARCH
        assert ctx.last_entity == "kanye"