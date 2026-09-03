#!/usr/bin/env python3
"""Batch re-classification CLI with preview + apply.

Pattern-based bulk update for known categories (facts, decisions, goals).
--preview shows affected memories without persisting.
--apply commits changes.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Project root is three levels up from this file
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ARCHIVE_PATH = PROJECT_ROOT / "data" / "archive"
MEMORIES_PATH = ARCHIVE_PATH / "memories.json"


# Classification patterns: regex patterns that match memory content to categories
CLASSIFICATION_PATTERNS = {
    "FACT": [
        r"\b(?:el|la|un|una)\s+(?:hecho|hecho|constatado|comprobado|verdad|realidad)\b",
        r"\b(?:es|son)\s+(?:un\s+)?hecho\b",
        r"\b(?:sab|se|conozco|conozco)\s+(?:que|\s+\w+)\b",
    ],
    "DECISION": [
        r"\b(?:decisi[oó]n|decidi|vote|votamos|elegimos|optamos)\b",
        r"\b(?:eligi|escog|elegimos|decidimos)\s+(?:que|por)\b",
        r"\b(?:problema|argument|alternativa|decisi[oó]n)\b",
    ],
    "GOAL": [
        r"\b(?:objetivo|meta|prop[oó]sito|propongo|quiero\s+que|metas)\b",
        r"\b(?:busco|quiero|necesito)\s+(?:hacer|lograr|alcanzar)\b",
        r"\b(?:plani|proyecto|viaje|curso|certificado)\b",
    ],
}


def classify_memory(content: str) -> str | None:
    """Classify a memory's content into a type based on patterns.

    Returns one of: "FACT", "DECISION", "GOAL", or None if no pattern matches.
    """
    content_lower = content.lower() if content else ""
    for mtype, patterns in CLASSIFICATION_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                return mtype
    return None


def reclassify_memories(dry_run: bool = True) -> dict:
    """Re-classify memories based on content patterns.

    Args:
        dry_run: If True, only report what would be changed without persisting.

    Returns:
        Reclassification report dict.
    """
    # Read current memories
    try:
        with open(MEMORIES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return {
            "total": 0,
            "affected": 0,
            "changes": [],
            "errors": [str(e)],
        }

    memories = data.get("memories", [])
    total = len(memories)
    affected = 0
    changes = []
    errors = []

    for idx, memory in enumerate(memories):
        try:
            content = memory.get("content") or memory.get("text") or ""
            current_type = memory.get("type", "")

            new_type = classify_memory(content)

            # Only re-classify if a pattern matched and the type is changing
            if new_type and new_type != current_type:
                memory["type"] = new_type
                affected += 1
                changes.append(
                    {
                        "index": idx,
                        "id": memory.get("id"),
                        "old_type": current_type,
                        "new_type": new_type,
                        "content_snippet": (content[:80] + "...") if len(content) > 80 else content,
                    }
                )
            elif new_type == current_type:
                # Same type, no change needed
                pass
            else:
                # No pattern matched, keep current type
                pass

        except Exception as e:
            errors.append(f"entry {idx}: {str(e)}")

    if dry_run:
        # Don't persist changes in dry-run mode
        return {
            "total": total,
            "affected": affected,
            "changes": changes,
            "errors": errors,
            "dry_run": True,
        }
    else:
        # Write modified memories.json
        try:
            with open(MEMORIES_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return {
                "total": total,
                "affected": affected,
                "changes": changes,
                "errors": errors,
                "dry_run": False,
            }
        except Exception as e:
            return {
                "total": total,
                "affected": affected,
                "changes": changes,
                "errors": [str(e)],
                "dry_run": False,
            }


def main():
    parser = argparse.ArgumentParser(description="Batch re-classification CLI for memories")
    parser.add_argument(
        "--preview",
        action="store_true",
        default=False,
        help="Preview re-classification without persisting changes",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help="Apply re-classification changes to memories.json",
    )
    args = parser.parse_args()

    if not args.preview and not args.apply:
        parser.error("Either --preview or --apply must be specified")

    dry_run = not args.apply  # --preview is dry-run, --apply is for real

    report = reclassify_memories(dry_run=dry_run)

    print(f"Re-classification Report:")
    print(f"  Total memories: {report['total']}")
    print(f"  Affected (type change): {report['affected']}")
    if report["changes"]:
        print(f"  Changes:")
        for c in report["changes"][:20]:
            print(f"    [{c['index']}] {c['old_type']}' → {c['new_type']} (id: {c['id']})")
            print(f"        snippet: {c['content_snippet']}")
    if report["errors"]:
        print(f"  Errors: {len(report['errors'])}")
        for e in report["errors"][:5]:
            print(f"    - {e}")

    if not dry_run and report["affected"] > 0:
        print(f"\nRe-classification applied to {report['affected']} memories.")


if __name__ == "__main__":
    main()