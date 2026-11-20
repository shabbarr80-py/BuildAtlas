# BuildAtlas

**Research Smarter. Architect Better. Build with Confidence.**

BuildAtlas is an open-source, evidence-backed software project planning engine. Describe an idea and get a structured blueprint: requirements, assumptions, technology trade-offs, architecture, risks, roadmap, GitHub repository evidence, and Markdown/JSON exports.

## Run locally

### Docker Compose

Install Docker Desktop, copy `.env.example` to `.env`, then run:

```sh
docker compose up --build
```

Open [http://localhost:3000](http://localhost:3000). The API is at [http://localhost:8000/docs](http://localhost:8000/docs). The API container applies Alembic migrations on startup. Leave `LLM_API_KEY` blank to use the deterministic mock provider. Add a GitHub token to raise API search limits.

### Without Docker

Start PostgreSQL or use the API's SQLite default. From `apps/api`: `python -m venv .venv`, activate it, `pip install -e '.[dev]'`, then `uvicorn app.main:app --reload`. From `apps/web`: `npm install` and `npm run dev`. Set `NEXT_PUBLIC_API_URL` if the API is not on localhost:8000.

## Configuration

See `.env.example` for database, JWT, GitHub, LLM, CORS, and frontend API settings. Never expose provider credentials to the browser. Repository metadata comes from GitHub REST; unknown license data remains unknown. AI output is planning assistance and should be reviewed before implementation.

## Checks

API: `ruff check . && pytest` from `apps/api`. Web: `npm run typecheck && npm run build` from `apps/web`.

## Limitations

Background analysis and rate-limit state are process-local, so restart loses queued work and multiple API replicas do not share throttling. GitHub search query construction is intentionally simple. The initial migration creates schema from current SQLAlchemy metadata; future schema revisions should use explicit Alembic operations. Use HTTPS and cookie-based sessions before exposing accounts to production traffic.

See [product spec](docs/PRODUCT_SPEC.md), [architecture](docs/ARCHITECTURE.md), [API](docs/API.md), and [decisions](docs/DECISIONS.md).
