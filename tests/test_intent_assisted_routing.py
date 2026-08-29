import sys

from pathlib import Path

import pytest

from unittest.mock import patch, call

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "app"),
)

from brain.intent_layer import IntentLayer

from brain.intent_types import (
    GREETING,
    THANKS,
    DECIA_SELF,
    DECIA_CREATOR,
    USER_NAME_ASK,
    USER_NAME_SET,
    PREFERRED_NAME_ASK,
    PREFERRED_NAME_SET,
    CALCULATE,
    TIME,
    DATE,
    MEMORY_CREATE,
    MEMORY_SEARCH,
    ARCHIVE_DIRECT,
    ARCHIVE_SEARCH,
    EXIT,
    AMBIGUOUS_INPUT,
    FREE_TALK,
    CONFIDENCE_SEGURO,
)

from brain.core import think, _SAFE_INTENTS

from brain.handlers import (
    quick_response,
    identity_response,
    personal_identity_handler,
    calculate,
    memory_request,
    archive_response,
    search_deca_memory,
    ambiguous_input_response,
)

il = IntentLayer()


@pytest.fixture(scope="module", autouse=True)
def a16b_archive_aislado(tmp_path_factory):
    import shutil
    import services.archive as archive_mod

    real_path = archive_mod.ARCHIVE_PATH
    tmp_path = tmp_path_factory.mktemp("a16b_archive")
    if real_path.is_dir():
        for item in real_path.iterdir():
            if item.is_file():
                shutil.copy2(item, tmp_path / item.name)
    archive_mod.ARCHIVE_PATH = tmp_path
    yield tmp_path
    archive_mod.ARCHIVE_PATH = real_path


# ==========================================
# 1. SAFE INTENTS DEFINITION
# ==========================================


class TestSafeIntentsDefinition:

    def test_only_seven_safe_intents(self):

        assert len(_SAFE_INTENTS) == 9

    def test_greeting_is_safe(self):

        assert GREETING in _SAFE_INTENTS

    def test_thanks_is_safe(self):

        assert THANKS in _SAFE_INTENTS

    def test_calculate_is_safe(self):

        assert CALCULATE in _SAFE_INTENTS

    def test_exit_is_safe(self):

        assert EXIT in _SAFE_INTENTS

    def test_decia_self_is_safe(self):

        assert DECIA_SELF in _SAFE_INTENTS

    def test_decia_creator_is_safe(self):

        assert DECIA_CREATOR in _SAFE_INTENTS

    def test_user_name_ask_not_safe(self):

        assert USER_NAME_ASK not in _SAFE_INTENTS

    def test_user_name_set_not_safe(self):

        assert USER_NAME_SET not in _SAFE_INTENTS

    def test_preferred_name_ask_not_safe(self):

        assert PREFERRED_NAME_ASK not in _SAFE_INTENTS

    def test_preferred_name_set_not_safe(self):

        assert PREFERRED_NAME_SET not in _SAFE_INTENTS

    def test_memory_create_not_safe(self):

        assert MEMORY_CREATE not in _SAFE_INTENTS

    def test_memory_search_not_safe(self):

        assert MEMORY_SEARCH not in _SAFE_INTENTS

    def test_archive_direct_is_safe(self):

        assert ARCHIVE_DIRECT in _SAFE_INTENTS

    def test_archive_search_not_safe(self):

        assert ARCHIVE_SEARCH not in _SAFE_INTENTS

    def test_ambiguous_input_not_safe(self):

        assert AMBIGUOUS_INPUT not in _SAFE_INTENTS

    def test_free_talk_not_safe(self):

        assert FREE_TALK not in _SAFE_INTENTS


# ==========================================
# 2. ASSISTED ROUTING: GREETING
# ==========================================


