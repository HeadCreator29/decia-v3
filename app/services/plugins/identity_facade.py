# app/services/plugins/identity_facade.py - Identity façade
# Re-exports identity functions with original signatures, delegates to IdentityPlugin

import warnings
from pathlib import Path
import json

from app.services.plugins.identity import IdentityPlugin


# Module-level plugin instance
_identity_plugin = IdentityPlugin()

# Archive path for JSON persistence (maintains zero behavioral change)
BASE_DIR = Path(__file__).resolve().parents[3]
ARCHIVE_PATH = BASE_DIR / "data" / "archive"


def _load_identity_file():
    """Load identity from JSON file (preserves original behavior)."""
    path = ARCHIVE_PATH / "identity.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_identity_file(data):
    """Save identity to JSON file (preserves original behavior)."""
    path = ARCHIVE_PATH / "identity.json"
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[DECIA ARCHIVE] Error al guardar identity: {e}")


def get_identity(key: str = None):
    """Get identity data. If key provided, return that key's value."""
    # Load from file for persistence
    data = _load_identity_file()
    if key is None:
        return data
    return data.get(key, {})


def save_identity(data: dict):
    """Save identity data to file."""
    _save_identity_file(data)


# For backward compatibility with plugin interface
def execute(context: dict):
    """Plugin execute interface."""
    return _identity_plugin.execute(context)


# Plugin instance for registry
PLUGIN = _identity_plugin

__all__ = ["get_identity", "save_identity", "execute", "PLUGIN", "ARCHIVE_PATH"]