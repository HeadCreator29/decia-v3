# tests/services/test_plugin_base.py
# Contract assertions for ServicePlugin dataclass:
# - name, category fields
# - default validate()

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from app.services.plugins.base import ServicePlugin


def test_service_plugin_has_name():
    """ServicePlugin must have a name field."""
    plugin = ServicePlugin(
        name="IDENTITY",
        category="ARCHIVE",
    )
    assert plugin.name == "IDENTITY"


def test_service_plugin_has_category():
    """ServicePlugin must have a category field."""
    plugin = ServicePlugin(
        name="IDENTITY",
        category="ARCHIVE",
    )
    assert plugin.category == "ARCHIVE"


def test_service_plugin_default_validate():
    """ServicePlugin.default validate() must return True."""
    plugin = ServicePlugin(
        name="IDENTITY",
        category="ARCHIVE",
    )
    result = plugin.validate("any message", {})
    assert result is True


def test_service_plugin_validate_override():
    """ServicePlugin.validate() can be overridden with custom logic."""
    plugin = ServicePlugin(
        name="IDENTITY",
        category="ARCHIVE",
    )
    # Custom validation: return False if message is empty
    result = plugin.validate("", {})
    assert result is False