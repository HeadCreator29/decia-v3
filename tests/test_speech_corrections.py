import json
import pytest
from unittest.mock import patch, MagicMock

from utils.speech_corrections import (
    correct_transcription,
)

from transcription_interpreter import (
    check_suspicion,
    validate_ollama_response,
    CONFIDENCE_THRESHOLD,
)


# ==========================================
# CORRECCIONES CONTEXTUALES (LOCALES)
# ==========================================


class TestContextualCorrections:

    def test_planeta_martes_corregido(self):
        result = correct_transcription(
            "buscame información sobre el planeta martes"
        )
        assert "Marte" in result
        assert "martes" not in result

    def test_planeta_mal_corregido(self):
        result = correct_transcription(
            "buscame información sobre el planeta mal"
        )
        assert "Marte" in result
        assert "mal" not in result

    def test_planeta_marte_normalizado(self):
        result = correct_transcription(
            "planeta marte"
        )
        assert result == "planeta Marte"

    def test_planeta_mayuscula_martes(self):
        result = correct_transcription(
            "Qué sabes del planeta Martes"
        )
        assert "Marte" in result


# ==========================================
# PALABRAS LEGÍTIMAS NO DESTRUIDAS
# ==========================================


class TestLegitimateWordsPreserved:

    def test_hoy_es_martes(self):
        original = "hoy es martes"
        result = correct_transcription(original)
        assert result == original

    def test_eso_estuvo_mal(self):
        original = "eso estuvo mal"
        result = correct_transcription(original)
        assert result == original

    def test_sobre_el_mal(self):
        original = "quiero saber más sobre el mal"
        result = correct_transcription(original)
        assert result == original

    def test_martes_puro(self):
        original = "martes"
        result = correct_transcription(original)
        assert result == original

    def test_mal_puro(self):
        original = "mal"
        result = correct_transcription(original)
        assert result == original


# ==========================================
# PALABRAS DE DECIA (sin corrección)
# ==========================================


class TestDECIAVocabulary:

    def test_deca_no_modificado(self):
        original = "habla sobre DECA"
        result = correct_transcription(original)
        assert result == original

    def test_decia_no_modificado(self):
        original = "quién es DECIA"
        result = correct_transcription(original)
        assert result == original

    def test_deca_dream_no_modificado(self):
        original = "qué es Deca Dream"
        result = correct_transcription(original)
        assert result == original

    def test_idelvi_no_modificado(self):
        original = "quién es Idelvi"
        result = correct_transcription(original)
        assert result == original

    def test_herrera_no_modificado(self):
        original = "Herrera"
        result = correct_transcription(original)
        assert result == original


# ==========================================
# DETECTOR DE SOSPECHA
# ==========================================


class TestSuspicionDetection:

    def test_planeta_mario_es_sospechoso(self):
        result = check_suspicion(
            "busca información sobre el planeta mario"
        )
        assert result.is_suspicious is True
        assert result.suspect_word == "mario"

    def test_planeta_marvel_es_sospechoso(self):
        result = check_suspicion(
            "busca información sobre el planeta marvel"
        )
        assert result.is_suspicious is True
        assert result.suspect_word == "marvel"

    def test_planeta_martes_es_sospechoso(self):
        result = check_suspicion(
            "busca información sobre el planeta martes"
        )
        assert result.is_suspicious is True
        assert result.suspect_word == "martes"

    def test_planeta_marte_no_es_sospechoso(self):
        result = check_suspicion(
            "busca información sobre el planeta marte"
        )
        assert result.is_suspicious is False

    def test_planeta_mal_es_sospechoso(self):
        result = check_suspicion(
            "busca información sobre el planeta mal"
        )
        assert result.is_suspicious is True
        assert result.suspect_word == "mal"

    def test_hoy_es_martes_no_es_sospechoso(self):
        result = check_suspicion("hoy es martes")
        assert result.is_suspicious is False

    def test_me_gusta_mario_no_es_sospechoso(self):
        result = check_suspicion("me gusta Mario")
        assert result.is_suspicious is False

    def test_planeta_tierra_no_es_sospechoso(
        self,
    ):
        result = check_suspicion(
            "cuál es la distancia al planeta tierra"
        )
        assert result.is_suspicious is False

    def test_planeta_jupiter_no_es_sospechoso(
        self,
    ):
        result = check_suspicion(
            "cuántos satélites tiene el planeta jupiter"
        )
        assert result.is_suspicious is False

    def test_texto_vacio_no_es_sospechoso(self):
        result = check_suspicion("")
        assert result.is_suspicious is False

    def test_none_no_es_sospechoso(self):
        result = check_suspicion(None)
        assert result.is_suspicious is False

    def test_planeta_solo_no_es_sospechoso(self):
        result = check_suspicion("planeta")
        assert result.is_suspicious is False

    def test_sospecha_muestra_ventana(self):
        result = check_suspicion(
            "el planeta fantastico"
        )
        assert result.is_suspicious is True
        assert result.context_window == (
            "planeta fantastico"
        )


