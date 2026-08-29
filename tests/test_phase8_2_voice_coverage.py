import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "app"),
)

from services.speaker import speak as speaker_speak

from transcription_interpreter import (
    ANALYZER_MAX_TOKENS,
    ANALYZER_MODEL,
    ANALYZER_SYSTEM_PROMPT,
    ANALYZER_TEMPERATURE,
    OLLAMA_URL,
    SUSPICION_RULES,
    SuspicionResult,
    analyze_with_ollama,
    interpret_transcription,
)


# ==========================================
# ANALYZE_WITH_OLLAMA — CONTRATO HTTP REAL
# ==========================================


class TestAnalyzeWithOllama:


    def _suspicion(self):
        return SuspicionResult(
            is_suspicious=True,
            reason="palabra después de 'planeta' "
                   "no coincide con planetas conocidos",
            suspect_word="mario",
            context_window="planeta mario",
        )

    def _mock_http_response(self, raw_text):
        response = MagicMock()
        response.read.return_value = raw_text
        return response

    @patch("transcription_interpreter.request.urlopen")
    def test_contrato_http_payload(self, mock_urlopen):
        response = self._mock_http_response(
            json.dumps({
                "message": {
                    "content": (
                        '{"should_correct": false, '
                        '"confidence": 1.0}'
                    )
                }
            }).encode("utf-8")
        )
        mock_urlopen.return_value.__enter__.return_value = (
            response
        )

        resultado = analyze_with_ollama(
            "planeta mario",
            self._suspicion(),
        )

        mock_urlopen.assert_called_once()
        http_request = mock_urlopen.call_args.args[0]

        assert http_request.full_url == OLLAMA_URL
        assert http_request.get_header(
            "Content-type"
        ) == "application/json"

        payload = json.loads(
            http_request.data.decode("utf-8")
        )

        assert payload["model"] == ANALYZER_MODEL
        assert payload["think"] is False
        assert payload["keep_alive"] == -1
        assert payload["stream"] is False
        assert payload["options"]["temperature"] == (
            ANALYZER_TEMPERATURE
        )
        assert payload["options"]["num_predict"] == (
            ANALYZER_MAX_TOKENS
        )

        messages = payload["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == (
            ANALYZER_SYSTEM_PROMPT
        )
        assert messages[1]["role"] == "user"
        assert "planeta mario" in messages[1]["content"]
        assert "mario" in messages[1]["content"]

        assert resultado == (
            '{"should_correct": false, '
            '"confidence": 1.0}'
        )

    @patch("transcription_interpreter.request.urlopen")
    def test_respuesta_sin_message_devuelve_vacio(
        self, mock_urlopen
    ):
        response = self._mock_http_response(
            b'{"otro_campo": "x"}'
        )
        mock_urlopen.return_value.__enter__.return_value = (
            response
        )

        resultado = analyze_with_ollama(
            "planeta mario",
            self._suspicion(),
        )

        assert resultado == ""

    @patch("transcription_interpreter.request.urlopen")
    def test_json_invalido_devuelve_none(
        self, mock_urlopen
    ):
        response = self._mock_http_response(
            b"<html>no es json</html>"
        )
        mock_urlopen.return_value.__enter__.return_value = (
            response
        )

        resultado = analyze_with_ollama(
            "planeta mario",
            self._suspicion(),
        )

        assert resultado is None

    @patch("transcription_interpreter.request.urlopen")
    def test_error_de_red_devuelve_none(
        self, mock_urlopen
    ):
        mock_urlopen.side_effect = (
            OSError("conexión rechazada")
        )

        resultado = analyze_with_ollama(
            "planeta mario",
            self._suspicion(),
        )

        assert resultado is None

    @patch("transcription_interpreter.request.urlopen")
    def test_timeout_devuelve_none(
        self, mock_urlopen
    ):
        mock_urlopen.side_effect = (
            TimeoutError("timeout de 30s")
        )

        resultado = analyze_with_ollama(
            "planeta mario",
            self._suspicion(),
        )

        assert resultado is None


