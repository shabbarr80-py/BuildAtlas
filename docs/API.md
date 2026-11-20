# API

All application routes are under `/api/v1`. Send `Authorization: Bearer <token>` after register/login. Errors use FastAPI's standard validation response or `{ "detail": { "error": { "code", "message" } } }` for application errors.

| Method | Route | Purpose |
|---|---|---|
| POST | `/auth/register`, `/auth/login` | Create account / issue JWT |
| GET, POST | `/projects` | List owned projects / create |
| GET, PATCH, DELETE | `/projects/{id}` | Read, update, archive |
| POST | `/projects/{id}/analyses` | Queue analysis (202; max 10 per hour/user) |
| GET | `/projects/{id}/analyses` | List a project's analysis history |
| GET | `/analyses/{id}` | Poll analysis status/result |
| GET | `/analyses/{id}/sources`, `/repositories`, `/recommendations` | Inspect evidence and stack |
| GET | `/projects/{id}/roadmap` | Read current project roadmap |
| PATCH | `/roadmap/tasks/{id}` | Change task status/priority |
| GET | `/analyses/{id}/export?format=md\|json` | Export completed analysis |

Every resource lookup checks the owning user. OpenAPI docs are at `/docs`.
