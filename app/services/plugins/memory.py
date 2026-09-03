# app/services/plugins/memory.py - MemoryPlugin
# Long-term memory with CRUD, deduplication, canonical forms

import re
from app.services.plugins.base import ServicePlugin


def _canonicalize(text: str) -> str:
    """Normalize text to canonical form: lowercase, trimmed, collapsed whitespace."""
    if not isinstance(text, str):
        return str(text)
    return re.sub(r"\s+", " ", text.strip().lower())


def _content_hash(content: str) -> str:
    """Generate a simple hash for deduplication."""
    return str(hash(_canonicalize(content)))


class MemoryPlugin:
    """Plugin for long-term memory with deduplication and canonical forms."""

    def __init__(self):
        self._storage: dict = {}  # key -> {content, tags, hash}
        self._by_hash: dict = {}  # content_hash -> key (for dedup)
        self._plugin = ServicePlugin(
            name="MEMORY",
            category="ARCHIVE",
            description="Long-term memory with deduplication and canonical forms",
            execute=self.execute,
        )

    @property
    def name(self) -> str:
        return self._plugin.name

    @property
    def category(self) -> str:
        return self._plugin.category

    def execute(self, context: dict) -> dict | list:
        """Execute memory operation.

        Args:
            context: Dict with action and parameters

        Returns:
            Result based on action
        """
        action = context.get("action", "read")

        if action == "create":
            key = context.get("key")
            data = context.get("data", {})
            content = data.get("content", "")
            tags = data.get("tags", [])

            if key is None:
                raise ValueError("create action requires 'key'")

            # Canonicalize content
            canon = _canonicalize(content)
            c_hash = _content_hash(canon)

            # Deduplicate: if same content exists, return existing key
            if c_hash in self._by_hash:
                existing_key = self._by_hash[c_hash]
                return {"status": "duplicate", "key": existing_key, "canonical": canon}

            # Store new
            self._storage[key] = {"content": canon, "tags": tags, "hash": c_hash}
            self._by_hash[c_hash] = key
            return {"status": "created", "key": key, "canonical": canon}

        elif action == "read":
            key = context.get("key")
            if key is None:
                return {}
            entry = self._storage.get(key, {})
            return entry

        elif action == "update":
            key = context.get("key")
            data = context.get("data", {})

            if key is None:
                raise ValueError("update action requires 'key'")
            if key not in self._storage:
                return {}

            old_entry = self._storage[key]
            old_hash = old_entry["hash"]

            # Handle content update with dedup
            if "content" in data:
                new_content = data["content"]
                canon = _canonicalize(new_content)
                new_hash = _content_hash(canon)

                # If content unchanged, just update tags
                if new_hash == old_hash:
                    if "tags" in data:
                        old_entry["tags"] = data["tags"]
                    return {"status": "updated", "key": key, "canonical": canon}

                # Content changed - check dedup
                if new_hash in self._by_hash and self._by_hash[new_hash] != key:
                    # Duplicate exists - merge or reject
                    return {"status": "duplicate", "key": self._by_hash[new_hash], "canonical": canon}

                # Update hash mapping
                del self._by_hash[old_hash]
                self._by_hash[new_hash] = key
                old_entry["content"] = canon
                old_entry["hash"] = new_hash

            if "tags" in data:
                old_entry["tags"] = data["tags"]

            return {"status": "updated", "key": key, "canonical": old_entry["content"]}

        elif action == "delete":
            key = context.get("key")
            if key is None:
                raise ValueError("delete action requires 'key'")
            entry = self._storage.pop(key, None)
            if entry:
                self._by_hash.pop(entry["hash"], None)
            return {"status": "deleted", "key": key}

        elif action == "list":
            return {k: v for k, v in self._storage.items()}

        elif action == "search":
            query = context.get("query", "")
            canon_query = _canonicalize(query)
            results = {}
            for k, v in self._storage.items():
                if canon_query in v["content"]:
                    results[k] = v
            return results

        elif action == "query_by_tag":
            tag = context.get("tag", "")
            results = {}
            for k, v in self._storage.items():
                if tag in v.get("tags", []):
                    results[k] = v
            return results

        else:
            raise ValueError(f"Unknown action: {action}")


# ── type enum ──────────────────────────────────────────────────────
_TYPED_MEMORY_TYPES = frozenset(
    ["FACT", "MEMORY", "DECISION", "GOAL", "PREDICTION", "LESSON", "INTERPRETATION", "UNKNOWN"]
)

_RELATION_TYPES = frozenset(["relates-to", "supports", "contradicts", "supersedes"])

_VALID_CONFIDENCE = lambda v: isinstance(v, (int, float)) and 0.0 <= v <= 1.0


# ── helpers ──────────────────────────────────────────────────────
def _validate_type(mtype: str) -> bool:
    """Check if a memory type is in the 8-type enum."""
    return mtype in _TYPED_MEMORY_TYPES


def _validate_relation(rtype: str) -> bool:
    """Check if a relation type is valid."""
    return rtype in _RELATION_TYPES


