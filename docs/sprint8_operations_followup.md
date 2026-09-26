# Sprint 8 operations follow-up

Status: Active, authorized by the user's request on 2026-09-26 to address the
remaining limitations now. This extends the open Sprint 8 branch; it does not
change the previously approved retrospective or claim new manual observations.

## Scope and acceptance criteria

1. **Pitcher lookup budget (M).** Use cancellable asynchronous HTTP for serving
   only, with a five-second total network budget across the probable-starter and
   game-log requests. Preserve completed results, fill missing values with model
   medians, close connections on cancellation, and do not leave a background
   request running. Database queries and model computation are outside this
   budget. Tests cover stalled/streaming responses, successful lookups, partial
   results, cleanup, and the real HTTP endpoint. Historical collection retains
   its synchronous client and 30-second timeouts.
2. **Automatic recovery (M).** Before an update, derive recovery dates from the
   persisted skip marker. For gaps over 30 days, include the missed range in the
   schedule and team-stat refresh, and the affected pitcher seasons. Retain the
   marker if the update or recovery is incomplete. Commit successful work so a
   retry can skip existing rows. Tests cover date boundaries, multi-season
   recovery, argument forwarding, partial failures, and retry behavior. No live
   backfill is run merely to test this change.
3. **Notification diagnosis (S).** Provide a repeatable notification check using
   the scheduler's notifier and document how to check macOS notification
   permissions and scheduled execution. A command succeeding is never recorded
   as visual confirmation. Ask the user to observe a live diagnostic; record
   only the result they actually report.

Dependencies: recovery must distinguish a complete update from a successful
process with partial downloads before markers can be cleared. Biggest
uncertainties: historical API coverage and macOS notification presentation.
