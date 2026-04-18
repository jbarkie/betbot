# Sprint 2 Retrospective

**Date:** 2026-04-17
**Goal:** Upgrade Angular frontend from v19 to v21 (via v20), NgRx to v21, jest to v30
**PR:** https://github.com/jbarkie/betbot/pull/20
**Outcome:** All 6 acceptance criteria met

## Acceptance Criteria

| Criterion | Status |
|---|---|
| All `@angular/*` packages at `^21.x` | ✅ 21.2.9 / CLI 21.2.7 |
| `ng build` clean at both v20 and v21 checkpoints | ✅ 0 errors, 0 warnings |
| Schematic output committed separately at each hop | ✅ |
| All `@ngrx/*` at Angular-21-compatible versions | ✅ 21.1.0 |
| `npm test` passes all 219 tests | ✅ |
| `typescript` satisfies Angular 21's required range | ✅ 5.9.3 |

## Surprises and Blockers

- `ng update` dry-run only showed Angular 20 — user correctly identified v21 was available; confirmed via `npm show @angular/core version --tag latest`
- npm cache had root-owned files; required manual `sudo chown` outside of tool calls
- `jest-preset-angular@14` peer dep rejected `@angular/core >=20`; blocked Angular 21 hop until jest tooling was upgraded first
- NgRx and jest-preset-angular had a circular peer conflict; resolved by installing both in a single `npm install` invocation
- NgRx v21 install initially ran from project root instead of `frontend/`; caught during version verification

## Lessons Learned

- For Angular major-version upgrades, check `npm show @angular/core version --tag latest` before planning — `ng update` dry-run only steps one major at a time

## Notes

- Angular 21 schematic auto-migrated 9 components to `@if`/`@for` block control flow syntax — net improvement to codebase style
- picomatch high-severity ReDoS vulnerability surfaced and resolved via `npm audit fix` during the upgrade