class TestAssistedRoutingGreeting:

    def test_hola_returns_greeting_response(self):

        r = think("hola")
        assert r is not None
        assert "DECIA" in r

    def test_buenas_returns_greeting_response(self):

        r = think("buenas")
        assert r is not None

    def test_buenos_dias_returns_greeting(self):

        r = think("buenos dias")
        assert r is not None
        assert "DECIA" in r

    def test_buenas_tardes_returns_greeting(self):

        r = think("buenas tardes")
        assert r is not None

    def test_buenas_noches_returns_greeting(self):

        r = think("buenas noches")
        assert r is not None

    @patch("brain.core.quick_response")
    def test_hola_calls_quick_response_directly(
        self, mock_qr,
    ):

        mock_qr.return_value = "mocked greeting"

        r = think("hola")

        mock_qr.assert_called_with("hola")
        assert r == "mocked greeting"

    @patch("brain.core.quick_response")
    def test_bypasses_identity_chain_for_greeting(
        self, mock_qr,
    ):

        mock_qr.return_value = "mocked greeting"

        with patch(
            "brain.core.identity_response"
        ) as mock_id, patch(
            "brain.core.personal_identity_handler"
        ) as mock_pi, patch(
            "brain.core.calculate"
        ) as mock_calc, patch(
            "brain.core.ambiguous_input_response"
        ) as mock_amb:

            think("hola")

            mock_id.assert_not_called()
            mock_pi.assert_not_called()
            mock_calc.assert_not_called()
            mock_amb.assert_not_called()


# ==========================================
# 3. ASSISTED ROUTING: THANKS
# ==========================================


class TestAssistedRoutingThanks:

    def test_gracias_returns_thanks_response(self):

        r = think("gracias")
        assert r is not None

    def test_muchas_gracias_returns_thanks(self):

        r = think("muchas gracias")
        assert r is not None

    @patch("brain.core.quick_response")
    def test_gracias_calls_quick_response_directly(
        self, mock_qr,
    ):

        mock_qr.return_value = "De nada."

        r = think("gracias")

        mock_qr.assert_called_with("gracias")
        assert r == "De nada."

    @patch("brain.core.quick_response")
    def test_bypasses_identity_chain_for_thanks(
        self, mock_qr,
    ):

        mock_qr.return_value = "De nada."

        with patch(
            "brain.core.identity_response"
        ) as mock_id, patch(
            "brain.core.personal_identity_handler"
        ) as mock_pi, patch(
            "brain.core.calculate"
        ) as mock_calc:

            think("gracias")

            mock_id.assert_not_called()
            mock_pi.assert_not_called()
            mock_calc.assert_not_called()


# ==========================================
# 4. ASSISTED ROUTING: CALCULATE
# ==========================================


class TestAssistedRoutingCalculate:

    def test_2plus2_returns_result(self):

        r = think("2+2")
        assert r == "4"

    def test_3star4plus1_returns_result(self):

        r = think("3*4+1")
        assert r == "13"

    def test_division_returns_result(self):

        r = think("(10-2)/4")
        assert r in ("2", "2.0")

    @patch("brain.core.calculate")
    def test_calls_calculate_handler_directly(
        self, mock_calc,
    ):

        mock_calc.return_value = "42"

        r = think("2+2")

        mock_calc.assert_called_with("2+2")
        assert r == "42"

    @patch("brain.core.calculate")
    def test_fallback_if_calculate_returns_none(
        self, mock_calc,
    ):
        """Si calculate() no puede ejecutar →
        la Intent Layer NO decide → fallback."""

        mock_calc.return_value = None

        with patch(
            "brain.core.ambiguous_input_response",
            return_value=None,
        ), patch(
            "brain.core.ask_ollama",
            return_value="fallback",
        ) as mock_ollama:

            r = think("2+2")

            mock_ollama.assert_called_once()
            assert r == "fallback"

    @patch("brain.core.calculate")
    def test_bypasses_earlier_handlers_for_calc(
        self, mock_calc,
    ):

        mock_calc.return_value = "4"

        with patch(
            "brain.core.identity_response",
            return_value=None,
        ) as mock_id, patch(
            "brain.core.personal_identity_handler",
            return_value=None,
        ) as mock_pi:

            think("2+2")

            mock_id.assert_not_called()
            mock_pi.assert_not_called()


# ==========================================
# 5. ASSISTED ROUTING: EXIT
# ==========================================


class TestAssistedRoutingExit:

    def test_salir_returns_exit_response(self):

        r = think("salir")
        assert r == "Hasta luego."

    def test_exit_returns_exit_response(self):

        r = think("exit")
        assert r == "Hasta luego."

    def test_quit_returns_exit_response(self):

        r = think("quit")
        assert r == "Hasta luego."

    def test_exit_bypasses_all_handlers(self):

        with patch(
            "brain.core.quick_response",
            return_value=None,
        ) as mock_qr, patch(
            "brain.core.identity_response",
            return_value=None,
        ) as mock_id:

            r = think("salir")

            mock_qr.assert_not_called()
            mock_id.assert_not_called()
            assert r == "Hasta luego."


