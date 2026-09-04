# app/services/plugins/identity.py - IdentityPlugin
# User identity management plugin

from app.services.plugins.base import ServicePlugin


class IdentityPlugin:
    """Plugin for managing user identity data."""

    def __init__(self):
        self._storage: dict = {}
        self._plugin = ServicePlugin(
            name="IDENTITY",
            category="ARCHIVE",
            description="User identity management",
            execute=self.execute,
        )

    @property
    def name(self) -> str:
        return self._plugin.name

    @property
    def category(self) -> str:
        return self._plugin.category

    def execute(self, context: dict) -> dict:
        """Execute identity operation.

        Args:
            context: Dict with 'action' (get|save|delete|list) and optional 'key', 'data'

        Returns:
            Result dict based on action
        """
        action = context.get("action", "get")
        key = context.get("key")

        if action == "get":
            if key is None:
                return {}
            return self._storage.get(key, {})

        elif action == "save":
            if key is None:
                raise ValueError("save action requires 'key'")
            data = context.get("data", {})
            self._storage[key] = data
            return {"status": "saved", "key": key}

        elif action == "delete":
            if key is None:
                raise ValueError("delete action requires 'key'")
            self._storage.pop(key, None)
            return {"status": "deleted", "key": key}

        elif action == "list":
            return list(self._storage.keys())

        else:
            raise ValueError(f"Unknown action: {action}")


# Module-level PLUGIN for auto-discovery
PLUGIN = IdentityPlugin()