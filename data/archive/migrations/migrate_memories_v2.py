#!/usr/bin/env python3
"""One-shot migration: read memories.json and enrich each entry with v2 schema fields.

Idempotent: skips entries already marked source="migration".
Backup: creates memories.pre-migration.backup.json before modifying.
Dry-run: --dry-run flag returns report without writing any files.

Usage:
    python data/archive/migrations/migrate_memories_v2.py        # perform migration
    python data/archive/migrations/migrate_memories_v2.py --dry-run  # preview only
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Project root is three levels up from this file: .../app/services/plugins/ → app/ → project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ARCHIVE_PATH = PROJECT_ROOT / "data" / "archive"
MEMORIES_PATH = ARCHIVE_PATH / "memories.json"
BACKUP_PATH = ARCHIVE_PATH / "memories.pre-migration.backup.json"


def migrate_memories(dry_run: bool = False) -> dict:
    """Run the migration of memories.json to v2 schema.

    Args:
        dry_run: If True, only report what would be changed without writing files.

    Returns:
        MigrationReport dict with {total, migrated, errors, backup_path, checksum}.
    """
    # Read current memories
    try:
        with open(MEMORIES_PATH, "r", encoding="utf-8") as f:
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

    # Backup only if not already backed up
    backup_created = False
    if not BACKUP_PATH.exists():
        backup_created = True
        if not dry_run:
            shutil.copy2(MEMORIES_PATH, BACKUP_PATH)

    # In dry-run mode, don't actually copy backup, just note it
    if dry_run:
        backup_created = False  # we won't actually create it in dry-run

    for idx, memory in enumerate(memories):
        try:
            # Skip already-migrated entries
            if memory.get("source") == "migration":
                continue

            # Map legacy "text" to "content" if present
            if "text" in memory and "content" not in memory:
                memory["content"] = memory.pop("text")

            # Ensure type and confidence
            if "type" not in memory:
                memory["type"] = "MEMORY"
            if "confidence" not in memory:
                memory["confidence"] = 0.7

            # Set default v2 fields
            if "relations" not in memory:
                memory["relations"] = []
            if "encryption_flag" not in memory:
                # Apply per-type encryption policy
                mandatory = {"INTERPRETATION", "LESSON"}
                optional = {"MEMORY", "DECISION", "PREDICTION", "GOAL"}
                if memory["type"] in mandatory:
                    memory["encryption_flag"] = "mandatory"
                elif memory["type"] in optional:
                    memory["encryption_flag"] = "optional"
                else:
                    # FACT and UNKNOWN: no encryption
                    memory["encryption_flag"] = "none"
            if "metadata" not in memory:
                memory["metadata"] = {}
            if "version" not in memory:
                memory["version"] = 1
            now = datetime.now().isoformat()
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
        "backup_path": str(BACKUP_PATH) if backup_created else None,
        "checksum": checksum,
    }

    # Write enriched data back to file (not in dry-run mode)
    if not dry_run:
        try:
            with open(MEMORIES_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            report["write_error"] = str(e)

    return report


def main():
    parser = argparse.ArgumentParser(description="Migrate memories.json to v2 schema")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Preview migration without writing files",
    )
    args = parser.parse_args()

    report = migrate_memories(dry_run=args.dry_run)

    print(f"Migration Report:")
    print(f"  Total entries: {report['total']}")
    print(f"  Migrated: {report['migrated']}")
    if report.get("errors"):
        print(f"  Errors: {len(report['errors'])}")
        for e in report["errors"][:5]:
            print(f"    - {e}")
    else:
        print("  Errors: none")
    print(f"  Backup: {report.get('backup_path')}")
    print(f"  Checksum: {report.get('checksum')[:16] if report.get('checksum') else 'None'}...")

    if report.get("write_error"):
        print(f"\nError writing memories.json: {report['write_error']}")
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()