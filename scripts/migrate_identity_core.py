#!/usr/bin/env python3
"""Migration tool: migrate legacy identity.json → identity_core.json (versioned schema).

Usage:
    python scripts/migrate_identity_core.py --dry-run        # Phase 1: verify migration
    python scripts/migrate_identity_core.py --execute       # REAL MIGRATION

The script is idempotent: re-running on already-migrated data skips entries.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path
from datetime import datetime, timezone

# Project root = parents[1] from scripts/ directory
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
IDENTITY_JSON = _PROJECT_ROOT / "data" / "archive" / "identity.json"
IDENTITY_CORE_JSON = _PROJECT_ROOT / "data" / "archive" / "identity_core.json"


def _now_iso():
    """Return current UTC datetime in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def _migrate_legacy_identity(legacy: dict) -> dict:
    """Migrate a legacy identity.json dict to the new versioned schema v1.

    Maps known legacy fields to the new IdentityCorePlugin schema.
    Missing fields get sensible defaults.
    """
    identity = {
        "version": 1,
        "name": legacy.get("name", "DECA"),
        "origin": legacy.get("origin", {
            "date": datetime.now(timezone.utc).isoformat(),
            "description": "Migrated from legacy identity.json",
        }),
        "purpose": legacy.get("purpose", ""),
        "mission": legacy.get("mission", ""),
        "values": legacy.get("values", []),
        "principles": legacy.get("principles", []),
        "rules": legacy.get("rules", []),
        "limits": legacy.get("limits", {}),
        "deca_relation": legacy.get("deca_relation", {}),
        "creator_relation": legacy.get("creator_relation", {}),
        "audit_log": [
            {
                "version": 1,
                "date": _now_iso(),
                "changes": "Migrated from legacy identity.json",
                "approved_by": "system",
            }
        ],
    }
    return identity


def main():
    parser = argparse.ArgumentParser(
        description="DECIA Identity Core Migration Tool"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Dry run mode (default). No files written. Report only.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        default=False,
        help="REAL MIGRATION: write identity_core.json and optionally backup identity.json.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_false",
        dest="backup",
        help="Skip backup of identity.json before migration.",
    )

    args = parser.parse_args()

    # ── Gate: --execute requires checking existing state ──────────────
    if args.execute:
        print("=== DECIA Identity Core Migration (real) ===")
        # Check if identity_core.json already exists
        if IDENTITY_CORE_JSON.exists():
            print(f"identity_core.json already exists at {IDENTITY_CORE_JSON}")
            print("Skipping — already migrated. Use --dry-run to re-verify.")
            return

        # Check if identity.json exists (the source)
        if not IDENTITY_JSON.exists():
            print(f"ERROR: legacy identity.json not found at {IDENTITY_JSON}")
            print("Nothing to migrate. Create identity_core.json manually or")
            print("ensure the legacy file exists first.")
            return

        # Create backup of identity.json if requested
        if args.backup:
            backup_path = _PROJECT_ROOT / "data" / "archive" / \
                f"identity.pre-migration.backup.{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
            shutil.copy2(str(IDENTITY_JSON), str(backup_path))
            print(f"Backup created: {backup_path}")

        # Read legacy identity.json
        with open(IDENTITY_JSON, "r", encoding="utf-8") as f:
            legacy = json.load(f)

        # Migrate to new schema
        identity = _migrate_legacy_identity(legacy)

        # Write identity_core.json
        IDENTITY_CORE_JSON.parent.mkdir(parents=True, exist_ok=True)
        with open(IDENTITY_CORE_JSON, "w", encoding="utf-8") as f:
            json.dump(identity, f, ensure_ascii=False, indent=2)

        print(f"Migrated identity.json → identity_core.json (v1)")
        print(f"New file: {IDENTITY_CORE_JSON}")
        return

    # ── Dry-run mode (default) ───────────────────────────────────────
    print("=== DECIA Identity Core Migration (dry-run) ===")

    # Check if identity.json exists
    if not IDENTITY_JSON.exists():
        print(f"ERROR: legacy identity.json not found at {IDENTITY_JSON}")
        print("No migration possible. Create identity.json first or use --execute")
        sys.exit(1)

    # Check if identity_core.json already exists
    if IDENTITY_CORE_JSON.exists():
        print(f"identity_core.json already exists at {IDENTITY_CORE_JSON}")
        print("Already migrated. Nothing to do in dry-run mode.")
        return

    # Read legacy identity.json
    with open(IDENTITY_JSON, "r", encoding="utf-8") as f:
        legacy = json.load(f)

    # Migrate
    identity = _migrate_legacy_identity(legacy)

    # Report what would be written
    print(f"Would create: {IDENTITY_CORE_JSON}")
    print(f"Version: {identity['version']}")
    print(f"name: {identity['name']}")
    print(f"origin: {identity['origin']}")
    print(f"values: {identity['values']}")
    print(f"principles: {identity['principles']}")
    print(f"rules: {identity['rules']}")
    print(f"limits: {identity['limits']}")
    print(f"deca_relation: {identity['deca_relation']}")
    print(f"creator_relation: {identity['creator_relation']}")
    print(f"audit_log entries: {len(identity['audit_log'])}")
    print()
    print("Dry-run complete. No files were written.")
    print("Run --execute to perform the real migration.")


if __name__ == "__main__":
    main()