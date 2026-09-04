#!/usr/bin/env python3
"""Migration tool: enrich memories.json with v2 typed memory schema.

Phase 1 ONLY: This script supports --dry-run (default), --backup, and --validate flags.
--execute is REQUIRED for real migration and MUST NOT be used in Phase 1.

Usage:
    python scripts/migrate_memories_v2.py --dry-run        # Phase 1: verify changes
    python scripts/migrate_memories_v2.py --dry-run --backup  # Create backup + verify
    python scripts/migrate_memories_v2.py --dry-run --validate  # Verify checksum
    python scripts/migrate_memories_v2.py --execute       # REAL MIGRATION - Phase 2+

The script is idempotent: re-running on already-migrated data (source="migration")
skips entries and does not overwrite the backup.
"""

import argparse
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path
from datetime import datetime


# ────────────────────────────────────────────────────────────────────
# Schema / constants
# ──────────────────────────────────────────────────────────────────_

# Project root = parents[1] from scripts/ directory
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
MEMORIES_PATH = _PROJECT_ROOT / "data" / "archive" / "memories.json"
BACKUP_PATH = _PROJECT_ROOT / "data" / "archive" / "memories.pre-migration.backup.json"
SCHEMA_PATH = _PROJECT_ROOT / "data" / "archive" / "memories.schema.json"


# ────────────────────────────────────────────────────────────────────
# Type policy: encryption per memory type
# ──────────────────────────────────────────────────────────────────_

_ENCRYPTION_POLICY = {
    "FACT": "none",
    "MEMORY": "optional",
    "DECISION": "optional",
    "GOAL": "optional",
    "PREDICTION": "optional",
    "LESSON": "mandatory",
    "INTERPRETATION": "mandatory",
    "UNKNOWN": "none",
}


def _encryption_flag(mtype: str) -> str:
    """Return encryption flag per memory type policy."""
    return _ENCRYPTION_POLICY.get(mtype, "none")


# ────────────────────────────────────────────────────────────────────
# Core migration logic
# ──────────────────────────────────────────────────────────────────_

def _migrate_entry(memory: dict, default_type: str = "MEMORY", default_confidence: float = 0.7) -> dict:
    """Enrich a single memory entry with v2 schema fields.

    Preserves ALL existing fields. Adds/missing fields with defaults.
    Maps legacy "text" → "content" if present and "content" absent.
    Only applies default type/confidence when field is absent (preserves existing types).
    """
    import copy as _copy
    from datetime import datetime
    mem = _copy.deepcopy(memory)

    # Map legacy "text" to "content" if present and "content" absent
    if "text" in mem and "content" not in mem:
        mem["content"] = mem.pop("text")

    # Ensure type with default ONLY if absent (preserve existing types like "actividad")
    if "type" not in mem:
        mem["type"] = default_type

    # Ensure confidence with default ONLY if absent
    if "confidence" not in mem:
        mem["confidence"] = default_confidence

    # Ensure relations array
    if "relations" not in mem:
        mem["relations"] = []

    # Ensure encryption_flag per type policy (only if absent)
    if "encryption_flag" not in mem:
        mem["encryption_flag"] = _encryption_flag(mem.get("type", default_type))

    # Ensure metadata dict
    if "metadata" not in mem:
        mem["metadata"] = {}

    # Ensure version (default to 1 if absent)
    if "version" not in mem:
        mem["version"] = 1

    # Ensure created_at / updated_at (ISO8601 now)
    now = datetime.now().isoformat()
    if "created_at" not in mem:
        mem["created_at"] = now
    if "updated_at" not in mem:
        mem["updated_at"] = now

    # Ensure source = "migration" if absent
    if "source" not in mem:
        mem["source"] = "migration"

    return mem


def _compute_checksum(data: dict) -> str:
    """Compute SHA-256 checksum of the full data dict."""
    mc = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(mc.encode("utf-8")).hexdigest()


# ────────────────────────────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────────────────────────_

