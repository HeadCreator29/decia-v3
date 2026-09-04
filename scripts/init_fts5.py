#!/usr/bin/env python3
"""
scripts/init_fts5.py - Initialize SQLite database with FTS5 virtual table
for unified search across all memory types.

Usage:
    python scripts/init_fts5.py [--db-path PATH]
"""

import sqlite3
import os
import argparse
from pathlib import Path


SCHEMA_SQL = """
-- Core memories table (stores all memory types)
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,           -- FACT, MEMORY, DECISION, GOAL, PREDICTION, LESSON, INTERPRETATION, UNKNOWN, REFLECTION
    content TEXT NOT NULL,        -- Main text content
    date TEXT NOT NULL,           -- ISO8601 datetime
    source TEXT,                  -- Origin: user, system, decision, prediction, etc.
    confidence REAL DEFAULT 0.7,  -- 0.0-1.0
    relations TEXT,               -- JSON array of {target_id, relation_type}
    encrypted INTEGER DEFAULT 0,  -- 0=no, 1=yes
    metadata TEXT,                -- JSON for type-specific fields
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- FTS5 virtual table for full-text search on content
CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
    content,
    content='memories',
    content_rowid='rowid'
);

-- Triggers to keep FTS5 in sync
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

-- Indices for common queries
CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type);
CREATE INDEX IF NOT EXISTS idx_memories_date ON memories(date);
CREATE INDEX IF NOT EXISTS idx_memories_confidence ON memories(confidence);
CREATE INDEX IF NOT EXISTS idx_memories_encrypted ON memories(encrypted);
CREATE INDEX IF NOT EXISTS idx_memories_source ON memories(source);
"""


def init_fts5(db_path: str) -> None:
    """Initialize SQLite database with FTS5 schema."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        print(f"✅ FTS5 schema initialized at {db_path}")
    finally:
        conn.close()


def verify_fts5(db_path: str) -> bool:
    """Verify FTS5 is working correctly."""
    conn = sqlite3.connect(db_path)
    try:
        # Check tables exist
        cursor = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type IN ('table', 'virtual table') 
            AND name IN ('memories', 'memories_fts')
        """)
        tables = {row[0] for row in cursor.fetchall()}
        
        if 'memories' not in tables or 'memories_fts' not in tables:
            print(f"❌ Missing tables: {tables}")
            return False
        
        # Test FTS5 insert/search
        conn.execute("INSERT INTO memories (id, type, content, date, confidence) VALUES (?, ?, ?, ?, ?)",
                    ("test-1", "FACT", "test content for search", "2026-01-01T00:00:00", 0.8))
        conn.commit()
        
        cursor = conn.execute("SELECT content FROM memories_fts WHERE content MATCH 'search'")
        result = cursor.fetchone()
        
        if result and "search" in result[0]:
            print("✅ FTS5 search working")
            conn.execute("DELETE FROM memories WHERE id = 'test-1'")
            conn.commit()
            return True
        else:
            print("❌ FTS5 search not working")
            return False
            
    except Exception as e:
        print(f"❌ FTS5 verification failed: {e}")
        return False
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Initialize SQLite FTS5 database")
    parser.add_argument("--db-path", default="data/search/memories.db",
                       help="Path to SQLite database file")
    parser.add_argument("--verify", action="store_true", 
                       help="Verify FTS5 is working after init")
    args = parser.parse_args()
    
    init_fts5(args.db_path)
    
    if args.verify:
        verify_fts5(args.db_path)


if __name__ == "__main__":
    main()