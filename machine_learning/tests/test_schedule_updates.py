"""
Sprint 8 Card 2 (#47): scheduler skips are recorded and surfaced.

Runs the real bash script through subprocess with every external dependency
injected via environment variables: a fake readiness check, a stub update
command, a stub notifier, and a temp log directory. No PostgreSQL, no launchd.
"""

import os
import stat
import subprocess
from datetime import date, timedelta
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "schedule_updates.sh"
TRUE = "/usr/bin/true" if os.path.exists("/usr/bin/true") else "/bin/true"
FALSE = "/usr/bin/false" if os.path.exists("/usr/bin/false") else "/bin/false"


@pytest.fixture
def env(tmp_path):
    """Base environment: DB down, update succeeds, notifier records its messages."""
    log_dir = tmp_path / "logs"
    notified = tmp_path / "notified.txt"
    notifier = tmp_path / "notify.sh"
    notifier.write_text(f'#!/bin/bash\necho "$1" >> "{notified}"\n')
    notifier.chmod(notifier.stat().st_mode | stat.S_IEXEC)

    return {
        "log_dir": log_dir,
        "marker": log_dir / "mlb_update_skips.log",
        "notified": notified,
        "vars": {
            **os.environ,
            "BETBOT_LOG_DIR": str(log_dir),
            "BETBOT_PG_ISREADY": FALSE,
            "BETBOT_UPDATE_CMD": "true",
            "BETBOT_NOTIFY_CMD": str(notifier),
        },
    }


def run(env, **overrides):
    variables = {**env["vars"], **overrides}
    return subprocess.run(["bash", str(SCRIPT)], env=variables, capture_output=True, text=True, timeout=30)


def _marker_lines(env):
    return [line for line in env["marker"].read_text().splitlines() if line.strip()]


def _notifications(env):
    return env["notified"].read_text().splitlines() if env["notified"].exists() else []


class TestSkip:

    def test_skip_records_one_line_and_exits_zero(self, env):
        result = run(env)
        assert result.returncode == 0
        assert "SKIP:" in result.stdout
        assert len(_marker_lines(env)) == 1

    def test_two_skips_record_two_attempts(self, env):
        run(env)
        result = run(env)
        assert result.returncode == 0
        assert len(_marker_lines(env)) == 2
        assert "2 skipped attempt(s)" in result.stdout

    def test_skip_sends_notification(self, env):
        run(env)
        messages = _notifications(env)
        assert len(messages) == 1
        assert "SKIPPED" in messages[0]

    def test_missing_notifier_still_records_skip(self, env):
        result = run(env, BETBOT_NOTIFY_CMD="/nonexistent/notifier")
        assert result.returncode == 0
        assert len(_marker_lines(env)) == 1
        assert "notifier" in result.stdout and "ignored" in result.stdout

    def test_failing_notifier_still_records_skip(self, env):
        result = run(env, BETBOT_NOTIFY_CMD=FALSE)
        assert result.returncode == 0
        assert len(_marker_lines(env)) == 1


class TestResume:

    def test_success_after_skips_logs_resumed_and_clears_marker(self, env):
        run(env)
        run(env)
        result = run(env, BETBOT_PG_ISREADY=TRUE)

        assert result.returncode == 0
        assert "RESUMED: 2 skipped attempt(s) across 1 day(s)" in result.stdout
        assert not env["marker"].exists()
        assert any("RESUMED" in m for m in _notifications(env))

    def test_distinct_days_are_counted_separately(self, env):
        env["log_dir"].mkdir(parents=True)
        today = date.today()
        env["marker"].write_text(
            f"{today - timedelta(days=2)} 06:00:00\n"
            f"{today - timedelta(days=1)} 06:00:00\n"
            f"{today - timedelta(days=1)} 09:00:00\n"
        )
        result = run(env, BETBOT_PG_ISREADY=TRUE)
        assert "RESUMED: 3 skipped attempt(s) across 2 day(s)" in result.stdout
        assert f"first skip {today - timedelta(days=2)}" in result.stdout

    def test_failed_update_preserves_marker(self, env):
        run(env)
        result = run(env, BETBOT_PG_ISREADY=TRUE, BETBOT_UPDATE_CMD="false")

        assert result.returncode == 1
        assert "ERROR" in result.stdout
        assert "RESUMED" not in result.stdout
        assert len(_marker_lines(env)) == 1

    def test_gap_over_thirty_days_prints_backfill_command(self, env):
        env["log_dir"].mkdir(parents=True)
        first = date.today() - timedelta(days=31)
        env["marker"].write_text(f"{first} 06:00:00\n")
        result = run(env, BETBOT_PG_ISREADY=TRUE)

        assert "RESUMED" in result.stdout
        assert "WARN" in result.stdout
        assert f"--start-date {first}" in result.stdout

    def test_gap_within_thirty_days_has_no_backfill_warning(self, env):
        env["log_dir"].mkdir(parents=True)
        env["marker"].write_text(f"{date.today() - timedelta(days=30)} 06:00:00\n")
        result = run(env, BETBOT_PG_ISREADY=TRUE)
        assert "RESUMED" in result.stdout
        assert "WARN" not in result.stdout

    def test_success_without_prior_skips_is_quiet(self, env):
        result = run(env, BETBOT_PG_ISREADY=TRUE)
        assert result.returncode == 0
        assert "RESUMED" not in result.stdout
        assert not env["marker"].exists()
        assert _notifications(env) == []


def test_script_is_executable():
    assert SCRIPT.stat().st_mode & stat.S_IEXEC