# ==========================================
# 6. NEGATIVE / FALLBACK
# ==========================================


class TestAssistedRoutingFallback:

    @patch("brain.core.identity_response")
    def test_quien_eres_uses_original_routing(
        self, mock_id,
    ):

        mock_id.return_value = "Soy DECIA"

        r = think("quién eres")

        mock_id.assert_called_once()
        assert r == "Soy DECIA"

    @patch("brain.core.identity_response")
    def test_quien_te_creo_uses_original_routing(
        self, mock_id,
    ):

        mock_id.return_value = "Fui creada por Idelvi"

        r = think("quién te creó")

        mock_id.assert_called_once()
        assert r == "Fui creada por Idelvi"

    @patch("brain.core.personal_identity_handler")
    def test_como_me_llamo_uses_original_routing(
        self, mock_pi,
    ):

        mock_pi.return_value = "Tu nombre es Idelvi"

        r = think("cómo me llamo")

        mock_pi.assert_called_once()
        assert r == "Tu nombre es Idelvi"

    @patch("brain.core.memory_request")
    def test_guarda_que_uses_original_routing(
        self, mock_mr,
    ):

        mock_mr.return_value = "tengo clase"

        with patch(
            "brain.core.create_memory",
            return_value={
                "date": "2026-08-26",
                "time": None,
            },
        ):

            r = think("guarda que tengo clase")

            mock_mr.assert_called_once()

    @patch("brain.core.search_deca_memory")
    def test_que_recuerdas_uses_original_routing(
        self, mock_sd,
    ):

        mock_sd.return_value = None

        with patch(
            "brain.core.ambiguous_input_response",
            return_value="¿Sí?",
        ):

            r = think("qué recuerdas")

            mock_sd.assert_called_once()

    @patch("brain.core.archive_response")
    def test_que_significa_deca_uses_original_routing(
        self, mock_ar,
    ):

        mock_ar.return_value = "DECA significa..."

        r = think("qué significa DECA")

        mock_ar.assert_called_once()
        assert r == "DECA significa..."

    @patch("brain.core.ambiguous_input_response")
    def test_algo_uses_original_routing(
        self, mock_ai,
    ):

        mock_ai.return_value = "¿Sí? ¿Qué necesitas?"

        r = think("algo")

        mock_ai.assert_called_once()
        assert r == "¿Sí? ¿Qué necesitas?"

    @patch("brain.core.ask_ollama")
    def test_cuename_un_chiste_reaches_ollama(
        self, mock_oa,
    ):

        mock_oa.return_value = "Chiste de Ollama"

        r = think("cuéntame un chiste gracioso")

        mock_oa.assert_called_once()
        assert r == "Chiste de Ollama"

    @patch("brain.core.ask_ollama")
    def test_non_safe_never_uses_assisted_routing(
        self, mock_oa,
    ):
        """Intentos que no son safe NUNCA deben
        ser procesados por assisted routing."""

        mock_oa.return_value = "Ollama"

        non_safe = [
            "quién eres",
            "quién te creó",
            "cómo me llamo",
            "guarda que tengo clase",
            "qué recuerdas",
            "qué significa DECA",
            "algo",
            "cuéntame un chiste",
        ]

        for phrase in non_safe:

            with patch(
                "brain.core.quick_response",
                return_value=None,
            ):

                r = think(phrase)

                assert r is not None


# ==========================================
# 7. CONFIDENCE THRESHOLD
# ==========================================


