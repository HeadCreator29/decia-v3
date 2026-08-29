"""Tests for conversational context flow to Ollama."""
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "app"),
)

from brain.context import ConversationContext
from services.ollama_service import (
    ask_ollama,
    needs_archive,
)


def _capture_payload(mock_urlopen):
    """Extract the JSON payload from a mocked urlopen call."""
    call_args = mock_urlopen.call_args
    http_request = call_args[0][0]
    payload_bytes = http_request.data
    return json.loads(payload_bytes.decode("utf-8"))


def _mock_ollama_response(
    content="Respuesta de prueba"
):
    """Create a mock response from Ollama."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({
        "message": {"content": content},
        "eval_duration": 100000000,
        "eval_count": 10,
    }).encode("utf-8")
    mock_resp.__enter__ = MagicMock(
        return_value=mock_resp
    )
    mock_resp.__exit__ = MagicMock(
        return_value=False
    )
    return mock_resp


# ==========================================
# 1. HISTORIAL SE PRESERVA EN ORDEN
# ==========================================


def test_history_preserves_order():
    ctx = ConversationContext(max_turns=10)

    ctx.add_user_message("primero")
    ctx.add_assistant_message("resp1")
    ctx.add_user_message("segundo")
    ctx.add_assistant_message("resp2")
    ctx.add_user_message("tercero")

    messages = ctx.get_messages()

    assert len(messages) == 5
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "primero"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "resp1"
    assert messages[2]["role"] == "user"
    assert messages[2]["content"] == "segundo"
    assert messages[3]["role"] == "assistant"
    assert messages[3]["content"] == "resp2"
    assert messages[4]["role"] == "user"
    assert messages[4]["content"] == "tercero"


# ==========================================
# 2. ROLES USER Y ASSISTANT LLEGAN
#    CORRECTAMENTE
# ==========================================


def test_roles_are_user_and_assistant():
    ctx = ConversationContext()
    ctx.add_user_message("hola")
    ctx.add_assistant_message("que tal")

    messages = ctx.get_messages()

    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


# ==========================================
# 3. MENSAJE ACTUAL NO SE DUPLICA
# ==========================================


def test_no_duplicate_current_message():
    ctx = ConversationContext()
    ctx.add_user_message("anterior")
    ctx.add_assistant_message("resp1")

    with patch(
        "services.ollama_service.request.urlopen"
    ) as mock_urlopen:
        mock_urlopen.return_value = (
            _mock_ollama_response()
        )

        ask_ollama(
            "actual",
            context=ctx.get_messages(),
        )

    payload = _capture_payload(mock_urlopen)
    messages = payload["messages"]

    user_msgs = [
        m
        for m in messages
        if m["role"] == "user"
    ]

    actual_count = sum(
        1
        for m in user_msgs
        if m["content"] == "actual"
    )

    assert actual_count == 1, (
        f"Mensaje actual duplicado: "
        f"aparece {actual_count} veces"
    )


# ==========================================
# 4. ARCHIVO DECA SE CARGA CON HISTORIAL
# ==========================================


def test_archive_loads_with_history():
    ctx = ConversationContext()
    ctx.add_user_message("hola")
    ctx.add_assistant_message("que tal")

    with patch(
        "services.ollama_service.request.urlopen"
    ) as mock_urlopen:
        mock_urlopen.return_value = (
            _mock_ollama_response()
        )

        ask_ollama(
            "cuando comenzo deca",
            context=ctx.get_messages(),
        )

    payload = _capture_payload(mock_urlopen)
    system_content = payload["messages"][0][
        "content"
    ]

    assert "ARCHIVO DECA" in system_content


def test_archive_loads_without_history():
    with patch(
        "services.ollama_service.request.urlopen"
    ) as mock_urlopen:
        mock_urlopen.return_value = (
            _mock_ollama_response()
        )

        ask_ollama(
            "cuando comenzo deca",
            context=None,
        )

    payload = _capture_payload(mock_urlopen)
    system_content = payload["messages"][0][
        "content"
    ]

    assert "ARCHIVO DECA" in system_content


# ==========================================
# 5. PRIMER MENSAJE CON HISTORIAL VACÍO
# ==========================================


def test_first_message_empty_history():
    with patch(
        "services.ollama_service.request.urlopen"
    ) as mock_urlopen:
        mock_urlopen.return_value = (
            _mock_ollama_response()
        )

        ask_ollama(
            "hola",
            context=[],
        )

    payload = _capture_payload(mock_urlopen)
    messages = payload["messages"]

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "hola"


def test_first_message_no_context():
    with patch(
        "services.ollama_service.request.urlopen"
    ) as mock_urlopen:
        mock_urlopen.return_value = (
            _mock_ollama_response()
        )

        ask_ollama("hola", context=None)

    payload = _capture_payload(mock_urlopen)
    messages = payload["messages"]

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"


# ==========================================
# 6. PAYLOAD COMPLETO CON HISTORIAL
# ==========================================


def test_full_payload_with_history():
    ctx = ConversationContext()
    ctx.add_user_message("mi nombre es Idelvi")
    ctx.add_assistant_message(
        "Hola Idelvi, gusto en conocerte."
    )

    with patch(
        "services.ollama_service.request.urlopen"
    ) as mock_urlopen:
        mock_urlopen.return_value = (
            _mock_ollama_response()
        )

        ask_ollama(
            "como me llamo",
            context=ctx.get_messages(),
        )

    payload = _capture_payload(mock_urlopen)
    messages = payload["messages"]

    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert (
        messages[1]["content"]
        == "mi nombre es Idelvi"
    )
    assert messages[2]["role"] == "assistant"
    assert (
        "Idelvi" in messages[2]["content"]
    )
    assert messages[3]["role"] == "user"
    assert (
        messages[3]["content"] == "como me llamo"
    )


# ==========================================
# 7. HISTORIAL VACÍO NO AGREGA MENSAJES
# ==========================================


def test_empty_history_adds_no_messages():
    with patch(
        "services.ollama_service.request.urlopen"
    ) as mock_urlopen:
        mock_urlopen.return_value = (
            _mock_ollama_response()
        )

        ask_ollama(
            "test",
            context=[],
        )

    payload = _capture_payload(mock_urlopen)
    messages = payload["messages"]

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"


# ==========================================
# 8. NEEDS_ARCHIVE FUNCIONA INDEPENDIENTEMENTE
# ==========================================


def test_needs_archive_independent_of_history():
    assert needs_archive("cuando comenzo deca")
    assert needs_archive("cuenta algo de DECA")
    assert not needs_archive("hola que tal")
    assert not needs_archive("2 + 2")


# ==========================================
# 9. MAX_TURNS SE MANTIENE
# ==========================================


def test_max_turns_still_works():
    ctx = ConversationContext(max_turns=2)

    for i in range(5):
        ctx.add_user_message(f"msg {i}")
        ctx.add_assistant_message(f"reply {i}")

    messages = ctx.get_messages()

    assert len(messages) == 4
    assert messages[0]["content"] == "msg 3"
    assert messages[1]["content"] == "reply 3"
    assert messages[2]["content"] == "msg 4"
    assert messages[3]["content"] == "reply 4"