def _default_encryption_flag(mtype: str) -> str:
    """Return encryption flag per type policy."""
    mandatory = {"INTERPRETATION", "LESSON"}
    optional = {"MEMORY", "DECISION", "PREDICTION", "GOAL"}
    if mtype in mandatory:
        return "mandatory"
    if mtype in optional:
        return "optional"
    # FACT and UNKNOWN: no encryption
    return "none"


# ── MemoryPlugin methods (extended) ──────────────────────────────
def _ensure_type_confidence(memory: dict, mtype: str = None, conf: float = None) -> dict:
    """Ensure memory has valid type and confidence, applying defaults if needed."""
    if mtype is not None and _validate_type(mtype):
        memory["type"] = mtype
    if conf is not None and _VALID_CONFIDENCE(conf):
        memory["confidence"] = conf
    if "type" not in memory:
        memory["type"] = "MEMORY"
    if "confidence" not in memory:
        memory["confidence"] = 0.7
    return memory


# ── create_typed ─────────────────────────────────────────────────
def create_typed(
    content: str,
    mtype: str = "MEMORY",
    confidence: float = 0.7,
    relations: list = None,
    encryption: str = None,  # None -> apply default per type policy
) -> dict:
    """Create a typed memory with full v2 schema.

    Args:
        content: The memory content text.
        mtype: Memory type from the 8-type enum (default: MEMORY).
        confidence: Confidence score 0.0-1.0 (default: 0.7).
        relations: List of relation dicts with {type, target_id}.
        encryption: Encryption policy (none|optional|mandatory).

    Returns:
        dict with the typed memory including all v2 fields.
    """
    if not isinstance(content, str):
        raise ValueError("content must be a string")
    if not _validate_type(mtype):
        raise ValueError(f"Invalid memory type: {mtype}. Must be one of {sorted(_TYPED_MEMORY_TYPES)}")
    if not _VALID_CONFIDENCE(confidence):
        raise ValueError("confidence must be a number in [0.0, 1.0]")

    if encryption is None:
        encryption = _default_encryption_flag(mtype)
    elif encryption:
        pass  # use provided value

    import time, datetime
    now = datetime.datetime.now().isoformat()

    memory = {
        "id": None,  # will be set by caller/storage
        "content": content,
        "date": None,
        "source": "conversation",
        "type": mtype,
        "confidence": confidence,
        "relations": relations if relations else [],
        "encryption_flag": encryption,
        "metadata": {},
        "version": 1,
        "created_at": now,
        "updated_at": now,
    }
    return _ensure_type_confidence(memory)


# ── get_by_type ──────────────────────────────────────────────────
def get_by_type(plugin, type: str) -> list:
    """Filter memories stored in the plugin by type.

    Args:
        plugin: A MemoryPlugin instance.
        type: Memory type to filter by.

    Returns:
        List of memories matching the given type.
    """
    if not _validate_type(type):
        raise ValueError(f"Invalid memory type: {type}")
    all_memories = plugin.execute({"action": "list"})
    results = []
    for entry in all_memories.values():
        if entry.get("type") == type:
            results.append(entry)
    return results


# ── get_by_confidence_range ──────────────────────────────────────
def get_by_confidence_range(plugin, min_conf: float, max_conf: float) -> list:
    """Filter memories stored in the plugin by confidence range.

    Args:
        plugin: A MemoryPlugin instance.
        min_conf: Minimum confidence (inclusive, 0.0-1.0).
        max_conf: Maximum confidence (inclusive, 0.0-1.0).

    Returns:
        List of memories with confidence in [min_conf, max_conf].
    """
    if not (_VALID_CONFIDENCE(min_conf) and _VALID_CONFIDENCE(max_conf)):
        raise ValueError("confidence values must be in [0.0, 1.0]")
    if min_conf > max_conf:
        raise ValueError("min_conf must be <= max_conf")
    all_memories = plugin.execute({"action": "list"})
    results = []
    for entry in all_memories.values():
        conf = entry.get("confidence", 0.7)
        if min_conf <= conf <= max_conf:
            results.append(entry)
    return results


# ── add_relation ─────────────────────────────────────────────────
def add_relation(plugin, source_id: str, target_id: str, relation_type: str) -> dict:
    """Add a relation between two memories.

    Args:
        plugin: A MemoryPlugin instance.
        source_id: The source memory ID.
        target_id: The target memory ID.
        relation_type: One of [relates-to, supports, contradicts, supersedes].

    Returns:
        dict with the updated relation info.
    """
    if not _validate_relation(relation_type):
        raise ValueError(
            f"Invalid relation type: {relation_type}. "
            f"Must be one of {sorted(_RELATION_TYPES)}"
        )
    if source_id == target_id:
        raise ValueError("source_id and target_id must be different")

    # Execute update on the plugin
    result = plugin.execute(
        {
            "action": "update",
            "key": source_id,
            "data": {
                "relations": [
                    {"type": relation_type, "target_id": target_id}
                ]
            },
        }
    )
    return {"status": "relation_added", "source_id": source_id, "target_id": target_id, "relation_type": relation_type, "result": result}


