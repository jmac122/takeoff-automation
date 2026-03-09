# AGENTS.md

## Cursor Cloud specific instructions

### Architecture Overview

ForgeX Takeoffs is an AI-powered construction takeoff platform with:
- **Backend**: Python 3.11+ FastAPI app at `backend/` (port 8000)
- **Frontend**: React 18 + TypeScript + Vite SPA at `frontend/` (port 5173)
- **Infrastructure**: PostgreSQL 15, Redis 7, MinIO (S3-compatible storage) — all via Docker Compose

### Starting Infrastructure Services

```bash
# Start only infra (db, redis, minio) — not the api/worker/frontend containers
docker compose -f docker/docker-compose.yml up -d db redis minio
```

Docker must be running first. In Cursor Cloud VMs, start the daemon with:
```bash
sudo dockerd &>/tmp/dockerd.log &
sudo chmod 666 /var/run/docker.sock
```

### Running the Backend

```bash
cd backend && PYTHONPATH=/workspace/backend uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend reads its config from `backend/.env`. Key gotcha: the `.env.example` includes `VITE_API_URL` which causes a Pydantic validation error if present in the backend `.env` — remove or comment out any `VITE_*` vars and `GOOGLE_APPLICATION_CREDENTIALS` (unless you have credentials).

### Running the Frontend

```bash
cd frontend && npm run dev -- --host 0.0.0.0
```

### Running Database Migrations

```bash
cd backend && alembic upgrade head
```

Alembic loads settings from `app.config.Settings`, which requires a valid `backend/.env`.

### Running Tests

See `Makefile` and `.cursor/rules/testing.mdc` for full conventions. Quick reference:
- **Backend unit tests**: `cd backend && PYTHONPATH=/workspace/backend pytest tests/unit/ -v --tb=short`
- **Backend all tests** (excludes e2e): `cd backend && PYTHONPATH=/workspace/backend pytest tests/ --ignore=tests/e2e -v --tb=short`
- **Frontend tests**: `cd frontend && npm test`

Note: `PYTHONPATH=/workspace/backend` is required when running pytest outside Docker.

### Running Linters

- **Backend**: `cd backend && ruff check .` (ruff is the primary linter; black/isort/mypy also available)
- **Frontend**: `cd frontend && npm run lint`

### Known Pre-existing Issues

- ~25 backend tests fail due to incomplete mocking (database auth failures in integration tests, test fixture issues). These are pre-existing and not environment-related.
- Frontend ESLint reports 6 errors and 22 warnings, all pre-existing.
- Backend ruff reports ~176 lint issues, all pre-existing.
- `opencv-python-headless` is needed by `app.services.scale_detector` but is not listed in `requirements-base.txt` or `requirements-dev.txt`. Install it separately: `pip install opencv-python-headless==4.9.0.80`.