# ==========================================
# INTERPRET_TRANSCRIPTION — CONTRATO BORDE
# ==========================================


class TestInterpretTranscription:

    def test_error_analizador_preserva_original(self):
        with patch(
            "transcription_interpreter.analyze_with_ollama",
            return_value=None,
        ):
            resultado = interpret_transcription(
                "planeta mario",
                SuspicionResult(
                    is_suspicious=True,
                    reason="razón",
                    suspect_word="mario",
                ),
            )

        assert resultado == "planeta mario"

    def test_confianza_alta_acepta_correccion(self):
        with patch(
            "transcription_interpreter.analyze_with_ollama",
            return_value=json.dumps({
                "should_correct": True,
                "confidence": 0.95,
                "corrected_text": (
                    "busca información sobre el "
                    "planeta Marte"
                ),
                "reason": "mario no es un planeta",
            }),
        ):
            resultado = interpret_transcription(
                "busca info sobre el planeta mario",
                SuspicionResult(
                    is_suspicious=True,
                    reason="razón",
                    suspect_word="mario",
                ),
            )

        assert resultado == (
            "busca información sobre el planeta Marte"
        )

    def test_confianza_baja_preserva_original(self):
        with patch(
            "transcription_interpreter.analyze_with_ollama",
            return_value=json.dumps({
                "should_correct": True,
                "confidence": 0.60,
                "corrected_text": "planeta Marte",
                "reason": "no estoy seguro",
            }),
        ):
            resultado = interpret_transcription(
                "planeta mario",
                SuspicionResult(
                    is_suspicious=True,
                    reason="razón",
                    suspect_word="mario",
                ),
            )

        assert resultado == "planeta mario"


# ==========================================
# SUSPICION_RULES — CONTRATO DE DATOS
# ==========================================


class TestSuspicionRulesContract:

    def test_cada_regla_tiene_campos_obligatorios(self):
        assert isinstance(SUSPICION_RULES, list)
        assert len(SUSPICION_RULES) > 0
        for rule in SUSPICION_RULES:
            assert isinstance(rule, dict)
            assert isinstance(rule["trigger"], str)
            assert rule["trigger"]
            assert isinstance(
                rule["known_entities"], list
            )
            assert isinstance(rule["description"], str)
            assert rule["description"]


# ==========================================
# SERVICES.SPEAKER — CONTRATO CON ENGINE
# ==========================================


class TestSpeaker:

    def test_habla_texto_llama_engine(self):
        engine = MagicMock()
        with patch("services.speaker.engine", engine):
            retorno = speaker_speak("Hola, soy DECIA")

        assert retorno is None
        engine.say.assert_called_once_with(
            "Hola, soy DECIA"
        )
        engine.runAndWait.assert_called_once()

    def test_habla_dos_veces_llama_engine_dos_veces(self):
        engine = MagicMock()
        with patch("services.speaker.engine", engine):
            speaker_speak("Primero")
            speaker_speak("Segundo")

        assert engine.say.call_count == 2
        assert engine.runAndWait.call_count == 2
        assert engine.say.call_args_list[0] == (
            (("Primero",), {})
        )
        assert engine.say.call_args_list[1] == (
            (("Segundo",), {})
        )

    def test_habla_texto_vacio_usa_engine(self):
        engine = MagicMock()
        with patch("services.speaker.engine", engine):
            retorno = speaker_speak("")

        assert retorno is None
        engine.say.assert_called_once_with("")

    def test_error_del_engine_propaga(self):
        engine = MagicMock()
        engine.say.side_effect = RuntimeError(
            "motor de voz falló"
        )
        with patch("services.speaker.engine", engine):
            try:
                speaker_speak("texto")
            except RuntimeError:
                pass
            else:
                raise AssertionError(
                    "el error del engine debería propagarse"
                )