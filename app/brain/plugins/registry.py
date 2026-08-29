# brain.plugins.registry - PluginRegistry class
# Manages registration and discovery of intent plugins

from brain.plugins.base import IntentPlugin


class PluginRegistry:
    """Registry for managing intent plugins.

    Responsibilities:
    - Store registered plugins by name
    - Provide pattern access per intent
    - Validate matches against plugin-specific hooks
    - Support priority-based ordering

    Usage:
        registry = PluginRegistry()
        registry.register(plugin)
        patterns = registry.get_patterns("GREETING")
        plugin = registry.get_plugin("GREETING")
        is_valid = registry.validate_match("GREETING", message, entities)
    """

    def __init__(self):
        self._plugins: dict[str, IntentPlugin] = {}
        self._all_patterns: dict[str, list[Pattern]] = {}

    def register(self, plugin: IntentPlugin) -> None:
        """Register a plugin with the registry.

        Adds the plugin to the internal dictionary and stores its patterns.
        """
        self._plugins[plugin.name] = plugin
        self._all_patterns[plugin.name] = plugin.patterns

    def get_patterns(self, intent: str) -> list[Pattern]:
        """Return the patterns for the given intent.

        Returns an empty list if no plugin is registered for this intent.
        """
        return self._all_patterns.get(intent, [])

    def get_all_patterns(self) -> dict[str, list[Pattern]]:
        """Return all patterns grouped by intent name.

        Returns a dict mapping intent names to their pattern lists.
        """
        return dict(self._all_patterns)

    def get_plugin(self, intent: str) -> IntentPlugin | None:
        """Return the plugin for the given intent, or None if not registered."""
        return self._plugins.get(intent)

    def validate_match(self, intent: str, message: str, entities: dict) -> bool:
        """Validate a match against the plugin's validate() hook.

        By default, returns True (the default validate() returns True).
        Plugins can override validate() for custom logic (e.g., exit negation,
        planner recall-ban).
        """
        plugin = self._plugins.get(intent)
        return plugin.validate(message, entities) if plugin else True