# ==========================================
# VALIDACIÓN DE RESPUESTA OLLAMA
# ==========================================


class TestOllamaResponseValidation:

    def test_json_valido_con_correccion(self):
        response = json.dumps({
            "should_correct": True,
            "confidence": 0.95,
            "corrected_text": (
                "busca información sobre el planeta Marte"
            ),
            "reason": "mario no es un planeta",
        })
        result = validate_ollama_response(
            response,
            "busca información sobre el planeta mario",
        )
        assert result is not None
        assert result.should_correct is True
        assert result.confidence == 0.95

    def test_json_valido_sin_correccion(self):
        response = json.dumps({
            "should_correct": False,
            "confidence": 1.0,
            "corrected_text": None,
            "reason": "frase legítima",
        })
        result = validate_ollama_response(
            response, "hoy es martes"
        )
        assert result is not None
        assert result.should_correct is False

    def test_json_con_texto_extra_se_extrae(self):
        response = (
            "Analizando transcripción...\n"
            + json.dumps({
                "should_correct": True,
                "confidence": 0.90,
                "corrected_text": (
                    "busca información sobre "
                    "el planeta Marte"
                ),
                "reason": "error de Whisper",
            })
            + "\nFin del análisis."
        )
        result = validate_ollama_response(
            response,
            "busca información sobre el planeta mario",
        )
        assert result is not None
        assert result.should_correct is True

    def test_respuesta_vacia_retorna_none(self):
        result = validate_ollama_response(
            None, "planeta mario"
        )
        assert result is None

    def test_sin_json_retorna_none(self):
        result = validate_ollama_response(
            "No encontré errores en la transcripción",
            "planeta mario",
        )
        assert result is None

    def test_json_invalido_retorna_none(self):
        result = validate_ollama_response(
            "{should_correct: true}",
            "planeta mario",
        )
        assert result is None

    def test_confianza_fuera_de_rango_retorna_none(
        self,
    ):
        response = json.dumps({
            "should_correct": True,
            "confidence": 1.5,
            "corrected_text": "planeta Marte",
            "reason": "...",
        })
        result = validate_ollama_response(
            response, "planeta mario"
        )
        assert result is None

    def test_confianza_negativa_retorna_none(self):
        response = json.dumps({
            "should_correct": True,
            "confidence": -0.1,
            "corrected_text": "planeta Marte",
            "reason": "...",
        })
        result = validate_ollama_response(
            response, "planeta mario"
        )
        assert result is None

    def test_confianza_no_numerica_retorna_none(
        self,
    ):
        response = json.dumps({
            "should_correct": True,
            "confidence": "alta",
            "corrected_text": "planeta Marte",
            "reason": "...",
        })
        result = validate_ollama_response(
            response, "planeta mario"
        )
        assert result is None

    def test_corrected_text_vacio_retorna_none(
        self,
    ):
        response = json.dumps({
            "should_correct": True,
            "confidence": 0.95,
            "corrected_text": "",
            "reason": "...",
        })
        result = validate_ollama_response(
            response, "planeta mario"
        )
        assert result is None

    def test_cambio_demasiado_grande_retorna_none(
        self,
    ):
        response = json.dumps({
            "should_correct": True,
            "confidence": 0.95,
            "corrected_text": (
                "esta es completamente otra frase "
                "que no tiene nada que ver con la original"
            ),
            "reason": "...",
        })
        result = validate_ollama_response(
            response, "planeta mario"
        )
        assert result is None

    def test_respuesta_conversacional_retorna_none(
        self,
    ):
        response = json.dumps({
            "should_correct": True,
            "confidence": 0.95,
            "corrected_text": (
                "Hola, déjame ayudarte con eso"
            ),
            "reason": "...",
        })
        result = validate_ollama_response(
            response, "algo"
        )
        assert result is None

    def test_should_correct_false_no_requiere_texto(
        self,
    ):
        response = json.dumps({
            "should_correct": False,
            "confidence": 1.0,
            "corrected_text": None,
            "reason": "todo bien",
        })
        result = validate_ollama_response(
            response, "hola"
        )
        assert result is not None
        assert result.should_correct is False


