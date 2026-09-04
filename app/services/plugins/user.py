# app/services/plugins/user.py - UserPlugin
# User profile and preferences plugin

from app.services.plugins.base import ServicePlugin


class UserPlugin:
    """Plugin for managing user profiles and preferences."""

    def __init__(self):
        self._storage: dict = {}
        self._plugin = ServicePlugin(
            name="USER",
            category="ARCHIVE",
            description="User profile and preferences",
            execute=self.execute,
        )

    @property
    def name(self) -> str:
        return self._plugin.name

    @property
    def category(self) -> str:
        return self._plugin.category

    def execute(self, context: dict) -> dict:
        """Execute user operation.

        Args:
            context: Dict with 'action' (get|save|update|delete|list) and 'user_id', optional 'data'

        Returns:
            Result dict based on action
        """
        action = context.get("action", "get")
        user_id = context.get("user_id")

        if action == "get":
            if user_id is None:
                return {}
            return self._storage.get(user_id, {})

        elif action == "save":
            if user_id is None:
                raise ValueError("save action requires 'user_id'")
            data = context.get("data", {})
            self._storage[user_id] = data
            return {"status": "saved", "user_id": user_id}

        elif action == "update":
            if user_id is None:
                raise ValueError("update action requires 'user_id'")
            if user_id not in self._storage:
                return {}
            data = context.get("data", {})
            self._storage[user_id].update(data)
            return {"status": "updated", "user_id": user_id}

        elif action == "delete":
            if user_id is None:
                raise ValueError("delete action requires 'user_id'")
            self._storage.pop(user_id, None)
            return {"status": "deleted", "user_id": user_id}

        elif action == "list":
            return list(self._storage.keys())

        else:
            raise ValueError(f"Unknown action: {action}")


# Module-level PLUGIN for auto-discovery
PLUGIN = UserPlugin()