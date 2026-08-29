# Test for Task 1.1: Plugin package infrastructure
# This test verifies the plugins package directory structure

from pathlib import Path

# Check if the plugins package directory exists
plugins_dir = Path("/mnt/c/Users/idelv/Desktop/DECIA_V3/app/brain/plugins")

def test_plugins_directory_exists():
    # RED state: The directory must exist for the task to be complete
    assert plugins_dir.exists(), "Task 1.1: Plugins directory must exist"
    print("Task 1.1: GREEN - directory exists")