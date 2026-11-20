# Database

UUID primary keys and timezone-aware timestamps are used throughout. `projects.user_id`, `analysis_runs.project_id`, and analysis status are indexed. Deleting a user cascades through owned projects and their dependent records; the product delete action archives projects instead. JSON fields use PostgreSQL JSONB and SQLite JSON for local tests. A missing GitHub license remains NULL and is never inferred to be open source.

Apply migrations with `alembic upgrade head` from `apps/api`.
