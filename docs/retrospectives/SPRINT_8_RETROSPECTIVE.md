# Sprint 8 Retrospective (DRAFT — awaiting approval)

**Date:** 2026-09-26
**Branch:** `feature/20260922_Sprint_8`
**PR:** #48
**Goal:** Slow external calls no longer block the API event loop; skipped data refreshes are recorded and surfaced; training warns or stops when completed-game data is older than a configured age; CI proves every migration applies, rolls back one step, and re-applies.

> DRAFT: outcomes below are recorded; the Improvement Recommendations are proposals until the user approves them by number. Approval removes this marker.

---

## Sprint Outcomes vs Acceptance Criteria

### Issue #44 — Non-blocking external I/O in the analytics and games routes

| Criterion | Result |
|---|---|
| `call_odds_api` passes an explicit timeout; `requests.Timeout` produces HTTP 504 whose detail contains "timed out" | ✅ Met — `test_odds_timeout_maps_to_504`, `test_call_odds_api_passes_explicit_timeout` |
| Serving-path MLB Stats API requests use a 5s timeout; backfill retains 30s | ✅ Met — `TestServingPathTimeouts` asserts both values |
| With the live pitcher lookup raising `requests.Timeout`, the analytics response is 200 and all six pitcher features equal the training medians | ⚠️ Partially met — the medians half is tested directly (`test_request_timeout_yields_medians_not_an_error`); the 200 half rests on the existing never-raises contract rather than a route-level test with a timing-out collector |
| For each of the two routes, an unrelated coroutine completes while the external call is held open; 10s safety timeout, no sub-second assertion | ✅ Met — `test_event_loop_responsiveness.py`, both routes, plus a check that the blocking work ran off the main thread |
| `MLModelService` loads the model exactly once under concurrent first use | ✅ Met — `test_model_loads_exactly_once_under_concurrent_predict`; verified sensitive (two loads without the lock) |
| Every existing analytics and games test passes unmodified | ✅ Met — all 203 pre-existing tests passed before any new test was added |
| CLAUDE.md documents the ~15s worst-case prediction latency and the 504 behavior | ✅ Met |

### Issue #45 — Alembic migration check in CI

| Criterion | Result |
|---|---|
| A `migrations` CI job runs on push and PR to main against a service-container PostgreSQL using its own `DB_URL` | ✅ Met — explicit `DB_URL` in the workflow, not a secret |
| The job fails when `alembic heads` reports more than one head; the counting step is a shell script with a unit test that feeds it two-head output | ✅ Met — `scripts/ci/assert_single_head.sh`, `test_ci_scripts.py` (one, two, and zero heads) |
| `upgrade head`, `downgrade -1`, `upgrade head` in order; fails on any non-zero exit; rollback coverage stated in the workflow comment | ✅ Met — also run locally against a fresh scratch database |
| `all-checks-passed` requires `migrations` in both `needs` and its result check | ✅ Met |
| `alembic check` runs last and fails on model drift (verified locally with a throwaway column) | ✅ Met — local run reported the throwaway `users` column and exited non-zero |
| CLAUDE.md states that Alembic reads `DB_URL` from the environment, that `api/.env` is loaded through the config import, and that all three config variables must be present | ✅ Met |
| Job passes on the sprint PR | ✅ Met — green on PR #48 after two fixes: tracking `alembic.ini`, then pinning the `postgres:14` image digest and scoping job permissions for zizmor |

### Issue #46 — Data-freshness guard in training

| Criterion | Result |
|---|---|
| Freshness uses only `status == 'Final'` rows with non-null scores; a future scheduled row does not change the result | ✅ Met — `TestWhatCountsAsCompleted` |
| Reference date is the training `end_date`; a `--end-date` run against matching historical data reports fresh | ✅ Met — `test_completed_games_after_reference_date_are_ignored` |
| Empty or all-invalid-date input reports stale | ✅ Met — `TestNeverFreshWhenEmpty` (6 tests) |
| Exactly 3 days is fresh, 4 days is stale, at the default threshold | ✅ Met — `TestBoundary` |
| `--fail-on-stale` exits with code 2 before any model fitting; without it a warning is logged and training proceeds | ✅ Met — `TestMainWiring` asserts `prepare_training_data` and `train_and_evaluate` are never called on exit 2 |
| Model metadata for a new training run contains the four freshness fields | ✅ Met — `test_save_model_writes_freshness_fields` |
| CLAUDE.md documents the scope limits and the offseason adjustment | ✅ Met |

Live check on 2026-09-26: 7,553 schedule rows, newest completed game 2026-09-25, age 1 day, fresh.

### Issue #47 — Scheduler skip recording and notification

| Criterion | Result |
|---|---|
| A skipped run appends one timestamped line to `logs/mlb_update_skips.log` and exits 0 | ✅ Met — `TestSkip` |
| A successful update after skips logs `RESUMED` with attempt count, distinct-day count, and first-skip date, then removes the marker | ✅ Met — `TestResume`, including a 3-attempts-across-2-days case |
| A failed update leaves the marker unchanged | ✅ Met — `test_failed_update_preserves_marker` |
| With the notifier missing or failing, the skip is still recorded and the exit code is still 0 | ✅ Met — both cases tested |
| When the first skip is more than 30 days old, the RESUMED line includes the `--start-date` backfill command | ✅ Met — 31 days warns, 30 days does not |
| Manual: notification appears when the readiness check is overridden to fail, with PostgreSQL still running | ✅ Met — fired via real `osascript` on 2026-09-26 12:14 with no failure logged; user to confirm it was visible |
| CLAUDE.md documents the marker file, the env overrides, and that RESUMED does not imply full recovery | ✅ Met |