class TestConfidenceThreshold:

    def test_greeting_confidence_is_seguro(self):

        r = il.classify("hola")
        assert r.confidence >= CONFIDENCE_SEGURO

    def test_thanks_confidence_is_seguro(self):

        r = il.classify("gracias")
        assert r.confidence >= CONFIDENCE_SEGURO

    def test_calculate_confidence_is_seguro(self):

        r = il.classify("2+2")
        assert r.confidence >= CONFIDENCE_SEGURO

    def test_exit_confidence_is_seguro(self):

        r = il.classify("salir")
        assert r.confidence >= CONFIDENCE_SEGURO

    def test_all_safe_intents_above_threshold(self):

        phrases = {
            GREETING: ["hola", "buenas",
                       "buenos dias"],
            THANKS: ["gracias", "muchas gracias"],
            CALCULATE: ["2+2", "3*4+1",
                        "(10-2)/4"],
            EXIT: ["salir", "exit", "quit"],
        }

        for intent, test_phrases in phrases.items():

            for phrase in test_phrases:

                r = il.classify(phrase)

                assert r.confidence >= 0.90, (
                    f"{intent} confidence too "
                    f"low for '{phrase}': "
                    f"{r.confidence}"
                )

    def test_non_safe_intents_below_threshold(
        self,
    ):
        """Intentos no-safe que NO deben tener
        assisted routing."""

        phrases_below = [
            ("algo", AMBIGUOUS_INPUT),
            ("cuéntame un chiste", FREE_TALK),
            ("qué recuerdas", MEMORY_SEARCH),
        ]

        for phrase, _ in phrases_below:

            r = il.classify(phrase)

            assert r.confidence < 0.90 \
                or r.intent not in _SAFE_INTENTS, (
                f"'{phrase}' should not be "
                f"auto-routable: "
                f"intent={r.intent} "
                f"conf={r.confidence}"
            )

    def test_all_high_confidence_intents_are_safe(
        self,
    ):
        """Phase 2C: todo intent con confidence >= 0.90
        DEBE ser safe intent. Si llega aquí con conf
        alta y no es safe, algo falló."""

        high_conf_intents = set()
        test_phrases = [
            "hola", "gracias", "salir", "2+2",
            "quién eres", "quién te creo",
            "cuándo comenzó deca",
            "qué significa deca",
            "cuéntame la historia",
        ]
        for phrase in test_phrases:
            r = il.classify(phrase)
            if r.confidence >= 0.90:
                high_conf_intents.add(r.intent)

        for intent in high_conf_intents:
            assert intent in _SAFE_INTENTS, (
                f"{intent} has confidence >= 0.90 "
                f"but is NOT in _SAFE_INTENTS"
            )

    @patch("brain.core.quick_response")
    def test_high_confidence_non_safe_not_routed(
        self, mock_qr,
    ):
        """DECIA_SELF tiene confidence alta pero
        no está en safe intents → no se ejecuta
        assisted routing. El routing normal SÍ
        pasa por quick_response."""

        mock_qr.return_value = None

        with patch(
            "brain.core.identity_response",
            return_value="Soy DECIA",
        ) as mock_id:

            r = think("quién eres")

            mock_id.assert_called_once()
            assert r == "Soy DECIA"


# ==========================================
# 8. LOG FORMAT
# ==========================================


class TestObservationLog:

    def test_log_contains_used_field(self, capsys):

        think("hola")

        output = capsys.readouterr().out

        assert "used=" in output

    def test_log_contains_reason_field(
        self, capsys,
    ):

        think("hola")

        output = capsys.readouterr().out

        assert "reason=" in output

    def test_log_used_true_for_safe_intent(
        self, capsys,
    ):

        think("hola")

        output = capsys.readouterr().out

        assert "used=True" in output

    def test_log_used_false_for_non_safe(
        self, capsys,
    ):

        think("algo")

        output = capsys.readouterr().out

        assert "used=False" in output

    def test_log_reason_high_confidence(
        self, capsys,
    ):

        think("hola")

        output = capsys.readouterr().out

        assert (
            "reason=high_confidence_safe_intent"
            in output
        )

    def test_log_reason_below_threshold(
        self, capsys,
    ):

        think("algo")

        output = capsys.readouterr().out

        assert "reason=below_threshold" in output

    def test_log_contains_intent_and_confidence(
        self, capsys,
    ):

        think("hola")

        output = capsys.readouterr().out

        assert "intent=GREETING" in output
        assert "confidence=" in output

    def test_log_calculate_used_true(self, capsys):

        think("2+2")

        output = capsys.readouterr().out

        assert "intent=CALCULATE" in output
        assert "used=True" in output

    def test_log_exit_used_true(self, capsys):

        think("salir")

        output = capsys.readouterr().out

        assert "intent=EXIT" in output
        assert "used=True" in output

    def test_log_thanks_used_true(self, capsys):

        think("gracias")

        output = capsys.readouterr().out

        assert "intent=THANKS" in output
        assert "used=True" in output

    def test_log_decia_self_used_true(
        self, capsys,
    ):
        """Phase 2C: DECIA_SELF es safe intent
        → used=True."""

        think("quién eres")

        output = capsys.readouterr().out

        assert "intent=DECIA_SELF" in output
        assert "used=True" in output


