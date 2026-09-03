# app/services/plugins/search.py - SearchPlugin with SQLite + FTS5
# Unified search across all memory types with filters

import sqlite3
import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path

from app.services.plugins.base import ServicePlugin
from app.services.encryption import decrypt_memory_data, is_encryption_required


DEFAULT_DB_PATH = "data/search/memories.db"


class SearchPlugin(ServicePlugin):
    """SearchPlugin with SQLite + FTS5 for unified search across all memory types."""

    def __init__(self, db_path: str = None, **kwargs):
        super().__init__(
            name="SEARCH",
            category="ARCHIVE",
            description="Unified search across all memory types with FTS5",
            **kwargs,
        )
        self.db_path = db_path or DEFAULT_DB_PATH
        self._conn = None
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_db(self) -> None:
        """Initialize database schema if needed."""
        conn = self._get_connection()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                date TEXT NOT NULL,
                source TEXT,
                confidence REAL DEFAULT 0.7,
                relations TEXT,
                encrypted INTEGER DEFAULT 0,
                metadata TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                content,
                content='memories',
                content_rowid='rowid'
            );
            CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                INSERT INTO memories_fts(rowid, content) VALUES (new.rowid, new.content);
            END;
            CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, content) VALUES('delete', old.rowid, old.content);
            END;
            CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, content) VALUES('delete', old.rowid, old.content);
                INSERT INTO memories_fts(rowid, content) VALUES (new.rowid, new.content);
            END;
            CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type);
            CREATE INDEX IF NOT EXISTS idx_memories_date ON memories(date);
            CREATE INDEX IF NOT EXISTS idx_memories_confidence ON memories(confidence);
            CREATE INDEX IF NOT EXISTS idx_memories_encrypted ON memories(encrypted);
            CREATE INDEX IF NOT EXISTS idx_memories_source ON memories(source);
        """)

    def _row_to_dict(self, row: sqlite3.Row) -> Dict:
        """Convert SQLite row to dict with decryption if needed."""
        item = dict(row)
        # Parse JSON fields
        for field in ["relations", "metadata"]:
            if item.get(field):
                try:
                    item[field] = json.loads(item[field])
                except (json.JSONDecodeError, TypeError):
                    pass
        return item

    def _decrypt_if_needed(self, item: Dict) -> Dict:
        """Decrypt item if encrypted and passphrase available."""
        if item.get("encrypted") and is_encryption_required(item.get("type", "")):
            try:
                encrypted_data = {
                    "encrypted": True,
                    "algorithm": "aes-gcm",
                    "type": item.get("type", "MEMORY"),
                    "content": item.get("content", ""),
                }
                # Note: In real usage, passphrase would come from user
                # For now, return as-is if encrypted
                pass
            except Exception:
                pass
        return item

    # ── Public API ──

    def query(self, text: str = "", filters: Optional[Dict] = None) -> Dict:
        """Search memories with FTS5 and optional filters.
        
        Args:
            text: Search text (FTS5 query syntax supported)
            filters: Optional dict with keys:
                - type: str or List[str]
                - date_range: (start, end) ISO8601 strings
                - confidence_range: (min, max) floats
                - source: str or List[str]
                - limit: int
                - offset: int
        
        Returns:
            Dict with 'results' (list of items) and 'total' (int)
        """
        conn = self._get_connection()
        filters = filters or {}
        
        # Build query
        where_clauses = []
        params = []
        
        # FTS5 search
        if text:
            where_clauses.append("memories_fts MATCH ?")
            params.append(text)
        
        # Type filter
        if "type" in filters:
            types = filters["type"] if isinstance(filters["type"], list) else [filters["type"]]
            placeholders = ",".join(["?" for _ in types])
            where_clauses.append(f"type IN ({placeholders})")
            params.extend(types)
        
        # Date range filter
        if "date_range" in filters:
            start, end = filters["date_range"]
            if start:
                where_clauses.append("date >= ?")
                params.append(start)
            if end:
                where_clauses.append("date <= ?")
                params.append(end)
        
        # Confidence range
        if "confidence_range" in filters:
            min_conf, max_conf = filters["confidence_range"]
            if min_conf is not None:
                where_clauses.append("confidence >= ?")
                params.append(min_conf)
            if max_conf is not None:
                where_clauses.append("confidence <= ?")
                params.append(max_conf)
        
        # Source filter
        if "source" in filters:
            sources = filters["source"] if isinstance(filters["source"], list) else [filters["source"]]
            placeholders = ",".join(["?" for _ in sources])
            where_clauses.append(f"source IN ({placeholders})")
            params.extend(sources)
        
        # Build final query
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        if text:
            # FTS5 search: use memories_fts table
            count_sql = f"SELECT COUNT(*) FROM memories_fts{where_sql}"
            total = conn.execute(count_sql, params).fetchone()[0]
            
            # Limit/offset
            limit = filters.get("limit", 50)
            offset = filters.get("offset", 0)
            
            # Select results with FTS5 ranking
            select_sql = f"""
                SELECT memories.* FROM memories
                JOIN memories_fts ON memories.rowid = memories_fts.rowid
                {where_sql}
                ORDER BY 
                    bm25(memories_fts),
                    date DESC
                LIMIT ? OFFSET ?
            """
            search_params = params + [limit, offset]
        else:
            # Regular search without FTS5
            count_sql = f"SELECT COUNT(*) FROM memories{where_sql}"
            total = conn.execute(count_sql, params).fetchone()[0]
            
            # Limit/offset
            limit = filters.get("limit", 50)
            offset = filters.get("offset", 0)
            
            # Select results
            select_sql = f"""
                SELECT memories.* FROM memories
                {where_sql}
                ORDER BY date DESC
                LIMIT ? OFFSET ?
            """
            search_params = params + [limit, offset]
        
        cursor = conn.execute(select_sql, search_params)
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            item = self._row_to_dict(row)
            item = self._decrypt_if_needed(item)
            results.append(item)
        
        return {
            "results": results,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def filter_by_type(self, type_filter: str) -> Dict:
        """Filter by memory type."""
        return self.query("", {"type": type_filter})

    def filter_by_date_range(self, start: str, end: str) -> Dict:
        """Filter by date range."""
        return self.query("", {"date_range": (start, end)})

    def filter_by_confidence(self, min_conf: float = 0.0, max_conf: float = 1.0) -> Dict:
        """Filter by confidence range."""
        return self.query("", {"confidence_range": (min_conf, max_conf)})

    def filter_by_relations(self, relation_type: str, target_id: str) -> Dict:
        """Filter by relation to a target memory."""
        # This requires JSON querying on relations field
        conn = self._get_connection()
        cursor = conn.execute("""
            SELECT * FROM memories 
            WHERE json_extract(relations, '$[*].target_id') LIKE ?
        """, (f"%{target_id}%",))
        rows = cursor.fetchall()
        return {"results": [self._row_to_dict(r) for r in cursor.fetchall()], "total": len(rows)}

    def get_by_id(self, item_id: str) -> Optional[Dict]:
        """Get a single item by ID."""
        conn = self._get_connection()
        cursor = conn.execute("SELECT * FROM memories WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        if row:
            return self._decrypt_if_needed(self._row_to_dict(row))
        return None

    def list_all(self, limit: int = 100) -> List[Dict]:
        """List all memories (with limit)."""
        conn = self._get_connection()
        cursor = conn.execute("SELECT * FROM memories ORDER BY date DESC LIMIT ?", (limit,))
        return [self._row_to_dict(r) for r in cursor.fetchall()]

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None


# Module-level PLUGIN for auto-discovery
PLUGIN = SearchPlugin()

# Lowercase alias for backward compatibility
plugin = PLUGIN