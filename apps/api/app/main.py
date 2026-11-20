from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.routes import router
from app.core.config import effective_database_url, settings
from app.core.database import Base, engine
from app.models import entities  # noqa: F401

app = FastAPI(title="BuildAtlas API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix="/api/v1")


@app.exception_handler(Exception)
async def unhandled_error(_, exc):
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "internal_error", "message": "An unexpected error occurred"}},
    )


@app.get("/health")
def health():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok"}


if effective_database_url().startswith("sqlite"):
    Base.metadata.create_all(engine)
