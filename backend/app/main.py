from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.db.base_class import Base
from app.db.session import engine
from app import models  # noqa: F401  -- ensures all models are registered on Base.metadata

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Local-first, multi-vertical CRM for Sayanjali Nexus Private Limited",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
def on_startup():
    # Local-first convenience: auto-create tables if they don't exist yet.
    # Once Alembic migrations are the source of truth (Phase 2+), this can
    # be removed in favor of `alembic upgrade head` in the run script.
    Base.metadata.create_all(bind=engine)


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "environment": settings.ENVIRONMENT}