**27 of 28 criteria fully met, 1 partially met.** Backend/ML test suite grew from 203 to 253 (+50). Frontend unchanged at 219.

---

## Retrospective

### Acceptance Criteria Coverage

The Codex review's main point was that several original criteria proved less than the sprint goal promised. The rewritten criteria held up: every one was verifiable by a named test or a recorded observation, and the two that are not fully green are honestly labelled. The one partial (route-level 200 under a live-lookup timeout) is a test gap, not a behavior gap.

### Test Coverage Quality

- The responsiveness tests block on a `threading.Event` and use a 10s safety timeout, as Codex asked. No timing assertion under one second exists anywhere in the new tests.
- The concurrent-load test was checked for sensitivity by removing the lock: it loads twice without it, once with it. A concurrency test that passes either way is worthless; this one does not.
- The scheduler is a bash script, and it now has 12 subprocess tests that run the real script with every dependency injected. This is the first shell coverage in the repo.
- The CI head-count step is a script with its own tests, not a one-liner in YAML.

### Code Quality and Conventions

- Sessions were already opened and closed inside the synchronous bodies, so the `to_thread` change moved them onto the worker thread with no restructuring. A test pins that the session opens and closes on the same non-main thread.
- One self-inflicted bug: an automated import insertion landed inside an existing `from datetime import` line. The existing suite caught it on the first run. Prefer targeted string replacement over "insert before the first import".
- A tracked `.pyc` file under `alembic/__pycache__/` shows as modified whenever Alembic runs. It should not be in git.

### Documentation Completeness

CLAUDE.md, README, and the master plan were updated per card in the same commit as the code. The plan's Card 4 had a wrong claim about `.env` loading, caught by running the import chain before writing the CI job rather than after.

### Phase Discipline

- Phase 2 ran both suites before any change (203 and 219).
- Phase 3 used the new Plan Durability rule: the plan was committed as PROPOSED, corrected in a second commit, then flipped to Active on approval. A background agent had committed the first draft in parallel; the two copies were reconciled by reading the committed one line by line rather than trusting either.
- Phase 4 committed once per issue, in the approved order 1 → 4 → 3 → 2.
- Phase 6 opened the PR with the retrospective still pending, and this file was committed as DRAFT before asking for approval.

### Estimation Accuracy

The plan estimated ~29 hours across 21 tasks with per-task model assignments. The work completed in one session of roughly two hours wall clock, with a single model executing every task. The hour estimates are not useful as a forecast for this workflow; they remain useful as a relative sizing of the cards (Card 1 was the largest, Card 4 the smallest, as predicted).

### Surprises and Blockers

1. **Alembic's import chain loads the app config**, which raises without `ODDS_API_URL`, `DB_URL`, and `SECRET_KEY`. The committed plan said `.env` was never loaded; it is. Without the check, the CI job would have crashed on import and looked like a migration failure.
2. **The background durability agent** committed a plan while planning was still in progress. Harmless because both copies were compared, but it means two writers touched the same document in one session.
3. **`alembic check` already passed** on the current models, so it went from a conditional step to a required one.
4. **The training script prints a metric after saving**, which made three otherwise-correct wiring tests fail until the mock populated it.
5. **zizmor (pedantic persona) flagged the new job** for an unpinned `postgres:14` image and default permissions. Both were fixed in one commit; the image is pinned to its multi-arch manifest digest.
6. **`alembic.ini` was gitignored.** The first CI run of the `migrations` job failed with exit 255 and no message: `alembic heads` had no configuration to read. The local dry run against a scratch database could not catch it because the file exists locally. Fixed by tracking the file (default URL only, `DB_URL` overrides) and by making the head-count script print Alembic's stderr on failure.

### Lessons Learned

1. **Run the import chain before writing a CI job that imports it.** A module that raises on import turns a configuration gap into a misleading failure.
2. **Prove a concurrency test is sensitive by removing the guard.** Otherwise it documents nothing.
3. **Plan durability works.** The committed PROPOSED plan survived a scratchpad disappearing mid-session and a second writer; nothing was lost.
4. **Verify a new CI job from a clean clone, not the working tree.** Gitignored files are invisible to CI, and a local dry run silently depends on them. The fix was verified by cloning the branch into a temp directory and running the job's first step there.
5. **A script that runs under `set -e` must capture stderr before failing.** The first failure produced only an exit code; the second version of the script explains itself.

---

## Improvement Recommendations

1. **Remove tracked `__pycache__` files from git** and confirm `.gitignore` covers `*.pyc`. Small hygiene commit on this branch.
2. **Add a route-level test** for the analytics 200-with-medians path under a timing-out live lookup, closing the one partial criterion.
3. **Carry a Sprint 9 candidate for automatic backfill** when the scheduler resumes after a gap longer than 30 days, replacing the printed manual command.
4. **Carry a backlog candidate for a wall-clock budget across the three pitcher lookups**, lowering the ~15s worst case if real-world latency warrants it.
5. **Drop per-task hour estimates from future plans** in favor of relative card sizing, since the estimates did not predict effort in this workflow.

---

## Follow-Up Backlog Candidates

- Automatic backfill on RESUMED when the gap exceeds the team-stats window (Sprint 9 candidate)
- Wall-clock budget for the serving-path pitcher lookup
- Route-level timeout test for analytics
- Remove tracked `.pyc` files
