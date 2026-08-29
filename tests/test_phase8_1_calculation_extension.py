import sys
from pathlib import Path
from unittest.mock import patch
from contextlib import redirect_stdout
import io

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "app"),
)

from brain.handlers import calculate
from brain.intent_layer import IntentLayer
from brain.core import think
from brain.context import ConversationContext
from brain.intent_types import (CALCULATE, DECIA_SELF,
                                FREE_TALK, TIME)


# ==========================================
# HANDLER: GRAMÁTICA AMPLIADA
# ==========================================


class TestCalculateExtendedGrammar:

    def test_cuanto_es_15_por_3(self):
        assert calculate("cuanto es 15 por 3") == "45"

    def test_que_es_15_por_3(self):
        assert calculate("que es 15 por 3") == "45"

    def test_cuanto_es_15_x_3(self):
        assert calculate("cuanto es 15 x 3") == "45"

    def test_cuanto_es_15_x3_simbolo_multiplicacion(
        self
    ):
        assert calculate("cuanto es 15 × 3") == "45"

    def test_cuanto_es_15_x_3_con_signo(self):
        assert calculate("cuanto es 15 x 3?") == "45"

    def test_15_x_3_sin_prefijo(self):
        assert calculate("15 x 3") == "45"

    def test_15x3_compacto(self):
        assert calculate("15x3") == "45"

    def test_que_es_encadenada(self):
        assert calculate("que es 2 mas 3 por 4") == "14"

    def test_cuanto_es_encadenada(self):
        assert calculate("cuanto es 2 mas 3 por 4") == "14"

    def test_calcular_por(self):
        assert calculate("calcular 15 por 3") == "45"


class TestCalculateRegresionOperacionesPrevias:

    def test_operaciones_basicas(self):
        assert calculate("cuanto es 25 mas 17") == "42"
        assert calculate("cuanto es 100 menos 35") == "65"
        assert calculate("cuanto es 5 por 6") == "30"
        assert calculate("cuanto es 20 entre 4") == "5"

    def test_sin_prefijo(self):
        assert calculate("2 mas 2") == "4"
        assert calculate("10 menos 3") == "7"
        assert calculate("5 por 4") == "20"
        assert calculate("20 entre 5") == "4"

    def test_parentesis_y_decimales(self):
        assert calculate("(10 mas 5) por 2") == "30"
        assert calculate("2.5 por 4") == "10"
        assert calculate("10.5 mas 2.5") == "13"

    def test_math_pura(self):
        assert calculate("2+2") == "4"
        assert calculate("100/4") == "25"
        assert calculate("(10+5)*2") == "30"


class TestCalculateExpresionesInvalidas:

    def test_texto_normal_no_es_calculo(self):
        assert calculate("tengo 25 perros") is None
        assert calculate("tengo 2 cosas") is None
        assert calculate("compre 5 cosas por 4 dias") is None

    def test_frases_dec_autoconocimiento_no_calc(self):
        assert calculate("que es decia") is None
        assert calculate("que es deca") is None
        assert calculate("que es un perro") is None

    def test_vacio(self):
        assert calculate("") is None

    def test_expresion_con_invalidos_no_evalua(self):
        assert calculate("2 + 2 + primer") is None
        assert calculate("hola 2 x 3") is None


# ==========================================
# PIPELINE: DETERMINISMO Y SIN OLLAMA
# ==========================================


class TestThinkCalculationRouting:

    def _think(self, message):
        with patch(
            "brain.core.ask_ollama",
            return_value="<<OLLAMA>>",
        ) as mock_ollama:
            with redirect_stdout(
                io.StringIO()
            ):
                result = think(
                    message,
                    context=ConversationContext(),
                )
        return result, mock_ollama.called

    def test_que_es_15_por_3_determinista(self):
        result, ollama = self._think(
            "que es 15 por 3"
        )
        assert result == "45"
        assert ollama is False

    def test_cuanto_es_15_x_3_determinista(self):
        result, ollama = self._think(
            "cuanto es 15 x 3"
        )
        assert result == "45"
        assert ollama is False

    def test_cuanto_es_15_x_3_con_signo(self):
        result, ollama = self._think(
            "cuanto es 15 x 3?"
        )
        assert result == "45"
        assert ollama is False

    def test_que_es_encadenada_determinista(self):
        result, ollama = self._think(
            "que es 2 mas 3 por 4"
        )
        assert result == "14"
        assert ollama is False

    def test_cuanto_es_15_por_3_regresion(self):
        result, ollama = self._think(
            "cuanto es 15 por 3"
        )
        assert result == "45"
        assert ollama is False

    def test_single_pass_una_sola_respuesta(self):
        result, ollama = self._think(
            "que es 15 por 3"
        )
        assert isinstance(result, str)
        assert result == "45"
        assert ollama is False


class TestThinkSinCapturaDeOtrosIntents:

    def _think(self, message):
        with patch(
            "brain.core.ask_ollama",
            return_value="<<OLLAMA>>",
        ) as mock_ollama:
            with redirect_stdout(
                io.StringIO()
            ):
                result = think(
                    message,
                    context=ConversationContext(),
                )
        return result, mock_ollama.called

    def test_que_es_decia_sigue_siendo_identidad(
        self
    ):
        result, ollama = self._think("que es decia")
        assert result != "45"
        assert ollama is False

    def test_que_es_deca_sigue_siendo_archivo(
        self
    ):
        result, ollama = self._think("que es deca")
        assert result != "45"
        assert ollama is False

    def test_cuanto_es_la_hora_sigue_siendo_time(
        self
    ):
        result, ollama = self._think(
            "cuanto es la hora"
        )
        assert result is not None
        assert result != "45"
        assert ollama is False

    def test_ambigüo_no_ejecuta_calculo_incorrecto(
        self
    ):
        result, _ = self._think(
            "que es 15 por 3 manzanas"
        )
        assert result != "45"

    def test_que_es_un_perro_no_calcula(self):
        result, _ = self._think("que es un perro")
        assert result != "45"


# ==========================================
# CLASIFICACIÓN
# ==========================================


class TestClassificationCalculation:

    def setup_method(self):
        self.il = IntentLayer()

    def test_que_es_15_por_3_calculate(self):
        r = self.il.classify("que es 15 por 3")
        assert r.intent == CALCULATE

    def test_cuanto_es_15_x_3_calculate(self):
        r = self.il.classify("cuanto es 15 x 3")
        assert r.intent == CALCULATE

    def test_15_x_3_calculate(self):
        r = self.il.classify("15 x 3")
        assert r.intent == CALCULATE

    def test_que_es_decia_no_calculate(self):
        r = self.il.classify("que es decia")
        assert r.intent != CALCULATE
        assert r.intent == DECIA_SELF

    def test_que_es_un_perro_no_calculate(self):
        r = self.il.classify("que es un perro")
        assert r.intent != CALCULATE
        assert r.intent in (
            FREE_TALK,
        )

    def test_cuanto_es_la_hora_es_time(self):
        r = self.il.classify("cuanto es la hora")
        assert r.intent == TIME

    def test_cuanto_es_15_x_3_con_signo_calculate(
        self
    ):
        r = self.il.classify("cuanto es 15 x 3?")
        assert r.intent == CALCULATE