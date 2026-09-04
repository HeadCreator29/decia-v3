# app/services/plugins/planner.py - PlannerPlugin
# Task planning and scheduling plugin

from app.services.plugins.base import ServicePlugin


class PlannerPlugin:
    """Plugin for managing plans and tasks."""

    def __init__(self):
        self._storage: dict = {}
        self._plugin = ServicePlugin(
            name="PLANNER",
            category="PLANNER",
            description="Task planning and scheduling",
            execute=self.execute,
        )

    @property
    def name(self) -> str:
        return self._plugin.name

    @property
    def category(self) -> str:
        return self._plugin.category

    def execute(self, context: dict) -> dict | list:
        """Execute planner operation.

        Args:
            context: Dict with action (create|get|update|delete|query|list) and parameters

        Returns:
            Result based on action
        """
        action = context.get("action", "get")
        key = context.get("key")

        if action == "create":
            if key is None:
                raise ValueError("create action requires 'key'")
            data = context.get("data", {})
            self._storage[key] = data
            return {"status": "created", "key": key}

        elif action == "get":
            if key is None:
                return {}
            return self._storage.get(key, {})

        elif action == "update":
            if key is None:
                raise ValueError("update action requires 'key'")
            if key not in self._storage:
                return {}
            data = context.get("data", {})
            self._storage[key].update(data)
            return {"status": "updated", "key": key}

        elif action == "delete":
            if key is None:
                raise ValueError("delete action requires 'key'")
            self._storage.pop(key, None)
            return {"status": "deleted", "key": key}

        elif action == "query":
            status = context.get("status")
            tag = context.get("tag")
            results = []
            for plan in self._storage.values():
                if status and plan.get("status") != status:
                    continue
                if tag and tag not in plan.get("tags", []):
                    continue
                results.append(plan)
            return results

        elif action == "list":
            return list(self._storage.keys())

        else:
            raise ValueError(f"Unknown action: {action}")


# Module-level PLUGIN for auto-discovery
PLUGIN = PlannerPlugin()