# BetBot — All Sprints Master Plan

## Project

**BetBot** — Full-stack sports betting analytics app (FastAPI + PostgreSQL + Angular 19 + NgRx Signals + ML)

---

## Backlog: Next Sprint Candidates

> Prioritized list of potential work items. Reprioritize with `/sprint refine`.

### High Priority

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

---

## Sprint History

| Sprint | Dates | Goal | Outcome |
|--------|-------|------|---------|
| —      | —     | No sprints yet | — |

---

## Lessons Learned (Running Log)

_Updated after each retrospective._

---

## Notes

- ML `.joblib` model files are gitignored; always retrain after a fresh clone
- PostgreSQL runs on port **5439** (non-standard)
- Frontend at `localhost:4200`; API CORS is configured for that origin only
