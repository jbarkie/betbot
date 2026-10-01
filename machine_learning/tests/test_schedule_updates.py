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
            "LC_ALL": "C",
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

    def test_gap_over_thirty_days_runs_recovery(self, env):
        env["log_dir"].mkdir(parents=True)
        first = date.today() - timedelta(days=31)
        env["marker"].write_text(f"{first} 06:00:00\n")
        result = run(env, BETBOT_PG_ISREADY=TRUE, BETBOT_UPDATE_CMD="printf '%s\\n'")

        assert "RESUMED" in result.stdout
        assert "RECOVERY:" in result.stdout
        assert (env["log_dir"] / "mlb_data_update.log").read_text().splitlines() == [
            '--recover-from', str(first - timedelta(days=1))
        ]

    def test_gap_within_thirty_days_has_no_backfill_warning(self, env):
        env["log_dir"].mkdir(parents=True)
        env["marker"].write_text(f"{date.today() - timedelta(days=29)} 06:00:00\n")
        result = run(env, BETBOT_PG_ISREADY=TRUE)
        assert "RESUMED" in result.stdout
        assert "WARN" not in result.stdout
        assert "RECOVERY:" not in result.stdout

    def test_thirty_day_skip_recovers_previous_days_games(self, env):
        env["log_dir"].mkdir(parents=True)
        env["marker"].write_text(f"{date.today() - timedelta(days=30)} 06:00:00\n")
        result = run(env, BETBOT_PG_ISREADY=TRUE)
        assert "RECOVERY:" in result.stdout

    def test_recovery_failure_preserves_exact_marker_for_retry(self, env):
        env["log_dir"].mkdir(parents=True)
        marker = f"{date.today() - timedelta(days=45)} 06:00:00\n"
        env["marker"].write_text(marker)
        failed = run(env, BETBOT_PG_ISREADY=TRUE, BETBOT_UPDATE_CMD="false")
        assert failed.returncode == 1
        assert "RESUMED" not in failed.stdout
        assert env["marker"].read_text() == marker
        retried = run(env, BETBOT_PG_ISREADY=TRUE)
        assert "RECOVERY:" in retried.stdout
        assert "RESUMED" in retried.stdout
        assert not env["marker"].exists()

    def test_invalid_marker_stops_before_update(self, env):
        env["log_dir"].mkdir(parents=True)
        env["marker"].write_text('invalid timestamp\n')
        result = run(env, BETBOT_PG_ISREADY=TRUE)
        assert result.returncode == 1
        assert "Starting MLB data update" not in result.stdout
        assert env["marker"].read_text() == 'invalid timestamp\n'


    def test_success_without_prior_skips_is_quiet(self, env):
        result = run(env, BETBOT_PG_ISREADY=TRUE)
        assert result.returncode == 0
        assert "RESUMED" not in result.stdout
        assert not env["marker"].exists()
        assert _notifications(env) == []


def test_script_is_executable():
    assert SCRIPT.stat().st_mode & stat.S_IEXEC


