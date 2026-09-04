# app/services/plugins/base.py - ServicePlugin dataclass
# Provides the ServicePlugin data structure for service plugins
# Mirrors the pattern of brain.plugins.base.IntentPlugin

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class ServicePlugin:
    """Dataclass representing a single service plugin.

    Attributes:
        name: The plugin name identifier (e.g., "IDENTITY", "USER", "HISTORY")
        category: The plugin category (e.g., "ARCHIVE", "PLANNER", "OLLAMA")
        description: Optional description of the plugin's purpose
        validate: Optional validation hook; defaults to returning True
        execute: Optional execute hook; defaults to returning empty dict
    """

    name: str
    category: str
    description: str | None = None
    priority: int = 0
    validate: Callable[[str, dict], bool] = field(default_factory=lambda: lambda message, entities: bool(message.strip()))
    execute: Callable[[dict], dict] = field(default_factory=lambda: lambda context: {})

    def __post_init__(self):
        """Ensure callables are bound correctly."""
        if not callable(self.validate):
            raise TypeError("validate must be callable")
        if not callable(self.execute):
            raise TypeError("execute must be callable")