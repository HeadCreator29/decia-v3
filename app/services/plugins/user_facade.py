# app/services/plugins/user_facade.py - User façade
# Re-exports user functions with original signatures, delegates to UserPlugin

from pathlib import Path
import json

from app.services.plugins.user import UserPlugin


# Module-level plugin instance
_user_plugin = UserPlugin()

# Archive path for JSON persistence
BASE_DIR = Path(__file__).resolve().parents[3]
ARCHIVE_PATH = BASE_DIR / "data" / "archive"


def _load_user_file():
    """Load user from JSON file."""
    path = ARCHIVE_PATH / "user.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_user_file(data):
    """Save user to JSON file."""
    path = ARCHIVE_PATH / "user.json"
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[DECIA ARCHIVE] Error al guardar user: {e}")


def get_user(user_id: str = None):
    """Get user data. If user_id provided, return that user's data."""
    data = _load_user_file()
    if user_id is None:
        return data
    return data.get(user_id, {})


def save_user(data: dict):
    """Save user data to file."""
    _save_user_file(data)


# For backward compatibility with plugin interface
def execute(context: dict):
    """Plugin execute interface."""
    return _user_plugin.execute(context)


# Plugin instance for registry
PLUGIN = _user_plugin

__all__ = ["get_user", "save_user", "execute", "PLUGIN", "ARCHIVE_PATH"]