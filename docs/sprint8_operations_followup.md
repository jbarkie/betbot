# Sprint 8 operations follow-up

Status: Implementation complete; final validation and publishing in progress. Authorized by the user's request on 2026-09-26 to address the
remaining limitations now. This extends the open Sprint 8 branch; it does not
change the previously approved retrospective or claim new manual observations.

## Scope and acceptance criteria

1. **Pitcher lookup budget (#49, M).** Use cancellable asynchronous HTTP for serving
   only, with a five-second total network budget across the probable-starter and
   game-log requests. Preserve completed results, fill missing values with model
   medians, close connections on cancellation, and do not leave a background
   request running. Database queries and model computation are outside this
   budget. Tests cover stalled/streaming responses, successful lookups, partial
   results, cleanup, and the real HTTP endpoint. Historical collection retains
   its synchronous client and 30-second timeouts.
2. **Automatic recovery (#50, M).** Before an update, derive recovery dates from the
   persisted skip marker. For gaps over 30 days, include the missed range in the
   schedule and team-stat refresh, and the affected pitcher seasons. Retain the
   marker if the update or recovery is incomplete. Commit successful work so a
   retry can skip existing rows. Tests cover date boundaries, multi-season
   recovery, argument forwarding, partial failures, and retry behavior. No live
   backfill is run merely to test this change.
3. **Notification diagnosis (#51, S).** Provide a repeatable notification check using
   the scheduler's notifier and document how to check macOS notification
   permissions and scheduled execution. A command succeeding is never recorded
   as visual confirmation. Ask the user to observe a live diagnostic; record
   only the result they actually report.

Dependencies: recovery must distinguish a complete update from a successful
process with partial downloads before markers can be cleared. Biggest
uncertainties: historical API coverage and macOS notification presentation.

## Implementation and operations

### Live network budget

HTTPX async requests share one five-second `asyncio.wait_for` budget. Analytics
still opens, uses, and closes SQLAlchemy sessions on its worker thread. Only
primitive game IDs/dates cross back to the API loop for live HTTP, avoiding an
uncancellable Requests thread and avoiding temporary-loop DNS shutdown on the
serving path. The deadline retains already-computed sides and closes active
responses. It is not a hard real-time guarantee for the entire prediction:
database work, model computation, and cancellation cleanup are outside the limit.
Historical collection still uses Requests with its 30-second default.

### Automatic recovery

The earliest skipped morning also missed the previous day's results. The
scheduler compares that previous day with the inclusive 30-day refresh window.
Outside the window it passes `--recover-from` to the updater. Schedule fetching
starts at the earlier of that date and the current regular-season start; team
stats are fetched in ranges split at calendar-year boundaries; pitcher game logs
are collected for each affected season. Shorter gaps use the regular window with
`--require-complete` so an incomplete download does not silently clear the marker.

Strict recovery requires team stats for clubs that played on each completed date
and propagates HTTP failures in pitcher collection. Valid empty pitcher logs
remain normal, so this does not guarantee a known starter for every game.
Completed team-stat dates are committed; a failed date is rolled back when the
session closes. Failed runs retain the exact skip marker, and a later run retries
while skipping existing rows. Invalid/future marker timestamps stop the update
without clearing evidence. Only run one updater at a time; a multi-process
recovery lock is not part of this change.

`BETBOT_UPDATE_CMD` is a test override and now receives the updater arguments.
Other overrides remain `BETBOT_PG_ISREADY`, `BETBOT_LOG_DIR`,
`BETBOT_NOTIFY_CMD`, `BETBOT_VENV_PATH`, `BETBOT_BREW_CANDIDATES`, and
`BETBOT_HOMEBREW_ROOTS`. Do not replace the real updater with a command that
returns success without doing recovery in production.

### Notification setup and evidence

Build with `bash machine_learning/scripts/setup_notifications.sh`. Sources live
in `machine_learning/scripts/notifications`; the locally compiled and ad-hoc
signed app and compiler cache live in ignored `.local/`. No binary or signing
credentials are committed. macOS 11+ and Xcode Command Line Tools are required.
Then run `bash machine_learning/scripts/notify_macos.sh --authorize` and allow
BetBot Notifier. Use `--status` to inspect authorization without sending an alert.

The scheduler prefers this app when installed and otherwise falls back to
`osascript`. Daily runs never open a permission request. A unique temporary
result file carries errors back from the helper because `open` does not forward
app exit status; failures remain best effort and never erase a skip marker.
The helper exits after 30 seconds if the notification service does not respond.

On 2026-09-26, the user explicitly reported no visible osascript notification.
After the new app reported authorization, the user confirmed the scheduler's
manual diagnostic was visible at approximately 14:03 America/Denver, and also
confirmed a second notification from a temporary launchd job at approximately
14:04. That temporary job was removed afterward; the regular daily job was not
reconfigured. Use `--check-notification` for future checks: it neither writes a
skip marker nor runs an update. If delivery later stops, inspect Notifications →
BetBot Notifier and Focus settings; acceptance by macOS alone proves no visibility.

### Discovered historical-data issue (#52)

Read-only MLB API checks on 2026-09-26 showed the old team hitting request
(`stats=season`, `start_date=2025-04-01`, `end_date=2025-04-02`, `season=2025`)
returned 162 games for Tampa Bay. The supported `stats=byDateRange` request with
`startDate`/`endDate` returned 2 games. The collector now uses that date-range
contract and recognizes its response type. This correction is necessary before
automatic backfill can safely honor requested dates.

No existing rows were rewritten and no model was retrained. Recovery skips stored
rows, so it cannot repair previously misdated snapshots. Audit the existing data
and intended feature aggregation windows before the next retrain:
https://github.com/jbarkie/betbot/issues/52. No live backfill was run for validation.

## Validation (2026-10-01)

- Full backend/ML suite: **282 passed**, with 52 non-failing warnings (scikit-learn
  feature-name warnings, empty-slice calculations, and mixed-date parsing).
- Recovery tests rerun after a small cleanup: **13 passed**.
- Native notifier rebuilt from its final tracked source location; status returned
  `Notifications authorized; alert setting: 2`. No additional visible-delivery
  claim is inferred from this status; the user observations above are the evidence.
- Shell syntax checks and `git diff --check` passed.
- Final-head GitHub CI is checked after publishing; frontend and migration
  integration validation are delegated to those existing CI jobs.
