.PHONY: help setup dev build test lint clean docker-up docker-down migrate create-migration benchmark-llm

# Default target
help: ## Show this help message
	@echo "ForgeX Takeoffs Development Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Setup commands
setup: ## Initial setup - install dependencies and setup environment
	@echo "Setting up development environment..."
	cp .env.example .env
	@echo "Please edit .env file and add your LLM API keys"
	$(MAKE) backend-setup
	$(MAKE) frontend-setup
	$(MAKE) docker-up
	$(MAKE) migrate

backend-setup: ## Setup Python backend dependencies
	cd backend && pip install -r requirements-dev.txt

frontend-setup: ## Setup Node.js frontend dependencies
	cd frontend && npm install

# Development commands
dev: ## Start development environment (all services)
	$(MAKE) docker-up
	@echo "Starting backend..."
	@cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
	@echo "Starting frontend..."
	@cd frontend && npm run dev &
	@echo "Development environment started!"
	@echo "Frontend: http://localhost:5173"
	@echo "API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/api/docs"
	@echo "MinIO Console: http://localhost:9001"

backend-dev: ## Start backend development server
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend-dev: ## Start frontend development server
	cd frontend && npm run dev

worker-dev: ## Start Celery worker for development
	cd backend && celery -A app.workers.celery_app worker --loglevel=info

# Build commands
build: ## Build all services
	$(MAKE) backend-build
	$(MAKE) frontend-build

backend-build: ## Build backend (no-op for interpreted language)
	@echo "Python backend - no build required"

frontend-build: ## Build frontend
	cd frontend && npm run build

# Testing commands
test: ## Run all tests
	$(MAKE) backend-test
	$(MAKE) frontend-test

backend-test: ## Run backend tests
	cd backend && pytest --cov=app --cov-report=term-missing

frontend-test: ## Run frontend tests
	cd frontend && npm test -- --watchAll=false

# Code quality commands
lint: ## Run all linters
	$(MAKE) backend-lint
	$(MAKE) frontend-lint

backend-lint: ## Run backend linters
	cd backend && black . && isort . && mypy .

frontend-lint: ## Run frontend linters
	cd frontend && npm run lint

# Database commands
migrate: ## Run database migrations
	cd backend && alembic upgrade head

create-migration: ## Create a new database migration
	@echo "Usage: make create-migration name='migration_name'"
	cd backend && alembic revision --autogenerate -m "$(name)"

migrate-rollback: ## Rollback last migration
	cd backend && alembic downgrade -1

# Docker commands
docker-up: ## Start all Docker services
	docker compose -f docker/docker-compose.yml up -d

docker-down: ## Stop all Docker services
	docker compose -f docker/docker-compose.yml down

docker-logs: ## Show Docker service logs
	docker compose -f docker/docker-compose.yml logs -f

docker-build: ## Build Docker images
	docker compose -f docker/docker-compose.yml build

# LLM commands
benchmark-llm: ## Run LLM provider benchmark comparison
	@echo "Running LLM provider benchmarks..."
	@echo "This would run accuracy benchmarks across all configured providers"
	# TODO: Implement benchmark script

# Cleanup commands
clean: ## Clean up development environment
	$(MAKE) docker-down
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name node_modules -exec rm -rf {} +
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete

# Utility commands
check-health: ## Check health of all services
	@echo "Checking API health..."
	curl -f http://localhost:8000/api/v1/health || echo "API not responding"
	@echo "Checking database..."
	docker compose -f docker/docker-compose.yml exec db pg_isready -U forgex || echo "Database not responding"
	@echo "Checking Redis..."
	docker compose -f docker/docker-compose.yml exec redis redis-cli ping || echo "Redis not responding"