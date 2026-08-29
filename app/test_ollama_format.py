"""Test Ollama multi-message format."""
import json
from urllib import request

data = {
    "model": "llama3.2:3b",
    "messages": [
        {"role": "system", "content": "Eres un asistente util. Responde en español."},
        {"role": "user", "content": "Hola, me llamo Idelvi"},
        {"role": "assistant", "content": "Hola Idelvi! Como puedo ayudarte?"},
        {"role": "user", "content": "Como me llamo?"}
    ],
    "stream": False,
    "options": {"temperature": 0.2, "num_predict": 50}
}

payload = json.dumps(data).encode("utf-8")
req = request.Request(
    "http://localhost:11434/api/chat",
    data=payload,
    headers={"Content-Type": "application/json"}
)

try:
    with request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        answer = result.get("message", {}).get("content", "")
        msg_count = len(data["messages"])
        print(f"Mensajes enviados: {msg_count}")
        print(f"Respuesta: {answer}")
        print("Ollama acepta formato multi-mensaje: SI")
except Exception as e:
    print(f"Error: {e}")
    print("Ollama no disponible o error en formato")