class TestPgIsreadyDiscovery:
    """
    Sprint 8 review: discovery must work under launchd's minimal PATH, on both
    Apple Silicon (/opt/homebrew) and Intel or Rosetta (/usr/local) layouts.

    Each test builds a fake Homebrew layout in a temp dir and runs the script
    with PATH=/usr/bin:/bin, so no real brew can leak in. The fake pg_isready
    exits 0, which lets the run proceed to the stub update.
    """

    MINIMAL_PATH = "/usr/bin:/bin"

    def _fake_pg_isready(self, root):
        binary = root / "opt" / "postgresql@14" / "bin" / "pg_isready"
        binary.parent.mkdir(parents=True)
        binary.write_text("#!/bin/bash\nexit 0\n")
        binary.chmod(0o755)
        return binary

    def _fake_brew(self, path, prefix):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            '#!/bin/bash\n'
            f'[ "$1" = "--prefix" ] && [ "$2" = "postgresql@14" ] && echo "{prefix}" && exit 0\n'
            'exit 1\n'
        )
        path.chmod(0o755)
        return path

    def _run(self, env, tmp_path, brews, roots):
        variables = {
            "PATH": self.MINIMAL_PATH,
            "HOME": str(tmp_path),
            "BETBOT_LOG_DIR": str(env["log_dir"]),
            "BETBOT_UPDATE_CMD": "true",
            "BETBOT_NOTIFY_CMD": env["vars"]["BETBOT_NOTIFY_CMD"],
            "BETBOT_BREW_CANDIDATES": ":".join(str(b) for b in brews),
            "BETBOT_HOMEBREW_ROOTS": ":".join(str(r) for r in roots),
        }
        return subprocess.run(["/bin/bash", str(SCRIPT)], env=variables,
                               capture_output=True, text=True, timeout=30)

    def test_apple_silicon_brew_found_without_path(self, env, tmp_path):
        arm_root, intel_root = tmp_path / "opt-homebrew", tmp_path / "usr-local"
        arm_pg = self._fake_pg_isready(arm_root)
        arm_brew = self._fake_brew(arm_root / "bin" / "brew", arm_root / "opt" / "postgresql@14")
        result = self._run(env, tmp_path, [arm_brew, intel_root / "bin" / "brew"], [])

        assert f"Using pg_isready at {arm_pg}" in result.stdout
        assert "PostgreSQL is ready" in result.stdout
        assert result.returncode == 0

    def test_intel_brew_found_when_apple_silicon_absent(self, env, tmp_path):
        arm_root, intel_root = tmp_path / "opt-homebrew", tmp_path / "usr-local"
        intel_pg = self._fake_pg_isready(intel_root)
        intel_brew = self._fake_brew(intel_root / "bin" / "brew", intel_root / "opt" / "postgresql@14")
        result = self._run(env, tmp_path, [arm_root / "bin" / "brew", intel_brew], [])

        assert f"Using pg_isready at {intel_pg}" in result.stdout
        assert "PostgreSQL is ready" in result.stdout

    def test_root_scan_used_when_no_brew_binary_works(self, env, tmp_path):
        arm_root = tmp_path / "opt-homebrew"
        arm_pg = self._fake_pg_isready(arm_root)
        result = self._run(env, tmp_path, [tmp_path / "missing" / "brew"], [tmp_path / "usr-local", arm_root])

        assert f"Using pg_isready at {arm_pg}" in result.stdout
        assert "PostgreSQL is ready" in result.stdout

    def test_brew_prefix_without_postgres_falls_through(self, env, tmp_path):
        """A brew that answers but has no pg_isready at that prefix is skipped."""
        arm_root, intel_root = tmp_path / "opt-homebrew", tmp_path / "usr-local"
        arm_brew = self._fake_brew(arm_root / "bin" / "brew", arm_root / "opt" / "postgresql@14")
        intel_pg = self._fake_pg_isready(intel_root)
        result = self._run(env, tmp_path, [arm_brew], [intel_root])

        assert f"Using pg_isready at {intel_pg}" in result.stdout

    def test_nothing_found_falls_back_to_legacy_path_and_warns_if_missing(self, env, tmp_path):
        result = self._run(env, tmp_path, [tmp_path / "missing" / "brew"], [tmp_path / "nowhere"])

        assert "Using pg_isready at /usr/local/opt/postgresql@14/bin/pg_isready" in result.stdout
        if not os.access("/usr/local/opt/postgresql@14/bin/pg_isready", os.X_OK):
            assert "is not executable" in result.stdout
            assert "SKIP:" in result.stdout

    def test_real_defaults_under_minimal_path(self, tmp_path):
        """No overrides at all: on a dev machine with Homebrew PostgreSQL, discovery succeeds."""
        found = [p for p in ("/opt/homebrew/opt/postgresql@14/bin/pg_isready",
                             "/usr/local/opt/postgresql@14/bin/pg_isready")
                 if os.access(p, os.X_OK)]
        if not found:
            pytest.skip("no Homebrew postgresql@14 on this machine (expected in CI)")

        result = subprocess.run(
            ["/bin/bash", str(SCRIPT)],
            env={"PATH": self.MINIMAL_PATH, "HOME": str(tmp_path),
                 "BETBOT_LOG_DIR": str(tmp_path / "logs"), "BETBOT_UPDATE_CMD": "true",
                 "BETBOT_NOTIFY_CMD": "/usr/bin/true"},
            capture_output=True, text=True, timeout=30)
        assert any(f"Using pg_isready at {p}" in result.stdout for p in found)
