# Phase 0: Project Setup
## Repository Structure, Development Environment, CI/CD

> **Duration**: Week 1
> **Prerequisites**: None
> **Outcome**: Fully configured development environment with CI/CD pipeline

---

## Context for LLM Assistant

You are helping build an AI-powered construction takeoff platform. This phase establishes the project foundation including:
- Monorepo structure with backend (Python/FastAPI) and frontend (React/TypeScript)
- Docker-based development environment
- Database setup (PostgreSQL + Redis)
- CI/CD pipeline with GitHub Actions
- Code quality tooling
- **Multi-LLM provider support** for AI operations

---

## Task List

### Task 0.1: Initialize Repository Structure

Create the base repository structure:

```bash
mkdir -p takeoff-platform/{backend,frontend,docker,scripts,docs}
cd takeoff-platform
git init
```

Create `.gitignore`:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
*.egg-info/
dist/
build/
.eggs/
*.egg
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*

# Build outputs
frontend/dist/
*.local

# Environment
.env
.env.local
.env.*.local
!.env.example

# IDE
.idea/
.vscode/
*.swp
*.swo
*~
.DS_Store

# Docker
docker/data/

# Logs
logs/
*.log

# Test
coverage/
.nyc_output/

# Uploads (local dev)
uploads/
```

Create `.env.example`:

```env
# Application
APP_ENV=development
DEBUG=true
SECRET_KEY=your-secret-key-change-in-production

# Database
DATABASE_URL=postgresql+asyncpg://takeoff:takeoff@localhost:5432/takeoff
DATABASE_POOL_SIZE=20

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Storage (MinIO/S3)
STORAGE_ENDPOINT=localhost:9000
STORAGE_ACCESS_KEY=minioadmin
STORAGE_SECRET_KEY=minioadmin
STORAGE_BUCKET=takeoff-documents
STORAGE_USE_SSL=false

# =============================================================================
# LLM API KEYS - Multi-Provider Support
# =============================================================================
# The platform supports multiple LLM providers for AI operations.
# Configure the API keys for providers you want to use.
# At minimum, configure ONE provider. For benchmarking, configure ALL.

# Anthropic (Claude) - Recommended primary provider
ANTHROPIC_API_KEY=your-anthropic-api-key

# OpenAI (GPT-4o)
OPENAI_API_KEY=your-openai-api-key

# Google (Gemini)
GOOGLE_AI_API_KEY=your-google-ai-api-key

# xAI (Grok) - Uses OpenAI-compatible API
XAI_API_KEY=your-xai-api-key

# =============================================================================
# LLM Provider Configuration
# =============================================================================
# Default provider for AI operations (anthropic, openai, google, xai)
DEFAULT_LLM_PROVIDER=anthropic

# Fallback providers (comma-separated, in order of preference)
# If primary provider fails, system will try these in order
LLM_FALLBACK_PROVIDERS=openai,google

# Per-task provider overrides (optional)
# Leave empty to use DEFAULT_LLM_PROVIDER for all tasks
LLM_PROVIDER_PAGE_CLASSIFICATION=
LLM_PROVIDER_SCALE_DETECTION=
LLM_PROVIDER_ELEMENT_DETECTION=
LLM_PROVIDER_MEASUREMENT=

# =============================================================================
# Google Cloud Vision (for OCR - separate from Gemini LLM)
# =============================================================================
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Frontend
VITE_API_URL=http://localhost:8000
```

---

### Task 0.2: Backend Setup (Python/FastAPI)

Create `backend/pyproject.toml`:

```toml
[project]
name = "takeoff-platform"
version = "0.1.0"
description = "AI-powered construction takeoff platform"
requires-python = ">=3.11"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]

[tool.black]
line-length = 100
target-version = ['py311']
include = '\.pyi?$'

[tool.isort]
profile = "black"
line_length = 100

