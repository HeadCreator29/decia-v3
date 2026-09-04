# app/services/plugins/registry.py - ServiceRegistry
# Registry for service plugins with register/get/get_instance/discover

from typing import Dict, List, Type

from app.services.plugins.base import ServicePlugin


class ServiceRegistry:
    """Registry for service plugins.

    Provides registration, retrieval, instantiation, and discovery
    of service plugins by name and category.
    """

    def __init__(self):
        self._plugins: Dict[str, ServicePlugin] = {}

    def register(self, plugin: ServicePlugin) -> None:
        """Register a plugin.

        Args:
            plugin: The ServicePlugin to register.

        Raises:
            ValueError: If a plugin with the same name is already registered.
        """
        if plugin.name in self._plugins:
            raise ValueError(f"Plugin '{plugin.name}' already registered")
        self._plugins[plugin.name] = plugin

    def get(self, name: str) -> ServicePlugin:
        """Get a registered plugin by name.

        Args:
            name: The plugin name.

        Returns:
            The registered ServicePlugin.

        Raises:
            KeyError: If no plugin with the given name is registered.
        """
        if name not in self._plugins:
            raise KeyError(f"Plugin '{name}' not found")
        return self._plugins[name]

    def get_instance(self, name: str) -> ServicePlugin:
        """Get a fresh instance of a registered plugin.

        Args:
            name: The plugin name.

        Returns:
            A new ServicePlugin instance with the same configuration.

        Raises:
            KeyError: If no plugin with the given name is registered.
        """
        plugin = self.get(name)
        # Create a new instance with same configuration
        return ServicePlugin(
            name=plugin.name,
            category=plugin.category,
            description=plugin.description,
            priority=plugin.priority,
            validate=plugin.validate,
            execute=plugin.execute,
        )

    def discover(self, category: str) -> List[ServicePlugin]:
        """Discover all plugins in a category.

        Args:
            category: The category to filter by.

        Returns:
            List of ServicePlugin instances matching the category.
        """
        return [p for p in self._plugins.values() if p.category == category]

    def __contains__(self, name: str) -> bool:
        """Check if a plugin is registered."""
        return name in self._plugins

    def __len__(self) -> int:
        """Return number of registered plugins."""
        return len(self._plugins)