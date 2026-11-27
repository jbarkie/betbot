# Sprint 9 Retrospective — DRAFT

**Date:** 2026-11-26  
**Branch:** `feature/20261118_Sprint_9`  
**PR:** [#58](https://github.com/jbarkie/betbot/pull/58) · **Tracking card:** [#60](https://github.com/jbarkie/betbot/issues/60)  
**Goal:** Deliver long-requested NBA matchup analytics and evaluate omp on a hard, end-to-end task.

## Outcomes vs. acceptance checks

These checks were reconstructed from the user-requested scope and documented at closeout; they were not an approved pre-kickoff plan.

| Check | Outcome and evidence |
|---|---|
| NBA cards open an authenticated Analyze flow without regressing MLB analytics | **Met.** Chromium walkthrough, NBA auth/404 tests, and existing MLB route tests passed. |
| Show useful pregame team form from current results | **Met.** Two Chromium matchups with live ESPN results showed season and last-10 records, road/home splits, head-to-head, margins, and latest included dates. API tests check the Eastern-date cutoff and exclude non-qualifying games. |
| Keep market probabilities separate and retain useful data when one source fails | **Met.** Browser verification showed team form without a market; API tests verified the market remains available when ESPN fails. No trained NBA model or new paid feed. |
| Fix both reproduced review findings | **Met.** Concurrent-matchup tests exercise fetch sharing and cancellation. API tests show a tied final preserves valid stats and only flags comparisons it could affect. Chromium verified the warning with a synthetic tied final; none was observed in the live feed. |
| Verify before merge | **Met on implementation revision `38da0ef`.** All six GitHub checks passed. The final local fix run passed 20 focused API tests and 9 modal tests; these are not full-suite counts. PR remains open. |

## Retrospective

- **Acceptance coverage and phase discipline:** The first delivery showed only market odds; user feedback made clear that team-performance data was needed. Work happened on a feature branch in three incremental commits, followed by independent review and fixes. A formal kickoff, approved pre-build plan, and pre-build issue were not done. The sprint status, scope, and one tracking card were recorded at closeout rather than backdated.
- **Test quality and code conventions:** Sequential cache tests missed overlapping requests. Claude Sonnet 4.5 surfaced that case and the tied-final failure; both were reproduced before fixing. Its session-leak and serial-fetch claims did not hold up against the code. The API keeps bounded asynchronous ESPN calls and the UI reuses the shared modal.
- **Documentation:** README and CLAUDE.md explain the data source, cutoff, and fallback behavior. The master plan keeps NBA delivery separate from the unapproved MLB data-correctness work.
- **Estimation and cost:** No card estimate was made. The user requested an approximately $25 ceiling, but the implementation's billed cost was not available, so compliance is unverified. Claude CLI reported about $0.13 for the independent review attempts only.
- **Surprises and lessons:** The league-hosted endpoints probed from this environment returned 403s or timed out. ESPN's team schedule worked, but tagged the NBA Cup championship as regular-season data. Verify both reachability and inclusion rules before choosing a source. For shared caches, test overlapping requests and cancellation, not just sequential hits.

## Improvement recommendations — awaiting approval

1. For future external-data cards, record a live source sample and the cutoff, exclusion, and degradation rules before implementation.
2. For future cache or concurrency changes, require an overlapping-request test and reproduce each external review claim before accepting it.
3. When evaluating an agent against a dollar ceiling, check that per-task billing is observable before kickoff. Record unavailable cost as unknown, not as within budget.

No open NBA implementation blocker was identified in this closeout. The separate MLB repair, scheduler recovery, and retraining remain outside scope and unapproved. After retro approval, finalize the record before merging; the PR will close #60 on merge.
