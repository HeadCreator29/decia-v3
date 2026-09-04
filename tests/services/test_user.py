# tests/services/test_user.py
# Contract assertions for UserPlugin: get/save parity

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from app.services.plugins.user import UserPlugin


def test_user_get_returns_empty_for_missing():
    """UserPlugin.get must return {} for missing user."""
    plugin = UserPlugin()
    result = plugin.execute({"action": "get", "user_id": "nonexistent"})
    assert result == {}


def test_user_save_and_get_parity():
    """UserPlugin.save followed by get must return saved data."""
    plugin = UserPlugin()
    test_data = {"name": "John", "email": "john@example.com", "settings": {"lang": "es"}}
    plugin.execute({"action": "save", "user_id": "user_1", "data": test_data})
    result = plugin.execute({"action": "get", "user_id": "user_1"})
    assert result == test_data


def test_user_update_partial():
    """UserPlugin.update must merge partial data."""
    plugin = UserPlugin()
    plugin.execute({"action": "save", "user_id": "user_1", "data": {"name": "John", "age": 30}})
    plugin.execute({"action": "update", "user_id": "user_1", "data": {"age": 31}})
    result = plugin.execute({"action": "get", "user_id": "user_1"})
    assert result == {"name": "John", "age": 31}


def test_user_delete():
    """UserPlugin.delete must remove user."""
    plugin = UserPlugin()
    plugin.execute({"action": "save", "user_id": "user_1", "data": {"name": "John"}})
    plugin.execute({"action": "delete", "user_id": "user_1"})
    result = plugin.execute({"action": "get", "user_id": "user_1"})
    assert result == {}


def test_user_list_all():
    """UserPlugin.list must return all user IDs."""
    plugin = UserPlugin()
    plugin.execute({"action": "save", "user_id": "a", "data": {}})
    plugin.execute({"action": "save", "user_id": "b", "data": {}})
    result = plugin.execute({"action": "list"})
    assert set(result) == {"a", "b"}