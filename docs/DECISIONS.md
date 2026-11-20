# Decisions

- The repository was empty and had no Git history, so Git was initialized for milestone commits.
- The API uses SQLAlchemy 2 declarative models, PostgreSQL JSONB with a SQLite JSON variant, and an initial metadata-based Alembic migration.
- `TEST_DATABASE_URL` overrides `DATABASE_URL` for the test process; an autouse fixture creates and drops a clean schema for each test. `pytest-cov` is included to make reported coverage reproducible.
- Local API development defaults to SQLite to keep first run simple; Compose explicitly supplies PostgreSQL.
- JWTs are held in browser localStorage for this first implementation. Production should move to secure, HttpOnly cookies and CSRF protection.
- FastAPI BackgroundTasks keeps the requested modular monolith free of Redis/Celery. Tasks are in-process and may be lost on process restart.
- GitHub search uses a compact query derived from the first project description terms, caches results in-process for ten minutes, and fetches at most two pages. GitHub errors do not prevent a blueprint from being generated.
- The mock provider returns a conservative template for an idea, identifies stack suggestions as estimates, and needs no external API key.
- The OpenAI-compatible provider requests strict JSON Schema output, validates the complete result with Pydantic, and retries once when a response is invalid.
- Per-user analysis throttling is process-local. Multi-instance deployments should move this counter to shared persistent storage.
- Docker is unavailable in the authoring environment; Compose behavior is documented but could not be exercised here.
