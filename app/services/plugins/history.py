# app/services/plugins/history.py - HistoryPlugin
# Conversation history and temporal query plugin

import time
from app.services.plugins.base import ServicePlugin


class HistoryPlugin:
    """Plugin for managing conversation history with temporal queries."""

    def __init__(self):
        self._events: list = []
        self._plugin = ServicePlugin(
            name="HISTORY",
            category="ARCHIVE",
            description="Conversation history and temporal query",
            execute=self.execute,
        )

    @property
    def name(self) -> str:
        return self._plugin.name

    @property
    def category(self) -> str:
        return self._plugin.category

    def execute(self, context: dict) -> dict | list:
        """Execute history operation.

        Args:
            context: Dict with 'action' (add|query|clear) and optional filters

        Returns:
            Result based on action
        """
        action = context.get("action", "query")

        if action == "add":
            event = context.get("event", {})
            event = dict(event)  # copy
            event["timestamp"] = time.time()
            self._events.append(event)
            return {"status": "added", "count": len(self._events)}

        elif action == "query":
            since = context.get("since")
            until = context.get("until")
            limit = context.get("limit")
            event_type = context.get("type")

            results = self._events

            if since is not None:
                results = [e for e in results if e.get("timestamp", 0) >= since]
            if until is not None:
                results = [e for e in results if e.get("timestamp", 0) <= until]
            if event_type is not None:
                results = [e for e in results if e.get("type") == event_type]
            if limit is not None:
                results = results[-limit:]  # most recent

            return results

        elif action == "clear":
            count = len(self._events)
            self._events.clear()
            return {"status": "cleared", "count": count}

        else:
            raise ValueError(f"Unknown action: {action}")


# Module-level PLUGIN for auto-discovery
PLUGIN = HistoryPlugin()