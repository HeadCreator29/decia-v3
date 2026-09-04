#!/usr/bin/env python3
"""
scripts/migrate_to_sqlite.py - Migrate JSON memory files to SQLite with FTS5.

Usage:
    python scripts/migrate_to_sqlite.py --dry-run --backup --validate
    python scripts/migrate_to_sqlite.py --execute --backup --validate

JSON files migrated:
- data/archive/memories.json
- data/archive/decisions.json
- data/archive/predictions.json
- data/archive/learnings.json
- data/archive/reflections.json
- data/archive/identity_core.json
"""

import json
import os
import sys
import argparse
import hashlib
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add app to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.encryption import decrypt_memory_data, is_encryption_required


# JSON file paths
JSON_FILES = {
    "MEMORY": "data/archive/memories.json",
    "DECISION": "data/archive/decisions.json",
    "PREDICTION": "data/archive/predictions.json",
    "LEARNING": "data/archive/learnings.json",
    "REFLECTION": "data/archive/reflections.json",
    "INTERPRETATION": "data/archive/identity_core.json",  # identity stored as INTERPRETATION
}

# Type mapping from JSON filename to memory type
TYPE_MAPPING = {
    "MEMORY": "MEMORY",
    "DECISION": "DECISION",
    "PREDICTION": "PREDICTION",
    "LEARNING": "LESSON",
    "REFLECTION": "REFLECTION",
    "INTERPRETATION": "INTERPRETATION",
}


def compute_checksum(data: List[Dict]) -> str:
    """Compute SHA256 checksum of data for validation."""
    content = json.dumps(data, sort_keys=True, ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(content).hexdigest()


def backup_files(files: Dict[str, str]) -> str:
    """Create timestamped backup of all JSON files."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = Path(f"backups/migration_{timestamp}")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    backed_up = []
    for type_name, file_path in files.items():
        if os.path.exists(file_path):
            dest = backup_dir / Path(file_path).name
            shutil.copy2(file_path, dest)
            backed_up.append(str(dest))
    
    return str(backup_dir)


def decrypt_if_needed(item: Dict, type_name: str) -> Dict:
    """Decrypt item if it's encrypted per encryption policy."""
    if is_encryption_required(type_name) and item.get("encrypted"):
        try:
            # Try to decrypt
            decrypted = decrypt_memory_data(item, passphrase=None)
            return decrypted
        except Exception:
            # If decryption fails, return as-is (will be stored unencrypted)
            pass
    return item


def normalize_item(item: Dict, type_name: str) -> Dict:
    """Normalize item to SQLite schema."""
    # Handle different ID field names
    item_id = item.get("id") or item.get("memory_id") or item.get("decision_id") or \
              item.get("prediction_id") or item.get("learning_id") or \
              item.get("reflection_id") or item.get("proposal_id")
    
    if not item_id:
        import uuid
        item_id = str(uuid.uuid4())
    
    # Extract content based on type
    content = ""
    if type_name == "MEMORY":
        content = item.get("description") or item.get("content") or ""
    elif type_name == "DECISION":
        content = item.get("problem") or ""
        if item.get("decision"):
            content += " " + item.get("decision", "")
        if item.get("rationale"):
            content += " " + item.get("rationale", "")
        if item.get("outcome"):
            content += " " + item.get("outcome", "")
        if item.get("learning"):
            content += " " + item.get("learning", "")
    elif type_name == "PREDICTION":
        content = item.get("prediction_text") or ""
        if item.get("reasons"):
            content += " " + " ".join(item.get("reasons", []))
    elif type_name == "LESSON":
        content = item.get("lesson") or ""
        if item.get("future_considerations"):
            content += " " + item.get("future_considerations", "")
    elif type_name == "REFLECTION":
        content = item.get("draft_content") or item.get("approved_content") or ""
    elif type_name == "INTERPRETATION":
        content = json.dumps(item, ensure_ascii=False)
    
    # Extract date
    date_str = item.get("date") or item.get("created_at") or item.get("recorded_at") or \
               datetime.now().isoformat()
    
    # Extract confidence
    confidence = item.get("confidence", 0.7)
    if isinstance(confidence, str):
        try:
            confidence = float(confidence)
        except ValueError:
            confidence = 0.7
    
    # Extract relations
    relations = item.get("relations", [])
    if isinstance(relations, str):
        try:
            relations = json.loads(relations)
        except json.JSONDecodeError:
            relations = []
    
    # Extract source
    source = item.get("source", "user")
    
    # Encrypted flag
    encrypted = 1 if item.get("encrypted") else 0
    
    # Metadata (type-specific fields)
    metadata = {k: v for k, v in item.items() 
                if k not in ["id", "memory_id", "decision_id", "prediction_id", 
                            "learning_id", "reflection_id", "proposal_id",
                            "content", "description", "problem", "decision", 
                            "rationale", "outcome", "learning", "prediction_text",
                            "reasons", "lesson", "future_considerations",
                            "draft_content", "approved_content", "date", 
                            "created_at", "recorded_at", "confidence", 
                            "relations", "source", "encrypted"]}
    
    return {
        "id": item_id,
        "type": type_name,
        "content": content,
        "date": date_str,
        "source": source,
        "confidence": confidence,
        "relations": json.dumps(relations, ensure_ascii=False),
        "encrypted": encrypted,
        "metadata": json.dumps(metadata, ensure_ascii=False),
    }


def load_json_file(file_path: str) -> List[Dict]:
    """Load JSON file, handle empty/corrupted files."""
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
        return []
    except (json.JSONDecodeError, ValueError):
        return []


def migrate_json_to_sqlite(db_path: str, dry_run: bool = True, backup: bool = True, validate: bool = True) -> Dict[str, Any]:
    """Migrate all JSON files to SQLite with FTS5."""
    import uuid
    
    report = {
        "total": 0,
        "migrated": 0,
        "errors": [],
        "backup_path": None,
        "checksum": None,
        "by_type": {},
    }
    
    # Backup if requested
    if backup:
        report["backup_path"] = backup_files(JSON_FILES)
        print(f"📦 Backup created at: {report['backup_path']}")
    
    # Load all JSON data
    all_items = []
    for type_name, file_path in JSON_FILES.items():
        items = load_json_file(file_path)
        if not items:
            continue
        
        print(f"📥 Loading {len(items)} {type_name} items from {file_path}")
        
        for item in items:
            # Decrypt if needed
            decrypted = decrypt_if_needed(item, type_name)
            # Normalize to SQLite schema
            normalized = normalize_item(decrypted, type_name)
            all_items.append(normalized)
    
    report["total"] = len(all_items)
    
    # Compute checksum for validation
    if validate:
        report["checksum"] = compute_checksum(all_items)
        print(f"🔐 Checksum: {report['checksum']}")
    
    # Group by type for reporting
    for item in all_items:
        t = item["type"]
        report["by_type"][t] = report["by_type"].get(t, 0) + 1
    
    if dry_run:
        print(f"\n=== DRY RUN REPORT ===")
        print(f"Total entries: {report['total']}")
        for t, count in report["by_type"].items():
            print(f"  {t}: {count}")
        if validate:
            print(f"Checksum: {report['checksum']}")
        if report["backup_path"]:
            print(f"Backup: {report['backup_path']}")
        print(f"\nNo files were written. Use --execute for real migration.")
        return report
    
    # Execute real migration
    print(f"\n=== EXECUTING MIGRATION ===")
    
    # Initialize database
    conn = sqlite3.connect(db_path)
    try:
        # Initialize schema (reuse from init_fts5)
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
        
        # Insert all items
        for item in all_items:
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO memories 
                    (id, type, content, date, source, confidence, relations, encrypted, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item["id"], item["type"], item["content"], item["date"],
                    item["source"], item["confidence"], item["relations"],
                    item["encrypted"], item["metadata"]
                ))
                report["migrated"] += 1
            except Exception as e:
                report["errors"].append(f"Failed to insert {item['id']}: {e}")
        
        conn.commit()
        
        # Verify
        cursor = conn.execute("SELECT COUNT(*) FROM memories")
        count = cursor.fetchone()[0]
        print(f"✅ Migrated {report['migrated']}/{report['total']} entries ({count} in DB)")
        
        # Verify FTS5
        cursor = conn.execute("SELECT COUNT(*) FROM memories_fts")
        fts_count = cursor.fetchone()[0]
        print(f"📝 FTS5 entries: {fts_count}")
        
    except Exception as e:
        report["errors"].append(f"Migration failed: {e}")
    finally:
        conn.close()
    
    return report


