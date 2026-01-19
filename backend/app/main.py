"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.config import get_settings
from app.models import Project, Condition, Document, Page, Measurement  # Import models to register with SQLAlchemy
from app.api.routes import health, projects, documents, pages, conditions, measurements, exports, settings as settings_routes

logger = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    logger.info(
        "Starting application",
        env=settings.app_env,
        available_llm_providers=settings.available_providers,
        default_llm_provider=settings.default_llm_provider,
    )
    yield
    logger.info("Shutting down application")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="ForgeX Takeoffs API",
        description="AI-powered construction takeoff automation",
        version="0.1.0",
        docs_url="/api/docs" if settings.is_development else None,
        redoc_url="/api/redoc" if settings.is_development else None,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    app.include_router(health.router, prefix="/api/v1", tags=["Health"])
    app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
    app.include_router(documents.router, prefix="/api/v1", tags=["Documents"])
    app.include_router(pages.router, prefix="/api/v1", tags=["Pages"])
    app.include_router(conditions.router, prefix="/api/v1", tags=["Conditions"])
    app.include_router(measurements.router, prefix="/api/v1", tags=["Measurements"])
    app.include_router(exports.router, prefix="/api/v1", tags=["Exports"])
    app.include_router(settings_routes.router, prefix="/api/v1/settings", tags=["Settings"])

    return app


app = create_app()