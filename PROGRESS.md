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
- [ ] 2. Backend and database hardening, PostgreSQL test support, authorization and coverage
- [ ] 3. Frontend flow, states, accessibility checks, and Playwright smoke CI
- [ ] 4. Pipeline schema, provider failures, source evidence, and injection-resistance tests
- [ ] 5. Cookie sessions, CSRF, ownership, request limits, Mermaid handling, and dependency audits
- [ ] 6. Restart recovery, analysis timeout, structured logs, request IDs, liveness/readiness
- [ ] 7. Production images, CI services, repository hygiene, backups, deployment and env docs
- [ ] 8. Final verification, coverage, unverified checks, and production verdict