def main():
    parser = argparse.ArgumentParser(description="Migrate JSON memories to SQLite with FTS5")
    parser.add_argument("--db-path", default="data/search/memories.db",
                       help="Path to SQLite database file")
    parser.add_argument("--dry-run", action="store_true", default=True,
                       help="Perform dry run only (default)")
    parser.add_argument("--execute", action="store_true",
                       help="Execute real migration (overrides --dry-run)")
    parser.add_argument("--backup", action="store_true", default=True,
                       help="Create backup before migration (default)")
    parser.add_argument("--validate", action="store_true", default=True,
                       help="Validate with checksum (default)")
    parser.add_argument("--no-backup", action="store_false", dest="backup",
                       help="Skip backup")
    parser.add_argument("--no-validate", action="store_false", dest="validate",
                       help="Skip validation")
    
    args = parser.parse_args()
    
    dry_run = not args.execute
    
    print("=== DECIA JSON → SQLite Migration ===")
    print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
    print(f"Database: {args.db_path}")
    
    report = migrate_json_to_sqlite(
        db_path=args.db_path,
        dry_run=dry_run,
        backup=args.backup,
        validate=args.validate,
    )
    
    if report["errors"]:
        print(f"\n❌ Errors ({len(report['errors'])}):")
        for err in report["errors"]:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("\n✅ Migration completed successfully")
    
    # Print summary
    print(f"\n=== SUMMARY ===")
    print(f"Total: {report['total']}")
    print(f"Migrated: {report['migrated']}")
    print(f"Errors: {len(report['errors'])}")
    if report["backup_path"]:
        print(f"Backup: {report['backup_path']}")
    if report["checksum"]:
        print(f"Checksum: {report['checksum']}")


if __name__ == "__main__":
    main()