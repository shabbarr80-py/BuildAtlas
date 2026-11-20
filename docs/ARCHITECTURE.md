# Architecture

BuildAtlas is a modular monolith. The Next.js App Router web app calls a versioned FastAPI API. SQLAlchemy persists users, projects, analyses, evidence, recommendations, and roadmap items in PostgreSQL. Alembic owns schema migrations. FastAPI BackgroundTasks executes the analysis pipeline in-process.

The GitHub REST client and LLM provider are interfaces. The default deterministic mock provider needs no secret; setting `LLM_API_KEY` selects the OpenAI-compatible provider. External repository content is treated as untrusted data. The system does not clone repositories or execute their code. Analysis failures are recorded on their run and never replace a previous completed result.

Analysis sequence: snapshot project input, search GitHub, pass untrusted repository metadata to the provider, validate required output fields, persist evidence/recommendations/roadmap, then mark complete. GitHub failure is non-fatal and yields an analysis without repository evidence.
