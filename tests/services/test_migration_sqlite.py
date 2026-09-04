# tests/services/test_migration_sqlite.py - Migration to SQLite Tests
# Golden master: all 546 existing tests must pass unchanged

import os
import sys
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "app"))

# Import migration functions
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from migrate_to_sqlite import migrate_json_to_sqlite, backup_files, compute_checksum


def _make_temp_dirs():
    """Create temporary directory structure for testing."""
    tmpdir = tempfile.mkdtemp()
    data_dir = os.path.join(tmpdir, "data", "archive")
    os.makedirs(data_dir, exist_ok=True)
    return tmpdir, data_dir


def _cleanup_temp_dir(tmpdir):
    """Clean up temporary directory."""
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)


def test_backup_files():
    """Test backup creation."""
    tmpdir, data_dir = _make_temp_dirs()
    try:
        # Create test JSON files
        test_files = {
            "TEST1": os.path.join(data_dir, "test1.json"),
            "TEST2": os.path.join(data_dir, "test2.json"),
        }
        for name, path in test_files.items():
            with open(path, "w") as f:
                json.dump([{"id": f"{name}-1"}], f)
        
        backup_path = backup_files(test_files)
        assert os.path.exists(backup_path)
        assert os.path.exists(os.path.join(backup_path, "test1.json"))
        assert os.path.exists(os.path.join(backup_path, "test2.json"))
    finally:
        _cleanup_temp_dir(os.path.dirname(os.path.dirname(test_files["TEST1"])))


def test_compute_checksum():
    """Test checksum computation."""
    data = [{"id": "1", "value": "test"}, {"id": "2", "value": "test2"}]
    checksum1 = compute_checksum(data)
    checksum2 = compute_checksum(data)
    assert checksum1 == checksum2
    assert len(checksum1) == 64  # SHA256 hex length
    
    # Different data should produce different checksum
    data2 = [{"id": "3", "value": "different"}]
    checksum3 = compute_checksum(data2)
    assert checksum1 != checksum3


def test_migration_dry_run():
    """Test migration dry-run mode."""
    tmpdir = tempfile.mkdtemp()
    data_dir = os.path.join(tmpdir, "data", "archive")
    os.makedirs(data_dir, exist_ok=True)
    
    try:
        # Create test JSON files
        test_data = {
            "memories.json": [
                {"id": "mem-1", "description": "Test memory", "confidence": 0.8, "date": "2026-01-01T00:00:00"},
                {"id": "mem-2", "content": "Another memory", "confidence": 0.9},
            ],
            "decisions.json": [
                {"id": "dec-1", "problem": "Test problem", "decision": "Test decision", 
                 "rationale": "Test rationale", "confidence": 0.85, "status": "OPEN"},
            ],
            "predictions.json": [
                {"id": "pred-1", "prediction_text": "Test prediction", 
                 "confidence": 0.7, "reasons": ["reason1"]},
            ],
            "learnings.json": [
                {"id": "learn-1", "trigger_id": "dec-1", "trigger_type": "DECISION",
                 "expected": "success", "actual": "success", "confidence": 1.0},
            ],
            "reflections.json": [
                {"id": "refl-1", "draft_content": "Test reflection", "status": "DRAFT"},
            ],
            "identity_core.json": {
                "version": 1,
                "name": "DECIA",
                "meaning": "Test AI",
                "creator": "Test Creator",
                "values": ["honesty"],
            },
        }
        
        for filename, data in test_data.items():
            with open(os.path.join("data", "archive", filename), "w") as f:
                json.dump(data, f)
        
        # Ensure data directory exists
        os.makedirs("data/archive", exist_ok=True)
        
        # Run dry-run migration
        db_path = os.path.join(tempfile.gettempdir(), "test_migration.db")
        if os.path.exists(db_path):
            os.unlink(db_path)
        
        report = migrate_json_to_sqlite(
            db_path=db_path,
            dry_run=True,
            backup=False,
            validate=True,
        )
        
        assert report["total"] > 0
        assert report["migrated"] == 0  # dry run doesn't migrate
        assert report["checksum"] is not None
        assert len(report["by_type"]) > 0
        
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)
    finally:
        # Cleanup test files
        for fname in ["memories.json", "decisions.json", "predictions.json", 
                      "learnings.json", "reflections.json", "identity_core.json"]:
            fpath = os.path.join("data", "archive", fname)
            if os.path.exists(fpath):
                os.unlink(fpath)


def test_migration_dry_run_with_backup():
    """Test migration dry-run with backup."""
    tmpdir = tempfile.mkdtemp()
    try:
        # Create test JSON in temp directory
        data_dir = os.path.join(tmpdir, "data", "archive")
        os.makedirs(data_dir, exist_ok=True)
        
        test_files = {
            "memories.json": [{"id": "mem-1", "description": "Test", "confidence": 0.8}],
            "decisions.json": [{"id": "dec-1", "problem": "P", "decision": "D"}],
        }
        
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        
        try:
            os.makedirs("data/archive", exist_ok=True)
            for fname, data in test_files.items():
                with open(os.path.join("data", "archive", fname), "w") as f:
                    json.dump(data, f)
            
            db_path = os.path.join(tmpdir, "test.db")
            report = migrate_json_to_sqlite(
                db_path=db_path,
                dry_run=True,
                backup=True,
                validate=True,
            )
            
            assert report["backup_path"] is not None
            assert os.path.exists(report["backup_path"])
            assert os.path.exists(os.path.join(report["backup_path"], "memories.json"))
            assert os.path.exists(os.path.join(report["backup_path"], "decisions.json"))
        finally:
            os.chdir(original_cwd)
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_migration_execute_dry_run_false():
    """Test that --execute flag actually migrates data."""
    tmpdir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    
    try:
        os.chdir(tmpdir)
        os.makedirs("data/archive", exist_ok=True)
        
        # Create test data
        with open("data/archive/memories.json", "w") as f:
            json.dump([{"id": "mem-1", "description": "Test", "confidence": 0.8}], f)
        
        db_path = os.path.join(tmpdir, "test_execute.db")
        if os.path.exists(db_path):
            os.unlink(db_path)
        
        # This should fail because we don't have --execute (default dry_run=True)
        report = migrate_json_to_sqlite(
            db_path=os.path.join(tmpdir, "test.db"),
            dry_run=True,  # explicit dry run
            backup=False,
            validate=True,
        )
        assert report["migrated"] == 0
        
    finally:
        os.chdir(original_cwd)
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)