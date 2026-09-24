from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data/automation_regression.json"


def digest(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def temp_workspace(tmp):
    path = Path(tmp) / "automation_regression.json"
    shutil.copyfile(CANONICAL, path)
    return path


def test_empty_automation_workspace_is_valid():
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        path = temp_workspace(tmp)
        rel = path.relative_to(ROOT)

        p = subprocess.run([
            sys.executable,
            "tools/publish_automation_status.py",
            str(rel),
            "--dry-run",
        ], cwd=ROOT, text=True, capture_output=True)

        assert p.returncode == 0
        assert "validation passed" in (p.stdout + p.stderr).lower()


def test_automation_recorder_rejects_unknown_test():
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        path = temp_workspace(tmp)
        before = digest(path)
        rel = path.relative_to(ROOT)

        p = subprocess.run([
            sys.executable,
            "tools/record_automation_result.py",
            str(rel),
            "--automation-test-id",
            "NON-EXISTENT-AUTOMATION-TEST",
            "--environment",
            "UAT",
            "--status",
            "PASSED",
        ], cwd=ROOT, text=True, capture_output=True)

        assert p.returncode != 0
        assert digest(path) == before


def test_automation_publish_dry_run_is_non_destructive():
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        path = temp_workspace(tmp)
        rel = path.relative_to(ROOT)

        canonical_before = digest(CANONICAL)
        workspace_before = digest(path)

        subprocess.run([
            sys.executable,
            "tools/publish_automation_status.py",
            str(rel),
            "--dry-run",
        ], cwd=ROOT, check=True)

        assert digest(CANONICAL) == canonical_before
        assert digest(path) == workspace_before
