# Sprint 1 Retrospective

**Dates**: 2026-04-16 – 2026-04-17
**Sprint Goal**: Surface ML win probabilities in the game cards analytics modal
**PR**: https://github.com/jbarkie/betbot/pull/17
**Issues**: #15, #16

---

## Outcomes vs Acceptance Criteria

| Criterion | Status | Notes |
|-----------|--------|-------|
| `getMLBAnalytics(gameId)` returns typed response | Met | Convenience wrapper around `analyze()`; same latency |
| `AnalyticsResponse` matches `/analytics/mlb/game` shape | Met | All 14 fields from `MlbAnalyticsResponse` typed |
| Service has ≥1 test covering success and error | Met | 3 tests added |
| Game cards display home/away win % | Met | Split probability bar with computed signals |
| Display updates within 500ms of game card render | Met | No new network calls; synchronous from existing result |
| ≥3 tests covering prediction display, loading, error | Partially met | 7 tests added for display; loading/error live in `GameComponent`, not the modal |

---

## Retrospective Categories

### Acceptance Criteria Coverage
"Loading and error state" criterion was written for the modal but those states live in `GameComponent`. Criteria should specify which component owns the state (container vs presentational) to avoid ambiguity during testing.

### Test Coverage Quality
7 tests added, all meaningful. Fallback derivation for rule-based predictions (using `predicted_winner` + `win_probability` when explicit split probabilities are absent) is a good edge-case catch. `data-testid` attributes used for test queries — more resilient than CSS class selectors.

### Code Quality and Conventions
- Computed signals (`homePct`, `awayPct`, `keyFactorEntries`) follow existing Angular Signals pattern
- `data-testid` attributes introduced — not used elsewhere in the codebase; added as a convention to CLAUDE.md
- `analyze({gameId}, sport)` kept generic — correct decision for future multi-sport extensibility

### Documentation Completeness
- Sprint history updated in `ALL_SPRINTS_MASTER_PLAN.md`
- `CLAUDE.md` updated with `data-testid` and AC ownership conventions
- `sprint_status.json` updated

### Phase Discipline
All 6 phases executed in order. One justified implementation deviation: T2.1 ("add analytics fetch to MlbComponent") merged into T2.2 because `GameComponent` already owned the fetch — recognized as an implementation choice within scope, not a scope change.

Pre-kickoff correctly caught a real environment bug (`esbuild darwin-arm64` mismatch) before any code was written.

### Estimation Accuracy
Estimated ~13 hours; actual execution was approximately 1 session. Tasks were well-scoped. The analytics service and modal already existed — less scaffolding than planned. T2.1 (Sonnet, score 25) was the hardest conceptual task; resolved by recognizing an existing pattern.

### Surprises or Blockers
- `esbuild darwin-arm64` platform mismatch blocked frontend test run; fixed with `npm install`
- Sprint was additive rather than greenfield — service and modal already existed; sprint focused on extending them with rich data

### Lessons Learned
- Specify which component owns state in AC (container vs presentational)
- `data-testid` attributes improve test resilience — now documented as convention
- `gh pr edit` is broken in this environment due to GitHub Projects (classic) deprecation; use `gh api` for PR body updates

---

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Keep `analyze({gameId}, sport)` generic | Multi-sport extensibility — `getMLBAnalytics` is a convenience wrapper, not a replacement |
| Remove ML vs Rule-based badge | Conveyed internal implementation detail, not meaningful user-facing information |
| Stale database data deferred | Analyzed games successfully with stale data; unclear if this is a bug or acceptable behavior — added to backlog |

---

## Backlog Items Added

- **Stale data behavior investigation** — When DB data is stale, the API still returns analytics for today's games. Determine whether this is expected (uses last known team stats) or a bug (should return an error or warning when data is >N days old).