[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true
```

Create `backend/requirements.txt`:

```txt
# Web Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# Database
sqlalchemy[asyncio]==2.0.25
asyncpg==0.29.0
alembic==1.13.1

# Task Queue
celery[redis]==5.3.6
redis==5.0.1

# Validation
pydantic==2.5.3
pydantic-settings==2.1.0
email-validator==2.1.0

# Storage
boto3==1.34.25
python-magic==0.4.27

# PDF/Image Processing
pdf2image==1.17.0
pymupdf==1.23.18
Pillow==10.2.0
numpy==1.26.3

# Computer Vision
opencv-python-headless==4.9.0.80
scikit-image==0.22.0

# ML/AI
torch==2.1.2
torchvision==0.16.2
ultralytics==8.1.0

# LLM Clients - Multi-Provider Support
anthropic==0.18.1
openai==1.10.0              # Also used for xAI (Grok) - OpenAI-compatible API
google-generativeai==0.3.2

# Google Cloud Vision (OCR)
google-cloud-vision==3.5.0

# HTTP Client
httpx==0.26.0

# Auth
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Utilities
python-dotenv==1.0.0
structlog==24.1.0
tenacity==8.2.3
```

Create `backend/requirements-dev.txt`:

```txt
-r requirements.txt

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
httpx==0.26.0
factory-boy==3.3.0

# Code Quality
black==24.1.0
isort==5.13.2
mypy==1.8.0
ruff==0.1.13

# Type Stubs
types-redis==4.6.0.11
types-pillow==10.2.0.0
```

Create `backend/app/__init__.py`:

```python
"""Takeoff Platform - AI-powered construction takeoff automation."""

__version__ = "0.1.0"
```

Create `backend/app/config.py`:

```python
"""Application configuration with multi-LLM provider support."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    secret_key: str = Field(..., min_length=32)

    # Database
    database_url: PostgresDsn
    database_pool_size: int = 20

    # Redis
    redis_url: RedisDsn
    celery_broker_url: RedisDsn
    celery_result_backend: RedisDsn

    # Storage
    storage_endpoint: str
    storage_access_key: str
    storage_secret_key: str
    storage_bucket: str = "takeoff-documents"
    storage_use_ssl: bool = False

    # ==========================================================================
    # LLM API Keys - Multi-Provider Support
    # ==========================================================================
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    google_ai_api_key: str | None = None
    xai_api_key: str | None = None  # Grok

    # ==========================================================================
    # LLM Provider Configuration
    # ==========================================================================
    default_llm_provider: Literal["anthropic", "openai", "google", "xai"] = "anthropic"
    llm_fallback_providers: str = ""  # Comma-separated list
    
    # Per-task provider overrides (empty = use default)
    llm_provider_page_classification: str = ""
    llm_provider_scale_detection: str = ""
    llm_provider_element_detection: str = ""
    llm_provider_measurement: str = ""

    # Google Cloud Vision (OCR - separate from Gemini)
    google_application_credentials: str | None = None

    @field_validator("llm_fallback_providers", mode="before")
    @classmethod
    def parse_fallback_providers(cls, v: str) -> str:
        """Validate fallback providers."""
        if not v:
            return ""
        valid_providers = {"anthropic", "openai", "google", "xai"}
        providers = [p.strip().lower() for p in v.split(",") if p.strip()]
        invalid = set(providers) - valid_providers
        if invalid:
            raise ValueError(f"Invalid LLM providers: {invalid}")
        return ",".join(providers)

    @property
    def fallback_providers_list(self) -> list[str]:
        """Get fallback providers as a list."""
        if not self.llm_fallback_providers:
            return []
        return [p.strip() for p in self.llm_fallback_providers.split(",")]

    @property
    def available_providers(self) -> list[str]:
        """Get list of providers with configured API keys."""
        providers = []
        if self.anthropic_api_key:
            providers.append("anthropic")
        if self.openai_api_key:
            providers.append("openai")
        if self.google_ai_api_key:
            providers.append("google")
        if self.xai_api_key:
            providers.append("xai")
        return providers

    def get_provider_for_task(self, task: str) -> str:
        """Get the LLM provider to use for a specific task.
        
        Args:
            task: One of 'page_classification', 'scale_detection', 
                  'element_detection', 'measurement'
        
        Returns:
            Provider name to use for this task
        """
        task_overrides = {
            "page_classification": self.llm_provider_page_classification,
            "scale_detection": self.llm_provider_scale_detection,
            "element_detection": self.llm_provider_element_detection,
            "measurement": self.llm_provider_measurement,
        }
        
        override = task_overrides.get(task, "")
        if override and override in self.available_providers:
            return override
        
        # Use default if available, otherwise first available
        if self.default_llm_provider in self.available_providers:
            return self.default_llm_provider
        
        if self.available_providers:
            return self.available_providers[0]
        
        raise ValueError("No LLM providers configured. Set at least one API key.")

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
```

Create `backend/app/main.py`:

```python
"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.config import get_settings
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
        title="Takeoff Platform API",
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
```

Create `backend/app/api/__init__.py`:

```python
"""API routes package."""
```

Create `backend/app/api/routes/settings.py`:

```python
"""Settings API routes for LLM provider configuration."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import get_settings

router = APIRouter()
settings = get_settings()


class LLMProviderInfo(BaseModel):
    """Information about an LLM provider."""
    name: str
    display_name: str
    model: str
    available: bool
    is_default: bool


class LLMSettingsResponse(BaseModel):
    """Response with LLM settings."""
    available_providers: list[LLMProviderInfo]
    default_provider: str
    fallback_providers: list[str]
    task_overrides: dict[str, str]


class LLMTaskConfigRequest(BaseModel):
    """Request to update task-specific provider."""
    task: str
    provider: str


PROVIDER_INFO = {
    "anthropic": {
        "display_name": "Anthropic (Claude)",
        "model": "claude-3-5-sonnet-20241022",
    },
    "openai": {
        "display_name": "OpenAI (GPT-4o)",
        "model": "gpt-4o",
    },
    "google": {
        "display_name": "Google (Gemini 2.5 Flash)",
        "model": "gemini-1.5-pro",
    },
    "xai": {
        "display_name": "xAI (Grok)",
        "model": "grok-vision-beta",
    },
}


@router.get("/llm", response_model=LLMSettingsResponse)
async def get_llm_settings() -> LLMSettingsResponse:
    """Get current LLM provider settings."""
    providers = []
    for name, info in PROVIDER_INFO.items():
        providers.append(LLMProviderInfo(
            name=name,
            display_name=info["display_name"],
            model=info["model"],
            available=name in settings.available_providers,
            is_default=name == settings.default_llm_provider,
        ))
    
    task_overrides = {
        "page_classification": settings.llm_provider_page_classification or settings.default_llm_provider,
        "scale_detection": settings.llm_provider_scale_detection or settings.default_llm_provider,
        "element_detection": settings.llm_provider_element_detection or settings.default_llm_provider,
        "measurement": settings.llm_provider_measurement or settings.default_llm_provider,
    }
    
    return LLMSettingsResponse(
        available_providers=providers,
        default_provider=settings.default_llm_provider,
        fallback_providers=settings.fallback_providers_list,
        task_overrides=task_overrides,
    )


@router.get("/llm/providers")
async def list_available_providers() -> dict:
    """List available LLM providers with their status."""
    return {
        "providers": settings.available_providers,
        "default": settings.default_llm_provider,
        "all_supported": list(PROVIDER_INFO.keys()),
    }
```

---

### Task 0.3: Frontend Setup

[... rest of frontend setup remains the same ...]

---

### Task 0.4: Database Configuration

[... database configuration remains the same ...]

---

### Task 0.5: Docker Configuration

Update `docker/docker-compose.yml` to include LLM API keys:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: takeoff-db
    environment:
      POSTGRES_USER: takeoff
      POSTGRES_PASSWORD: takeoff
      POSTGRES_DB: takeoff
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U takeoff"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: takeoff-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  minio:
    image: minio/minio:latest
    container_name: takeoff-minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 5s
      timeout: 5s
      retries: 5

  api:
    build:
      context: ../backend
      dockerfile: ../docker/Dockerfile.api
    container_name: takeoff-api
    environment:
      - DATABASE_URL=postgresql+asyncpg://takeoff:takeoff@db:5432/takeoff
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
      - STORAGE_ENDPOINT=minio:9000
      - STORAGE_ACCESS_KEY=minioadmin
      - STORAGE_SECRET_KEY=minioadmin
      # LLM API Keys - passed from host .env file
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GOOGLE_AI_API_KEY=${GOOGLE_AI_API_KEY}
      - XAI_API_KEY=${XAI_API_KEY}
      - DEFAULT_LLM_PROVIDER=${DEFAULT_LLM_PROVIDER:-anthropic}
      - LLM_FALLBACK_PROVIDERS=${LLM_FALLBACK_PROVIDERS:-}
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    volumes:
      - ../backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  worker:
    build:
      context: ../backend
      dockerfile: ../docker/Dockerfile.worker
    container_name: takeoff-worker
    environment:
      - DATABASE_URL=postgresql+asyncpg://takeoff:takeoff@db:5432/takeoff
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
      - STORAGE_ENDPOINT=minio:9000
      - STORAGE_ACCESS_KEY=minioadmin
      - STORAGE_SECRET_KEY=minioadmin
      # LLM API Keys - passed from host .env file
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GOOGLE_AI_API_KEY=${GOOGLE_AI_API_KEY}
      - XAI_API_KEY=${XAI_API_KEY}
      - DEFAULT_LLM_PROVIDER=${DEFAULT_LLM_PROVIDER:-anthropic}
      - LLM_FALLBACK_PROVIDERS=${LLM_FALLBACK_PROVIDERS:-}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ../backend:/app
    command: celery -A app.workers.celery_app worker --loglevel=info

volumes:
  postgres_data:
  redis_data:
  minio_data:
```

[... rest of Docker configuration remains the same ...]

---

### Task 0.6: CI/CD Pipeline

[... CI/CD pipeline remains the same ...]

---

### Task 0.7: Makefile for Common Commands

[... Makefile remains the same ...]

---

### Task 0.8: README

Update `README.md`:

```markdown
# Takeoff Platform

AI-powered construction takeoff automation platform.

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Node.js 20+
- At least one LLM API key (Anthropic, OpenAI, Google, or xAI)

### Setup

1. Clone the repository
2. Copy environment file and configure API keys:
   ```bash
   cp .env.example .env
   # Edit .env and add your LLM API keys
   ```

3. Run setup:
   ```bash
   make setup
   ```

4. Start development environment:
   ```bash
   make dev
   ```

5. Access the application:
   - Frontend: http://localhost:5173
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/api/docs
   - MinIO Console: http://localhost:9001

## LLM Provider Configuration

The platform supports multiple LLM providers for AI operations:

| Provider | Model | Best For |
|----------|-------|----------|
| Anthropic | Claude 3.5 Sonnet | General accuracy, recommended primary |
| OpenAI | GPT-4o | Good all-around performance |
| Google | Gemini 2.5 Flash | Cost-effective option |
| xAI | Grok Vision | Alternative option |

### Configuration Options

```env
# Set default provider
DEFAULT_LLM_PROVIDER=anthropic

# Configure fallbacks (comma-separated)
LLM_FALLBACK_PROVIDERS=openai,google

# Override provider per task (optional)
LLM_PROVIDER_PAGE_CLASSIFICATION=google
LLM_PROVIDER_SCALE_DETECTION=anthropic
LLM_PROVIDER_ELEMENT_DETECTION=anthropic
LLM_PROVIDER_MEASUREMENT=anthropic
```

### Benchmarking Providers

Configure all provider API keys to run accuracy benchmarks:

```bash
# Run benchmark comparison across all providers
make benchmark-llm
```

## Development

### Running Tests
```bash
make test
```

### Running Linters
```bash
make lint
```

### Database Migrations
```bash
# Create a new migration
make migrate-create name="add_users_table"

# Apply migrations
make migrate
```

## Architecture

See `/docs/architecture` for detailed architecture documentation.
```

---

## Verification Checklist

After completing all tasks, verify:

- [ ] `docker compose up` starts all services without errors
- [ ] API responds at `http://localhost:8000/api/v1/health`
- [ ] Frontend builds and runs at `http://localhost:5173`
- [ ] Database connection works
- [ ] Redis connection works
- [ ] MinIO console accessible at `http://localhost:9001`
- [ ] All linters pass
- [ ] Test suite runs (even if minimal)
- [ ] **LLM settings endpoint returns available providers** (`GET /api/v1/settings/llm`)
- [ ] **At least one LLM provider shows as available**

---

## Next Phase

Once verified, proceed to **`02-DOCUMENT-INGESTION.md`** for implementing the document upload and processing pipeline.
