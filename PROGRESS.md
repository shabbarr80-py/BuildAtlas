# Build progress

- [x] M1 Foundation: repo scaffold, Compose, models, initial migration, project endpoints, project list/form, API smoke test, CI, README.
- [x] M2 GitHub research: REST search, token support, metadata normalization, retrieval timestamps, mocked HTTP test, non-fatal unavailable research.
- [x] M3 Structured analysis: provider Protocol, OpenAI-compatible JSON mode, deterministic mock provider, required-section validation.
- [x] M4 Recommendations and architecture: persisted stack recommendations, alternatives, risks, Mermaid architecture, analysis tabs.
- [x] M5 Roadmap and exports: roadmap persistence and APIs, task status/priority updates, Markdown/JSON export.
- [x] M6 Auth and hardening: Argon2 password hashes, JWT, ownership checks, process-local analysis rate limiting, docs and security policy.

## Verification

- [x] API pytest (10 passed) and Ruff
- [x] Frontend ESLint, type-check, and production build
- [x] Alembic initial migration on SQLite
- [x] Production dependency audit (0 vulnerabilities)
- [ ] Compose startup (Docker unavailable in authoring environment)

Known follow-up: move background work and rate-limit state to shared durable infrastructure before running multiple API replicas.

## Phase 3: QA

- [x] 1. Docker and infrastructure configuration review, Docker build-context ignores, and Compose YAML parse passed; Docker startup, Postgres migration rollback, restart and volume checks UNVERIFIED (Docker CLI/Compose unavailable)
- [x] 2. Backend and database hardening: `TEST_DATABASE_URL` (defaults to an isolated SQLite database), repeatable schema fixture, UUID/JSON/JSONB portability, status constraints, indexes and uniqueness asserted; 17 API tests pass with 93% coverage; GitHub timeout/rate-limit, ownership, archive, task edit and status tests pass; Markdown/JSON exports now include source URL/timestamp. Alembic SQLite upgrade/downgrade passed. PostgreSQL execution UNVERIFIED per Docker-unavailable rule.
  - [x] `TEST_DATABASE_URL` and repeatable isolated test database fixture
  - [x] Constraints/indexes and DB portability assertions
  - [x] Cross-user resource coverage, archive semantics, analysis/roadmap/export, and HTTP status coverage
  - [x] GitHub failure cases and evidence export assertions
  - [x] Coverage report (93%)
- [ ] 3. Frontend flow, states, accessibility checks, and Playwright smoke CI
- [ ] 4. Pipeline schema, provider failures, source evidence, and injection-resistance tests
- [ ] 5. Cookie sessions, CSRF, ownership, request limits, Mermaid handling, and dependency audits
- [ ] 6. Restart recovery, analysis timeout, structured logs, request IDs, liveness/readiness
- [ ] 7. Production images, CI services, repository hygiene, backups, deployment and env docs
- [ ] 8. Final verification, coverage, unverified checks, and production verdict
