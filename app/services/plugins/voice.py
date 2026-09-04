# app/services/plugins/voice.py - VoicePlugin
# Voice I/O plugin (STT + TTS merged, replaces voice.py + speaker.py)

from app.services.plugins.base import ServicePlugin


class VoicePlugin:
    """Plugin for voice input/output (STT + TTS)."""

    def __init__(self):
        self._rate = 200
        self._volume = 1.0
        self._voice_id = None
        self._plugin = ServicePlugin(
            name="VOICE",
            category="VOICE",
            description="Voice I/O (STT + TTS merged)",
            execute=self.execute,
        )

    @property
    def name(self) -> str:
        return self._plugin.name

    @property
    def category(self) -> str:
        return self._plugin.category

    def execute(self, context: dict) -> dict:
        """Execute voice operation.

        Args:
            context: Dict with 'action' (speak|listen|configure) and parameters

        Returns:
            Result dict
        """
        action = context.get("action", "speak")

        if action == "speak":
            text = context.get("text", "")
            if not text:
                return {"status": "skipped", "text": ""}
            # In real implementation, would use pyttsx3
            return {"status": "spoken", "text": text, "rate": self._rate, "volume": self._volume}

        elif action == "listen":
            # In real implementation, would use faster-whisper
            return {"status": "listened", "transcript": "", "confidence": 0.0}

        elif action == "configure":
            if "rate" in context:
                self._rate = context["rate"]
            if "volume" in context:
                self._volume = context["volume"]
            if "voice_id" in context:
                self._voice_id = context["voice_id"]
            return {"status": "configured", "rate": self._rate, "volume": self._volume, "voice_id": self._voice_id}

        else:
            raise ValueError(f"Unknown action: {action}")


# Module-level PLUGIN for auto-discovery
PLUGIN = VoicePlugin()