# ==========================================
# 9. CRITICAL REGRESSION
# ==========================================


class TestCriticalRegression:

    @patch("brain.core.identity_response")
    def test_identity_response_still_works(
        self, mock_id,
    ):

        mock_id.return_value = (
            "Soy DECIA, tu asistente"
        )

        r = think("quién eres")

        mock_id.assert_called_once()
        assert r == "Soy DECIA, tu asistente"

    @patch("brain.core.personal_identity_handler")
    def test_personal_identity_handler_still_works(
        self, mock_pi,
    ):

        mock_pi.return_value = "Tu nombre es Idelvi"

        r = think("cómo me llamo")

        mock_pi.assert_called_once()
        assert r == "Tu nombre es Idelvi"

    @patch("brain.core.memory_request")
    def test_memory_request_still_works(
        self, mock_mr,
    ):

        mock_mr.return_value = "tengo clase"

        with patch(
            "brain.core.create_memory",
            return_value={
                "date": "2026-08-26",
                "time": None,
            },
        ) as mock_cm:

            r = think("guarda que tengo clase")

            mock_mr.assert_called_once()
            mock_cm.assert_called_once()

    @patch("brain.core.archive_response")
    def test_archive_response_still_works(
        self, mock_ar,
    ):

        mock_ar.return_value = (
            "Los valores son: a, b, c."
        )

        r = think("valores de DECA")

        mock_ar.assert_called_once()
        assert r == "Los valores son: a, b, c."

    @patch("brain.core.search_deca_memory")
    def test_search_deca_memory_still_works(
        self, mock_sd,
    ):

        mock_sd.return_value = None

        with patch(
            "brain.core.ambiguous_input_response",
            return_value=None,
        ), patch(
            "brain.core.ask_ollama",
            return_value="Ollama",
        ):

            r = think("qué recuerdas de DECA")

            mock_sd.assert_called_once()

    @patch("brain.core.ambiguous_input_response")
    def test_ambiguous_input_still_works(
        self, mock_ai,
    ):

        mock_ai.return_value = "¿Sí? ¿Qué necesitas?"

        r = think("algo")

        mock_ai.assert_called_once()
        assert r == "¿Sí? ¿Qué necesitas?"

    @patch("brain.core.ask_ollama")
    def test_ask_ollama_still_works(self, mock_oa):

        mock_oa.return_value = "Respuesta de Ollama"

        r = think(
            "¿Qué es la fotosíntesis?"
        )

        mock_oa.assert_called_once()
        assert r == "Respuesta de Ollama"

    @patch("brain.core.ask_ollama")
    def test_ollama_receives_context(
        self, mock_oa,
    ):
        """Verificar que Ollama recibe contexto
        cuando se pasa un context object."""

        mock_oa.return_value = "Respuesta"

        from brain.context import (
            ConversationContext,
        )

        ctx = ConversationContext(max_turns=5)

        think(
            "cuéntame algo interesante", context=ctx,
        )

        mock_oa.assert_called_once()

        _, kwargs = mock_oa.call_args

        assert "context" in kwargs


# ==========================================
# 10. INTENT LAYER INTEGRATION
# ==========================================


class TestIntentLayerIntegration:

    def test_classify_still_works_independently(
        self,
    ):
        """IntentLayer.classify() no cambia.
        Solo core.py decide si usar el resultado."""

        r = il.classify("hola")
        assert r.intent == GREETING
        assert r.confidence >= 0.90

    def test_classify_all_intents_still_reachable(
        self,
    ):
        """Todos los 16 intents siguen siendo
        alcanzables por classify()."""

        phrases = {
            GREETING: "hola",
            THANKS: "gracias",
            DECIA_SELF: "quién eres",
            DECIA_CREATOR: "quién te creó",
            USER_NAME_ASK: "quién soy",
            USER_NAME_SET: "mi nombre es Pedro",
            PREFERRED_NAME_ASK:
                "cómo quieres llamarme",
            PREFERRED_NAME_SET: "llámame Creador",
            CALCULATE: "2+2",
            MEMORY_CREATE:
                "guarda que tengo clase",
            MEMORY_SEARCH: "qué recuerdas",
            ARCHIVE_DIRECT:
                "qué significa DECA",
            ARCHIVE_SEARCH: "historia de DECA",
            EXIT: "salir",
            AMBIGUOUS_INPUT: "algo",
            FREE_TALK: "cuéntame un chiste",
        }

        for intent, phrase in phrases.items():

            r = il.classify(phrase)
            assert r.intent == intent, (
                f"Intent {intent} not reached "
                f"with '{phrase}'"
            )

    def test_sixteen_intents_total(self):

        all_intents = set()

        phrases = [
            "hola", "gracias", "quién eres",
            "quién te creó", "quién soy",
            "mi nombre es Pedro",
            "cómo quieres llamarme",
            "llámame Creador", "2+2",
            "guarda que tengo clase",
            "qué recuerdas",
            "qué significa DECA",
            "historia de DECA", "salir",
            "algo", "cuéntame un chiste",
        ]

        for phrase in phrases:

            r = il.classify(phrase)
            all_intents.add(r.intent)

        assert len(all_intents) == 16