# ==========================================
# INTEGRACIÓN (CON MOCK DE OLLAMA)
# ==========================================


class TestInterpreterIntegration:

    @patch(
        "transcription_interpreter"
        ".analyze_with_ollama"
    )
    def test_sin_sospecha_no_llama_ollama(
        self, mock_analyze
    ):
        result = correct_transcription(
            "¿Quién eres?"
        )
        mock_analyze.assert_not_called()
        assert result == "¿Quién eres?"

    @patch(
        "transcription_interpreter"
        ".analyze_with_ollama"
    )
    def test_correccion_local_no_llama_ollama(
        self, mock_analyze
    ):
        result = correct_transcription(
            "planeta martes"
        )
        mock_analyze.assert_not_called()
        assert "Marte" in result

    @patch(
        "transcription_interpreter"
        ".analyze_with_ollama"
    )
    def test_sospecha_confianza_alta_acepta(
        self, mock_analyze
    ):
        mock_analyze.return_value = json.dumps({
            "should_correct": True,
            "confidence": 0.95,
            "corrected_text": (
                "busca información sobre el planeta Marte"
            ),
            "reason": "mario no es un planeta",
        })
        result = correct_transcription(
            "busca información sobre el planeta mario"
        )
        mock_analyze.assert_called_once()
        assert "Marte" in result

    @patch(
        "transcription_interpreter"
        ".analyze_with_ollama"
    )
    def test_sospecha_confianza_baja_rechaza(
        self, mock_analyze
    ):
        mock_analyze.return_value = json.dumps({
            "should_correct": True,
            "confidence": 0.60,
            "corrected_text": "planeta Marte",
            "reason": "no estoy seguro",
        })
        original = "planeta mario"
        result = correct_transcription(original)
        assert result == original

    @patch(
        "transcription_interpreter"
        ".analyze_with_ollama"
    )
    def test_sospecha_analizador_dice_no(
        self, mock_analyze
    ):
        mock_analyze.return_value = json.dumps({
            "should_correct": False,
            "confidence": 1.0,
            "corrected_text": None,
            "reason": "frase legítima",
        })
        original = "planeta mario"
        result = correct_transcription(original)
        assert result == original

    @patch(
        "transcription_interpreter"
        ".analyze_with_ollama"
    )
    def test_sospecha_error_en_ollama(
        self, mock_analyze
    ):
        mock_analyze.return_value = None
        original = "planeta mario"
        result = correct_transcription(original)
        assert result == original

    @patch(
        "transcription_interpreter"
        ".analyze_with_ollama"
    )
    def test_sospecha_respuesta_invalida(
        self, mock_analyze
    ):
        mock_analyze.return_value = (
            "No encontré errores"
        )
        original = "planeta mario"
        result = correct_transcription(original)
        assert result == original

    @patch(
        "transcription_interpreter"
        ".analyze_with_ollama"
    )
    def test_original_siempre_preservado(
        self, mock_analyze
    ):
        mock_analyze.return_value = json.dumps({
            "should_correct": True,
            "confidence": 0.95,
            "corrected_text": (
                "busca info sobre el planeta Marte"
            ),
            "reason": "...",
        })
        result = correct_transcription(
            "busca info sobre el planeta mario"
        )
        assert result == (
            "busca info sobre el planeta Marte"
        )


# ==========================================
# DEBUG OUTPUT
# ==========================================


class TestDebugOutput:

    def test_sin_correccion_local_muestra_mensaje(
        self, capsys
    ):
        correct_transcription("hoy es martes")
        captured = capsys.readouterr()
        assert "Sin corrección local" in captured.out

    def test_con_correccion_local_muestra_debug(
        self, capsys
    ):
        correct_transcription("planeta martes")
        captured = capsys.readouterr()
        assert "[DECIA CORRECTION]" in captured.out
        assert "Marte" in captured.out


# ==========================================
# CASOS BORDE
# ==========================================


class TestEdgeCases:

    def test_texto_vacio(self):
        result = correct_transcription("")
        assert result == ""

    def test_none(self):
        result = correct_transcription(None)
        assert result is None

    def test_solo_espacios(self):
        result = correct_transcription("   ")
        assert result == "   "

    def test_texto_largo_sin_correccion(self):
        original = (
            "Quiero que me cuentes algo interesante "
            "sobre la historia de la humanidad"
        )
        result = correct_transcription(original)
        assert result == original

    def test_planeta_en_oracion_larga(self):
        original = (
            "Hola DECIA, ¿puedes buscarme información "
            "sobre el planeta martes por favor?"
        )
        result = correct_transcription(original)
        assert "Marte" in result
        assert "martes" not in result