# ── update_confidence ────────────────────────────────────────────
def update_confidence(plugin, memory_id: str, confidence: float) -> dict:
    """Update the confidence score of a memory.

    Args:
        plugin: A MemoryPlugin instance.
        memory_id: The memory ID to update.
        confidence: New confidence score (0.0-1.0).

    Returns:
        dict with the update result.
    """
    if not _VALID_CONFIDENCE(confidence):
        raise ValueError("confidence must be a number in [0.0, 1.0]")
    result = plugin.execute(
        {"action": "update", "key": memory_id, "data": {"confidence": confidence}}
    )
    return {"status": "confidence_updated", "memory_id": memory_id, "confidence": confidence, "result": result}


# ── search_by_content ────────────────────────────────────────────
def search_by_content(plugin, query: str, filters: dict = None) -> list:
    """Content search with optional type/date/confidence filters.

    Args:
        plugin: A MemoryPlugin instance.
        query: Search query string.
        filters: Optional dict with filters: type, min_conf, max_conf, date_from, date_to.

    Returns:
        List of memories matching the content query and filters.
    """
    if not isinstance(query, str):
        raise ValueError("query must be a string")
    all_memories = plugin.execute({"action": "list"})
    results = []
    for entry in all_memories.values():
        # Content match (canonical substring)
        content = entry.get("content", "")
        canon = content.lower().strip()
        if query.lower() not in canon:
            continue

        # Apply filters
        if filters:
            # Filter by type
            if "type" in filters:
                if entry.get("type") != filters["type"]:
                    continue
            # Filter by confidence range
            if "min_conf" in filters or "max_conf" in filters:
                conf = entry.get("confidence", 0.7)
                min_c = filters.get("min_conf", 0.0)
                max_c = filters.get("max_conf", 1.0)
                if not (min_c <= conf <= max_c):
                    continue
            # Filter by date range
            if "date_from" in filters or "date_to" in filters:
                mem_date = entry.get("date", "")
                date_from = filters.get("date_from", "")
                date_to = filters.get("date_to", "")
                if date_from and mem_date < date_from:
                    continue
                if date_to and mem_date > date_to:
                    continue

        results.append(entry)
    return results


# ── migrate_legacy ────────────────────────────────────────────────
def migrate_legacy(plugin, default_type: str = "MEMORY", default_confidence: float = 0.7) -> dict:
    """One-shot migration: enrich all entries with v2 fields.

    DRY RUN mode - does not write to disk. Returns a MigrationReport.

    Args:
        plugin: A MemoryPlugin instance.
        default_type: Default type for untyped entries (default: MEMORY).
        default_confidence: Default confidence for untyped entries (default: 0.7).

    Returns:
        MigrationReport dict with {total, migrated, errors, backup_path, checksum}.
    """
    if not _validate_type(default_type):
        raise ValueError(f"Invalid default type: {default_type}")

    import hashlib, json, time
    from pathlib import Path
    from datetime import datetime

    archive_path = Path(__file__).resolve().parents[3] / "data" / "archive"
    memories_path = archive_path / "memories.json"
    backup_path = archive_path / "memories.pre-migration.backup.json"

    # Read current memories
    try:
        with open(memories_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return {
            "total": 0,
            "migrated": 0,
            "errors": [str(e)],
            "backup_path": None,
            "checksum": None,
        }

    memories = data.get("memories", [])
    total = len(memories)
    migrated = 0
    errors = []

    # Backup only if not already backed up (dry-run: still create backup path reference)
    backup_created = backup_path.exists()

    for idx, memory in enumerate(memories):
        try:
            # Skip already-migrated entries (source="migration")
            if memory.get("source") == "migration":
                continue

            # Enrich with v2 fields
            now = datetime.now().isoformat()

            # Map legacy "text" to "content" if present
            if "text" in memory and "content" not in memory:
                memory["content"] = memory.pop("text")

            # Ensure type and confidence
            if "type" not in memory:
                memory["type"] = default_type
            if "confidence" not in memory:
                memory["confidence"] = default_confidence

            # Set default v2 fields
            if "relations" not in memory:
                memory["relations"] = []
            if "encryption_flag" not in memory:
                memory["encryption_flag"] = _default_encryption_flag(memory.get("type", default_type))
            if "metadata" not in memory:
                memory["metadata"] = {}
            if "version" not in memory:
                memory["version"] = 1
            if "created_at" not in memory:
                memory["created_at"] = now
            if "updated_at" not in memory:
                memory["updated_at"] = now
            if "source" not in memory:
                memory["source"] = "migration"

            migrated += 1

        except Exception as e:
            errors.append(f"entry {idx}: {str(e)}")

    # Compute checksum of migrated data
    checksum = None
    try:
        mc = json.dumps(data, sort_keys=True, default=str)
        checksum = hashlib.sha256(mc.encode("utf-8")).hexdigest()
    except Exception:
        checksum = None

    report = {
        "total": total,
        "migrated": migrated,
        "errors": errors,
        "backup_path": str(backup_path) if backup_created else None,
        "checksum": checksum,
    }

    return report


# Module-level PLUGIN for auto-discovery
PLUGIN = MemoryPlugin()