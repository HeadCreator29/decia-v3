# app/services/speaker.py - DEPRECATED façade
# Re-exports VoicePlugin.speak() for backward compatibility
# TODO: Remove in Phase 6 cleanup

import warnings
from app.services.plugins.voice import VoicePlugin


# Module-level plugin instance
_voice_plugin = VoicePlugin()


def speak(text: str) -> None:
    """Deprecated: Use VoicePlugin.execute({'action': 'speak', 'text': ...}) instead.

    This façade will be removed in Phase 6.
    """
    warnings.warn(
        "services.speaker.speak is deprecated. "
        "Use services.plugins.voice.VoicePlugin.execute({'action': 'speak', 'text': ...}) instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    _voice_plugin.execute({"action": "speak", "text": text})


# For backward compatibility - allow importing the plugin directly
__all__ = ["speak"]