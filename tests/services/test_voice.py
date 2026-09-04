# tests/services/test_voice.py
# Contract assertions for VoicePlugin: speak/listen parity

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from app.services.plugins.voice import VoicePlugin


def test_voice_speak():
    """VoicePlugin.speak must accept text and return status."""
    plugin = VoicePlugin()
    result = plugin.execute({"action": "speak", "text": "Hello world"})
    assert result["status"] == "spoken"
    assert result["text"] == "Hello world"


def test_voice_listen():
    """VoicePlugin.listen must return transcript or empty."""
    plugin = VoicePlugin()
    result = plugin.execute({"action": "listen"})
    # In test mode, returns empty transcript
    assert "transcript" in result
    assert result["transcript"] == ""


def test_voice_speak_empty_text():
    """VoicePlugin.speak with empty text must handle gracefully."""
    plugin = VoicePlugin()
    result = plugin.execute({"action": "speak", "text": ""})
    assert result["status"] == "skipped"


def test_voice_config():
    """VoicePlugin must support configuration (rate, volume, voice_id)."""
    plugin = VoicePlugin()
    plugin.execute({"action": "configure", "rate": 150, "volume": 0.8})
    # Configuration should be stored
    assert plugin._rate == 150
    assert plugin._volume == 0.8