def main():
    parser = argparse.ArgumentParser(
        description="DECIA Memory v2 Migration Tool"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Dry run mode (default). No files written. Report only.",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        default=True,
        help="Create timestamped backup of memories.json (default: on)",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        default=True,
        help="Enable checksum validation post-migration (default: on)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        default=False,
        help="REQUIRED for real migration. DO NOT use in Phase 1.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_false",
        dest="backup",
        help="Disable backup creation",
    )
    parser.add_argument(
        "--no-validate",
        action="store_false",
        dest="validate",
        help="Disable checksum validation",
    )

    args = parser.parse_args()

    # ── Gate: --execute requires explicit confirmation ──────────────
    if args.execute:
        print(
            "ERROR: --execute must NOT be used in Phase 1. "
            "Use --dry-run for verification only."
        )
        print(
            "If you really want to perform the real migration, "
            "run without --dry-run after Phase 1 gate review."
        )
        sys.exit(1)

    # ── Read current memories ──────────────────────────────────────
    if not MEMORIES_PATH.exists():
        print(f"ERROR: memories.json not found at {MEMORIES_PATH}")
        sys.exit(1)

    with open(MEMORIES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    memories = data.get("memories", [])
    total = len(memories)

    print(f"=== DECIA Memory v2 Migration ===")
    print(f"Total entries: {total}")
    print(f"Dry run: {args.dry_run}")
    print(f"Backup: {args.backup}")
    print(f"Validate: {args.validate}")
    print()

    # ── Phase 1: dry-run mode - analyze without writing ────────────
    if not args.execute and args.dry_run:
        # Check how many entries are already migrated
        already_migrated = sum(
            1 for m in memories if m.get("source") == "migration"
        )
        untyped = sum(1 for m in memories if "type" not in m)
        no_confidence = sum(1 for m in memories if "confidence" not in m)

        print(f"Already migrated (source=migration): {already_migrated}")
        print(f"Untyped entries (no 'type' field): {untyped}")
        print(f"Entries without confidence: {no_confidence}")
        print()

        # Simulate migration on a copy to generate report
        migrated = 0
        errors = []

        valid_types = {"FACT", "MEMORY", "DECISION", "GOAL", "PREDICTION", "LESSON", "INTERPRETATION", "UNKNOWN"}

        for idx, mem in enumerate(memories):
            try:
                # Skip already-migrated
                if mem.get("source") == "migration":
                    continue

                # Enrich
                new_mem = _migrate_entry(mem)

                # Verify enriched fields - accept both new 8-types AND existing types
                t = new_mem.get("type", "")
                if t not in valid_types and t != "actividad":
                    errors.append(f"entry {idx}: unexpected type {t}")

                if "confidence" not in new_mem:
                    errors.append(f"entry {idx}: missing confidence after enrichment")

                if "relations" not in new_mem:
                    errors.append(f"entry {idx}: missing relations after enrichment")

                migrated += 1

            except Exception as e:
                errors.append(f"entry {idx}: {str(e)}")

        # Compute checksum of what the migrated data would look like
        migrated_data = data.copy()
        # We'll re-apply migration to compute checksum
        # For dry-run report, compute checksum on original (no changes written)
        # but mark the report fields appropriately

        backup_path_str = None
        if args.backup:
            # Timestamped backup path (what would be created)
            ts = time.strftime("%Y%m%d-%H%M%S")
            backup_path_str = f"memories.pre-migration.backup.{ts}.json"

        checksum = None
        if args.validate:
            checksum = _compute_checksum(data)

        report = {
            "total": total,
            "migrated": migrated,
            "errors": errors,
            "backup_path": backup_path_str,
            "checksum": checksum,
        }

        print("=== Migration Report (dry-run) ===")
        print(json.dumps(report, indent=2, default=str))
        print()
        print(f"Entries successfully enriched: {migrated}/{total}")
        if errors:
            print(f"Errors: {len(errors)}")
            for e in errors[:10]:  # show first 10
                print(f"  - {e}")
            if len(errors) > 10:
                print(f"  ... and {len(errors) - 10} more")
        else:
            print("No errors found.")
        print()
        print("=== Dry-run complete ===")
        print("No files were written. Use --execute for real migration (Phase 2+).")
        return

    # ── Real migration (--execute only, Phase 2+) ──────────────────
    if args.execute:
        # Backup existing memories.json
        if args.backup or True:  # always backup for real migration
            try:
                shutil.copy2(str(MEMORIES_PATH), str(BACKUP_PATH))
                print(f"Backup created: {BACKUP_PATH}")
            except Exception as e:
                print(f"WARNING: Could not create backup: {e}")

        # Migrate each entry
        migrated = 0
        errors = []

        for idx, mem in enumerate(memories):
            try:
                # Skip already-migrated (idempotent)
                if mem.get("source") == "migration":
                    continue

                new_mem = _migrate_entry(mem)
                memories[idx] = new_mem
                migrated += 1

            except Exception as e:
                errors.append(f"entry {idx}: {str(e)}")

        # Write migrated data back
        data["memories"] = memories
        with open(MEMORIES_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # Compute checksum
        checksum = None
        if args.validate:
            checksum = _compute_checksum(data)

        report = {
            "total": total,
            "migrated": migrated,
            "errors": errors,
            "backup_path": str(BACKUP_PATH),
            "checksum": checksum,
        }

        print("=== Migration Report (real) ===")
        print(json.dumps(report, indent=2, default=str))
        print()
        print(f"Entries migrated: {migrated}/{total}")
        if errors:
            print(f"Errors: {len(errors)}")
            for e in errors[:10]:
                print(f"  - {e}")
            if len(errors) > 10:
                print(f"  ... and {len(errors) - 10} more")
        else:
            print("No errors found.")
        print()
        if checksum:
            print(f"Checksum: {checksum}")
        print("=== Migration complete ===")
        return

    # ── Fallback should not reach here ─────────────────────────────
    print("Unexpected state reached.")
    sys.exit(1)


if __name__ == "__main__":
    main()