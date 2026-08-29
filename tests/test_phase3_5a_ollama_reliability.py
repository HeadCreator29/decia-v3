"""
PHASE 3.5A — Ollama Reliability Audit
Tests Ollama failure modes and error handling.
"""
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from services.ollama_service import ask_ollama, remove_thinking, needs_archive
from brain.core import think


class TestRemoveThinking:

    def test_normal_text(self):
        assert remove_thinking("Hola mundo") == "Hola mundo"

    def test_think_tags(self):
        assert remove_thinking("<think>razonamiento</think> respuesta") == "respuesta"

    def test_thinking_tags(self):
        assert remove_thinking("<thinking>Call</thinking> text") == "text"

    def test_analysis_tags(self):
        assert remove_thinking("<analysis>reasoning</analysis> final") == "final"

    def test_empty_after_think(self):
        assert remove_thinking("<think>todo razocinamiento</think>") == ""

    def test_multiple_think_blocks(self):
        result = remove_thinking("<think>a</think>middle<think>b</think>")
        assert result == "middle"

    def test_nested_garbage(self):
        result = remove_thinking("<think>内外</think> texto final")
        assert result == "texto final"

    def test_unclosed_think(self):
        result = remove_thinking("<think>sin cerrar")
        assert result == "<think>sin cerrar"

    def test_partial_close(self):
        result = remove_thinking("text</think>rest")
        assert "rest" in result

    def test_empty_string(self):
        assert remove_thinking("") == ""


class TestNeedsArchive:

    def test_deca(self):
        assert needs_archive("que es deca") is True

    def test_historia(self):
        assert needs_archive("cuentame la historia") is True

    def test_proyecto(self):
        assert needs_archive("que proyecto tenemos") is True

    def test_recuerdas(self):
        assert needs_archive("que recuerdas") is True

    def test_no_match(self):
        assert needs_archive("2+2") is False

    def test_partial_match(self):
        assert needs_archive("xdecax") is True

    def test_empty(self):
        assert needs_archive("") is False

    def test_case_insensitive(self):
        assert needs_archive("DECA") is True


class TestAskOllamaConnectionRefused:

    def test_connection_refused(self):
        with patch("services.ollama_service.request.urlopen") as mock:
            mock.side_effect = ConnectionRefusedError("Connection refused")
            result = ask_ollama("hola")
            assert isinstance(result, str)
            assert len(result) > 0
            assert "No pude" in result

    def test_connection_reset(self):
        with patch("services.ollama_service.request.urlopen") as mock:
            mock.side_effect = ConnectionResetError("Connection reset")
            result = ask_ollama("hola")
            assert isinstance(result, str)
            assert "No pude" in result

    def test_timeout(self):
        with patch("services.ollama_service.request.urlopen") as mock:
            mock.side_effect = TimeoutError("timed out")
            result = ask_ollama("hola")
            assert isinstance(result, str)
            assert "No pude" in result

    def test_os_error(self):
        with patch("services.ollama_service.request.urlopen") as mock:
            mock.side_effect = OSError("Network unreachable")
            result = ask_ollama("hola")
            assert isinstance(result, str)
            assert "No pude" in result


class TestAskOllamaMalformedResponse:

    def test_invalid_json(self):
        mock_response = MagicMock()
        mock_response.read.return_value = b"not json"
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("services.ollama_service.request.urlopen") as mock:
            mock.return_value = mock_response
            result = ask_ollama("hola")
            assert isinstance(result, str)
            assert "No pude" in result

    def test_empty_body(self):
        mock_response = MagicMock()
        mock_response.read.return_value = b""
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("services.ollama_service.request.urlopen") as mock:
            mock.return_value = mock_response
            result = ask_ollama("hola")
            assert isinstance(result, str)
            assert "No pude" in result

    def test_missing_message_key(self):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"model": "llama3.2:3b"}).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("services.ollama_service.request.urlopen") as mock:
            mock.return_value = mock_response
            result = ask_ollama("hola")
            assert isinstance(result, str)
            assert "No tengo" in result

    def test_empty_message_content(self):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "message": {"content": ""},
            "eval_duration": 0,
            "eval_count": 0
        }).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("services.ollama_service.request.urlopen") as mock:
            mock.return_value = mock_response
            result = ask_ollama("hola")
            assert isinstance(result, str)
            assert "No tengo" in result

    def test_none_message(self):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "message": None,
            "eval_duration": 0,
            "eval_count": 0
        }).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("services.ollama_service.request.urlopen") as mock:
            mock.return_value = mock_response
            result = ask_ollama("hola")
            assert isinstance(result, str)
            assert "No tengo" in result


class TestAskOllamaValidResponse:

    def test_normal_response(self):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "message": {"content": "Hola! Soy DECIA."},
            "eval_duration": 1_000_000_000,
            "eval_count": 50
        }).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("services.ollama_service.request.urlopen") as mock:
            mock.return_value = mock_response
            result = ask_ollama("hola")
            assert result == "Hola! Soy DECIA."

    def test_response_with_think_tags(self):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "message": {"content": "<think>razonamiento</think> Soy DECIA."},
            "eval_duration": 1_000_000_000,
            "eval_count": 50
        }).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("services.ollama_service.request.urlopen") as mock:
            mock.return_value = mock_response
            result = ask_ollama("hola")
            assert result == "Soy DECIA."


class TestThinkOllamaIntegration:

    def test_think_routes_to_ollama(self):
        with patch("services.ollama_service.request.urlopen") as mock:
            mock.side_effect = ConnectionRefusedError("refused")
            result = think("esto es una pregunta random sin patron")
            assert isinstance(result, str)
            assert len(result) > 0

    def test_think_connection_refused(self):
        with patch("services.ollama_service.request.urlopen") as mock:
            mock.side_effect = OSError("No route to host")
            result = think("hablame de algo interesante")
            assert isinstance(result, str)
            assert "No pude" in result

    def test_think_timeout(self):
        with patch("services.ollama_service.request.urlopen") as mock:
            mock.side_effect = TimeoutError("timeout")
            result = think("cuentame un cuento largo")
            assert isinstance(result, str)
            assert "No pude" in result