# ==========================================
# 11. CALCULATE SAFETY RULE
# ==========================================


class TestCalculateSafetyRule:

    @patch("brain.core.calculate")
    def test_calc_returns_none_falls_through(
        self, mock_calc,
    ):
        """Si Intent Layer dice CALCULATE pero
        calculate() no puede ejecutar →
        la acción NO se ejecuta → fallback."""

        mock_calc.return_value = None

        with patch(
            "brain.core.ambiguous_input_response",
            return_value=None,
        ), patch(
            "brain.core.ask_ollama",
            return_value="fallback",
        ) as mock_oa:

            r = think("2+2")

            mock_oa.assert_called_once()
            assert r == "fallback"

    @patch("brain.core.calculate")
    def test_calc_returns_result_uses_it(
        self, mock_calc,
    ):
        """Si calculate() retorna resultado →
        se usa directamente."""

        mock_calc.return_value = "4"

        r = think("2+2")

        mock_calc.assert_called_once()
        assert r == "4"


# ==========================================
# 12. WRITE INTENTS STILL OUTSIDE
# ==========================================


class TestWriteIntentsOutside:

    def test_user_name_set_not_in_safe(self):

        assert USER_NAME_SET not in _SAFE_INTENTS

    def test_preferred_name_set_not_in_safe(self):

        assert (
            PREFERRED_NAME_SET not in _SAFE_INTENTS
        )

    def test_memory_create_not_in_safe(self):

        assert MEMORY_CREATE not in _SAFE_INTENTS

    @patch("brain.core.personal_identity_handler")
    def test_user_name_set_uses_handler(
        self, mock_pi,
    ):

        mock_pi.return_value = (
            "Entendido. Tu nombre es Pedro."
        )

        r = think("mi nombre es Pedro")

        mock_pi.assert_called_once()
        assert "Pedro" in r

    @patch("brain.core.personal_identity_handler")
    def test_preferred_name_set_uses_handler(
        self, mock_pi,
    ):

        mock_pi.return_value = (
            "De ahora en adelante te llamaré Jefe."
        )

        r = think("llámame Jefe")

        mock_pi.assert_called_once()

    @patch("brain.core.memory_request")
    def test_memory_create_uses_handler(
        self, mock_mr,
    ):

        mock_mr.return_value = "tengo clase"

        with patch(
            "brain.core.create_memory",
            return_value={
                "date": "2026-08-26",
                "time": None,
            },
        ) as mock_cm:

            r = think("guarda que tengo clase")

            mock_mr.assert_called_once()
            mock_cm.assert_called_once()


# ==========================================
# 13. EDGE CASES
# ==========================================


class TestEdgeCases:

    def test_empty_string_returns_ambiguous(self):

        r = think("")
        assert r is not None

    def test_whitespace_only_returns_ambiguous(
        self,
    ):

        r = think("   ")
        assert r is not None

    @patch("brain.core.quick_response")
    def test_greeting_with_exclamation(
        self, mock_qr,
    ):

        mock_qr.return_value = "¡Hola! Soy DECIA."

        r = think("¡Hola!")

        mock_qr.assert_called_once()
        assert r is not None

    def test_mixed_case_still_routes(self):

        r = think("HOLA")

        assert r is not None
        assert "DECIA" in r

    def test_calculate_complex_expression(self):

        r = think("(3+5)*2-1")

        assert r == "15"
