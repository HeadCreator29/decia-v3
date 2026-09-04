# app/services/plugins/history_facade.py - History façade
# Re-exports history functions with original signatures, delegates to HistoryPlugin

from pathlib import Path
import json

from app.services.plugins.history import HistoryPlugin


# Module-level plugin instance
_history_plugin = HistoryPlugin()

# Archive path for JSON persistence
BASE_DIR = Path(__file__).resolve().parents[3]
ARCHIVE_PATH = BASE_DIR / "data" / "archive"


def _load_history_file():
    """Load history from JSON file."""
    path = ARCHIVE_PATH / "history.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"events": []}


def get_history():
    """Get full history data."""
    return _load_history_file()


# For backward compatibility with plugin interface
def execute(context: dict):
    """Plugin execute interface."""
    return _history_plugin.execute(context)


# Plugin instance for registry
PLUGIN = _history_plugin

__all__ = ["get_history", "execute", "PLUGIN", "ARCHIVE_PATH"]