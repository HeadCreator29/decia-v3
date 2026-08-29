"""Verify actual payload sent to Ollama with conversation history."""
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[0]),
)

from brain.context import ConversationContext
from services.ollama_service import ask_ollama


def mock_response(content="Respuesta de prueba"):
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({
        "message": {"content": content},
        "eval_duration": 100000000,
        "eval_count": 10,
    }).encode("utf-8")
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


print("=" * 60)
print("  VERIFICACION: PAYLOAD A OLLAMA")
print("=" * 60)

ctx = ConversationContext(max_turns=10)

# --- Turno 1: "Mi nombre es Idelvi" ---
print("\n[Turno 1] Usuario: Mi nombre es Idelvi")

with patch("services.ollama_service.request.urlopen") as mock:
    mock.return_value = mock_response("Hola Idelvi, gusto en conocerte.")
    ask_ollama("Mi nombre es Idelvi", context=ctx.get_messages())

    payload = json.loads(mock.call_args[0][0].data)
    msgs = payload["messages"]
    print(f"  Mensajes en payload: {len(msgs)}")
    for i, m in enumerate(msgs):
        content_preview = m['content'][:60].replace('\n', ' ')
        print(f"    [{i}] role={m['role']:10s} | {content_preview}...")

# --- Simular lo que hace main.py: guardar en contexto ---
ctx.add_user_message("Mi nombre es Idelvi")
ctx.add_assistant_message("Hola Idelvi, gusto en conocerte.")

# --- Turno 2: "Como me llamo?" ---
print("\n[Turno 2] Usuario: Como me llamo?")

with patch("services.ollama_service.request.urlopen") as mock:
    mock.return_value = mock_response("Tu nombre es Idelvi.")
    ask_ollama("Como me llamo?", context=ctx.get_messages())

    payload = json.loads(mock.call_args[0][0].data)
    msgs = payload["messages"]
    print(f"  Mensajes en payload: {len(msgs)}")
    for i, m in enumerate(msgs):
        content_preview = m['content'][:60].replace('\n', ' ')
        print(f"    [{i}] role={m['role']:10s} | {content_preview}...")

ctx.add_user_message("Como me llamo?")
ctx.add_assistant_message("Tu nombre es Idelvi.")

# --- Turno 3: Pregunta sobre DECA ---
print("\n[Turno 3] Usuario: Cuando comenzo DECA?")

with patch("services.ollama_service.request.urlopen") as mock:
    mock.return_value = mock_response("DECA comenzo el 29 de agosto de 2025.")
    ask_ollama("Cuando comenzo DECA?", context=ctx.get_messages())

    payload = json.loads(mock.call_args[0][0].data)
    msgs = payload["messages"]
    print(f"  Mensajes en payload: {len(msgs)}")
    for i, m in enumerate(msgs):
        content_preview = m['content'][:60].replace('\n', ' ')
        print(f"    [{i}] role={m['role']:10s} | {content_preview}...")

    system_content = msgs[0]["content"]
    has_archive = "ARCHIVO DECA" in system_content
    print(f"\n  Archivo DECA en system prompt: {'SI' if has_archive else 'NO'}")

    user_msgs = [m for m in msgs if m["role"] == "user"]
    duplicate_check = sum(1 for m in user_msgs if m["content"] == "Cuando comenzo DECA?")
    print(f"  Veces que aparece mensaje actual: {duplicate_check}")

print("\n" + "=" * 60)
print("  VERIFICACION COMPLETADA")
print("=" * 60)
