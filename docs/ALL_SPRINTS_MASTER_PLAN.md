# BetBot — All Sprints Master Plan

## Project

**BetBot** — Full-stack sports betting analytics app (FastAPI + PostgreSQL + Angular 19 + NgRx Signals + ML)

---

## Backlog: Next Sprint Candidates

> Prioritized list of potential work items. Reprioritize with `/sprint refine`.

### High Priority

- [ ] **Migrate local database from Docker to native Homebrew PostgreSQL** — Remove Docker as a runtime dependency for local development. Install PostgreSQL via `brew install postgresql@16`, migrate existing data with `pg_dump`/`pg_restore`, update `api/.env` connection string, and strip Docker lifecycle management from the scheduler script entirely. Keeps `docker-compose.yml` for CI and onboarding but removes day-to-day Docker Desktop dependency. Unblocks reliable automated data updates and reduces always-on resource usage. See conversation context: Docker Desktop hangs scheduler for hours on wake; Docker is disproportionate overhead for a single local Postgres instance; production will use a managed Postgres service anyway.
- [ ] **NFL/NHL parity with MLB analytics** — Add ML-backed game analytics endpoints for NFL and NHL (currently only MLB has the ML prediction pipeline)
- [ ] **NBA analytics endpoint** — Extend the analytics system to NBA games
- [ ] **Frontend analytics integration** — Display ML predictions and confidence scores in the game cards UI (currently only available via API)
- [ ] **Model retraining automation** — Scheduled script or cron job to retrain MLB model as new game data accumulates
- [ ] **User favorites/watchlist** — Allow authenticated users to bookmark games or teams

### Medium Priority

- [ ] **Historical odds tracking** — Store odds snapshots over time per game to surface line movement
- [ ] **Push notifications** — Alert users when odds move significantly on a favorited game
- [ ] **Model evaluation dashboard** — Admin page showing prediction accuracy, confusion matrix, and feature importance
- [ ] **Multi-bookmaker comparison** — Expand beyond FanDuel to show best available line across bookmakers
- [ ] **Test coverage improvement** — Backend API coverage is partial; increase to 80%+ with integration tests for analytics endpoints

### Low Priority

- [ ] **Dark/light theme persistence** — Persist user theme preference server-side (currently settings store is in-memory)
- [ ] **Rate limiting** — Add per-user rate limiting to external Odds API proxy endpoints
- [ ] **OpenAPI docs UI** — Enable Swagger UI behind auth in production
- [ ] **Alembic migration CI check** — Fail CI if unapplied migrations exist on branch
- [ ] **Stale data behavior investigation** — When DB data is stale, the API still returns analytics for today's games using last-known team stats. Determine whether this is expected behavior or should surface a warning/error when data is older than N days

---

## Sprint History

| Sprint | Dates | Goal | Outcome |
|--------|-------|------|---------|
| Sprint 1 | 2026-04-16 | Surface ML win probabilities in the game cards analytics modal | PR #17 open — pending retro |
| Sprint 2 | 2026-04-17 | Upgrade Angular from v19 to v21 (via v20), NgRx to v21, jest to v30 | PR open — pending retro |

---

## Sprint 2 — Angular Upgrade (Planned)

**Goal:** Upgrade the frontend from Angular 19 to the latest stable Angular release, keeping all tests green and the app fully functional.

**Background:** The frontend currently runs Angular `^19.0.5` / CLI `^19.0.6`. Angular releases major versions every 6 months; staying current reduces security exposure and ensures access to new signals/control flow APIs. The `ng update` migration tooling handles most mechanical changes, but NgRx Signals and Jest config require manual verification.

### Acceptance Criteria

- [ ] `@angular/core`, `@angular/cli`, and all `@angular/*` packages updated to latest stable
- [ ] `@ngrx/signals` updated to a version compatible with the new Angular major (check NgRx release notes)
- [ ] `typescript` version updated to the range required by the new Angular (Angular dictates TS floor/ceiling)
- [ ] `jest-preset-angular` updated to a version compatible with the new Angular
- [ ] `ng build` produces a clean production build with no errors or warnings introduced by the upgrade
- [ ] All frontend tests pass (`npm test`)
- [ ] Dev server starts and the app is functional end-to-end (auth, game cards, analytics modal, theme toggle)
- [ ] Any automated migration schematics run by `ng update` are reviewed and committed separately from manual fixes

### Tasks

1. **Research** — Run `ng update` dry-run; review Angular changelog and migration guide for each skipped major; note breaking changes relevant to standalone components, signals, and control flow
2. **Dependency bump** — Run `ng update @angular/core @angular/cli` (use `--force` only if a peer dep conflict cannot be resolved otherwise); commit schematic output separately
3. **NgRx update** — Update `@ngrx/signals` to compatible version; review API changes to `signalStore`, `withState`, `withMethods`, `patchState`, `rxMethod`
4. **TypeScript & tooling** — Update `typescript`, `jest-preset-angular`, and `@types/*` packages to compatible versions; fix any type errors surfaced
5. **Test suite** — Run `npm test`; fix any broken specs (likely import path or API shape changes)
6. **Build verification** — Run `ng build`; resolve any template or strict-mode errors
7. **Manual smoke test** — Start dev server; verify auth flow, game list, analytics modal, and theme toggle work correctly
8. **esbuild / bundler config** — Check `angular.json` for any builder config changes required by the new version

### Risks

- **NgRx Signals API churn** — NgRx Signals is still stabilizing; minor API renames between versions are common. Check `@ngrx/signals` changelog before upgrading.
- **Jest / jest-preset-angular compatibility** — New Angular versions sometimes require a matching `jest-preset-angular` release that lags by a few weeks.
- **TypeScript strictness** — Angular upgrades sometimes raise the minimum TS version, which can surface latent type errors in existing code.
- **Schematic safety** — `ng update` schematics modify files automatically. Review every schematic change before committing to avoid unintended rewrites.

---

## Lessons Learned (Running Log)

**Sprint 2 (2026-04-17)**
- For Angular major-version upgrades, check `npm show @angular/core version --tag latest` before planning — `ng update` dry-run only steps one major at a time and does not reflect the true latest version on npm

**Sprint 1 (2026-04-17)**
- Specify which component owns state in AC: container components own loading/error; presentational components own display-only states
- `data-testid` attributes make tests more resilient to CSS changes — use them for test-facing elements
- `gh pr edit` is broken in this environment due to GitHub Projects (classic) deprecation; use `gh api repos/{owner}/{repo}/pulls/{n}` instead

---

## Notes

- ML `.joblib` model files are gitignored; always retrain after a fresh clone
- PostgreSQL runs on port **5439** (non-standard)
- Frontend at `localhost:4200`; API CORS is configured for that origin only
