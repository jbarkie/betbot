# Live pitcher lookup measurements

The serving path emits JSON lines to stderr through the dedicated
`betbot.pitcher` logger at INFO level, including with Uvicorn's default logging.
It does not log user identities, credentials, response bodies, or model inputs.
The five-second budget, request ordering, predictions, and 15-minute cache TTL
are unchanged by instrumentation. Historical collection is not instrumented here.

## Capture

Retain API stdout/stderr in the service's log collector. For a manual local run,
from the repository root with the virtual environment activated:

```bash
mkdir -p logs
python -m api.src.main 2>&1 | tee -a logs/api.log
```

This starts the API; it does not load the data-update scheduler. Logs are emitted
only when analytics actually resolves pitcher features. If the ML model is
unavailable or there is little analytics traffic, elapsed calendar time alone
does not produce a useful sample. Retain at least the two-week observation window
(preferably 30 days). No automatic file rotation or retention is configured here;
use the service's log management and do not commit captured logs.

## Events

All events contain a UTC `timestamp` and a per-resolution `lookup_id`.

| Event | Meaning and fields |
| --- | --- |
| `pitcher_http_request` | One request actually started: `request_type`, `pitcher_id` for logs, `game_id`, `elapsed_ms`, `status_code`, and `outcome` (`success`, `http_error`, `request_timeout`, `invalid_response`, `cancelled`, or unexpected `error`). Timings include body reading and JSON parsing. Cancelled requests emit a record in `finally`. |
| `pitcher_live_lookup` | One live lookup attempt, never a cache hit: `elapsed_ms`, `budget_ms`, `outcome` (`completed`, `upstream_error`, `budget_exhausted`, `lookup_error`, `cancelled`), last `stage`/`active_team_id`, `resolved_team_ids`, and `fallback_reasons` for unresolved needed teams. `completed` can legitimately mean no announced starters or no usable prior starts. |
| `pitcher_features` | One feature resolution: `cache_hit`, `cache_age_seconds`, `live_attempted`, game/matchup identifiers, total resolution `elapsed_ms`, and `home`/`away` objects. Each side records a source (`stored`, `live`, `fallback`) for each of ERA, WHIP, and K/9, plus a `fallback_reason` or null. Cache hits preserve provenance and `origin_lookup_id` from the original computation; their own `lookup_id` is new. |

Fallback reasons distinguish `starter_not_announced`, `no_usable_pregame_stats`,
`request_timeout`, `http_error`, `invalid_response`, `budget_exhausted`,
`lookup_error`, `game_not_resolved`, `incomplete_stats`, and
`feature_resolution_error`. Fallback means the existing median/default policy;
it does not automatically lower prediction confidence.

## Review after representative use

Track the evaluation in [GitHub issue #53](https://github.com/jbarkie/betbot/issues/53).

Start the window when the instrumented API is deployed, not when the PR merges.
After two weeks, aim for at least 100 live attempts spanning multiple game days;
extend the window if traffic is sparse. This is a starting sample target, not a
statistical guarantee, and offseason behavior may not represent regular-season use.

1. Count `pitcher_live_lookup` events for the denominator. Report the fraction
   with `outcome=budget_exhausted`, and report HTTP errors separately. Cache hits
   must not inflate the number of network attempts.
2. Summarize elapsed p50/p95/p99 for completed lookups and request types. Report
   timed-out/cancelled counts alongside percentiles; the cutoff censors the
   unobserved natural completion times of slow requests.
3. Count pitcher sides/features using fallback by reason. Use `pitcher_features`
   cache-hit events to measure repeated exposure to cached fallback, linking
   `origin_lookup_id` when necessary; do not count these as new live failures.
4. Compare which side completes first and which stage hits the deadline.
   Consider fetching both logs concurrently before increasing the shared budget.
5. Record retain/change rationale and any diagnostic experiment in the follow-up
   issue. More time does not fix an unannounced starter, an empty prior history,
   or most HTTP errors. Measure endpoint latency separately: these events do not
   include all analytics work or model inference. Any longer diagnostic budget
   must be deliberate; instrumentation does not increase it automatically.
