"""
Sprint 8 Card 4 (#45): the CI head-count step must evaluate, not just display.
"""

import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "assert_single_head.sh"


def _run(tmp_path, text):
    captured = tmp_path / "heads.txt"
    captured.write_text(text)
    return subprocess.run(["bash", str(SCRIPT), str(captured)], capture_output=True, text=True)


def test_single_head_passes(tmp_path):
    result = _run(tmp_path, "cabafa45acd1 (head)\n")
    assert result.returncode == 0
    assert "exactly one" in result.stdout


def test_two_heads_fail(tmp_path):
    result = _run(tmp_path, "cabafa45acd1 (head)\n0f1e2d3c4b5a (head)\n")
    assert result.returncode == 1
    assert "found 2" in result.stderr


def test_no_heads_fail(tmp_path):
    result = _run(tmp_path, "")
    assert result.returncode == 1
    assert "found 0" in result.stderr


def test_script_is_executable():
    assert SCRIPT.stat().st_mode & 0o111
