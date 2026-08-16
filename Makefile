# VESTIGIUM — Development Makefile
# =========================================
# Common development tasks for the OSINT investigation platform.

.PHONY: help install dev backend frontend build test lint clean docker-up docker-down migrate

# Default target
help: ## Show this help message
	@echo "VESTIGIUM — Available Commands"
	@echo "======================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---- Installation ----
install: ## Install all dependencies (backend + frontend)
	cd backend && pip install -e ".[dev]"
	cd frontend && npm install

install-backend: ## Install backend dependencies only
	cd backend && pip install -e ".[dev]"

install-frontend: ## Install frontend dependencies only
	cd frontend && npm install

# ---- Development ----
dev: ## Start both backend and frontend dev servers
	@echo "Starting VESTIGIUM in development mode..."
	@echo "Backend:  http://localhost:8000"
	@echo "Frontend: http://localhost:5173"
	@echo "API Docs: http://localhost:8000/api/docs"
	@make -j2 backend frontend

backend: ## Start backend dev server
	cd backend && uvicorn app.main:create_app --factory --reload --host 0.0.0.0 --port 8000

frontend: ## Start frontend dev server
	cd frontend && npm run dev

# ---- Build ----
build: build-backend build-frontend ## Build both backend and frontend

build-backend: ## Build backend package
	cd backend && pip install -e .

build-frontend: ## Build frontend for production
	cd frontend && npm run build

# ---- Database ----
migrate: ## Run database migrations
	cd backend && alembic upgrade head

migrate-new: ## Create a new migration (usage: make migrate-new MSG="add foo table")
	cd backend && alembic revision --autogenerate -m "$(MSG)"

migrate-down: ## Downgrade one migration
	cd backend && alembic downgrade -1

db-reset: ## Reset database (WARNING: destroys all data)
	rm -f backend/data/vestigium.db
	cd backend && alembic upgrade head

# ---- Testing ----
test: ## Run all tests
	cd backend && pytest -v --tb=short
	cd frontend && npm test 2>/dev/null || echo "No frontend tests configured yet"

test-backend: ## Run backend tests only
	cd backend && pytest -v --tb=short

test-cov: ## Run tests with coverage report
	cd backend && pytest --cov=app --cov-report=html --cov-report=term-missing

# ---- Linting ----
lint: ## Run linters on both codebases
	cd backend && ruff check app/ && ruff format --check app/
	cd frontend && npx tsc --noEmit

lint-fix: ## Auto-fix lint issues
	cd backend && ruff check --fix app/ && ruff format app/

# ---- Docker ----
docker-up: ## Start all services with Docker Compose
	docker compose up -d --build

docker-up-full: ## Start with PostgreSQL and Redis
	docker compose --profile with-postgres --profile with-redis up -d --build

docker-down: ## Stop all Docker services
	docker compose down

docker-logs: ## Follow Docker logs
	docker compose logs -f

# ---- Cleanup ----
clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf frontend/dist frontend/node_modules/.vite
	rm -rf backend/htmlcov backend/.coverage
	@echo "Cleaned."
