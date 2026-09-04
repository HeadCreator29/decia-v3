# tests/services/test_identity.py
# Contract assertions for IdentityPlugin: get/save parity, missing -> {}

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from app.services.plugins.identity import IdentityPlugin


def test_identity_get_returns_empty_dict_for_missing():
    """IdentityPlugin.get must return {} for missing identity."""
    plugin = IdentityPlugin()
    result = plugin.execute({"action": "get", "key": "nonexistent"})
    assert result == {}


def test_identity_save_and_get_parity():
    """IdentityPlugin.save followed by get must return saved data."""
    plugin = IdentityPlugin()
    test_data = {"name": "Test User", "preferences": {"theme": "dark"}}
    plugin.execute({"action": "save", "key": "user_1", "data": test_data})
    result = plugin.execute({"action": "get", "key": "user_1"})
    assert result == test_data


def test_identity_overwrite():
    """IdentityPlugin.save must overwrite existing key."""
    plugin = IdentityPlugin()
    plugin.execute({"action": "save", "key": "user_1", "data": {"v": 1}})
    plugin.execute({"action": "save", "key": "user_1", "data": {"v": 2}})
    result = plugin.execute({"action": "get", "key": "user_1"})
    assert result == {"v": 2}


def test_identity_delete():
    """IdentityPlugin.delete must remove key and return {} on get."""
    plugin = IdentityPlugin()
    plugin.execute({"action": "save", "key": "user_1", "data": {"v": 1}})
    plugin.execute({"action": "delete", "key": "user_1"})
    result = plugin.execute({"action": "get", "key": "user_1"})
    assert result == {}


def test_identity_list_keys():
    """IdentityPlugin.list must return all saved keys."""
    plugin = IdentityPlugin()
    plugin.execute({"action": "save", "key": "a", "data": {}})
    plugin.execute({"action": "save", "key": "b", "data": {}})
    result = plugin.execute({"action": "list"})
    assert set(result) == {"a", "b"}