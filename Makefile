.PHONY: init help dev prod down pre-commit-install pre-commit-run pre-commit-update
.PHONY: domain migrate migrate-create

ENV_FILE ?= .env
ENV_ABS := $(abspath $(ENV_FILE))
COMPOSE ?= docker-compose
COMPOSE_BASE := $(COMPOSE) --env-file "$(ENV_ABS)" -f docker-compose.yml
COMPOSE_DEV := $(COMPOSE) --env-file "$(ENV_ABS)" -f docker-compose.yml -f docker-compose.dev.yml

# Default target
help:
	@echo "Available commands:"
	@echo "  make init    - Project initialization (.env and config setup)"
	@echo "  make dev     - Starts the development environment (docker-compose)"
	@echo "  make prod    - Starts the production environment (docker-compose)"
	@echo "  make down    - Stops all services and cleans up"
	@echo "  make domain  - Configure DOMAIN / BACKEND_PORT / webhook mode"
	@echo "  make migrate - Apply database migrations (alembic upgrade head)"
	@echo "  make migrate-create NAME=descr - Generate new migration"
	@echo "      (set ENV_FILE=/path/to/.env if your env lives elsewhere)"
	@echo "  make pre-commit-install  - Install pre-commit hooks"
	@echo "  make pre-commit-run      - Run pre-commit on all files"
	@echo "  make pre-commit-update   - Update pre-commit hooks"
	@echo "  make help    - Show this help message"

# Project initialization
init:
	@echo "🚀 Project initialization..."
	@chmod +x scripts/init.sh
	@./scripts/init.sh

domain:
	@if [ -z "$(DOMAIN)" ] && [ -z "$(PORT)" ] && [ -z "$(WEBHOOK)" ]; then \
		echo "Usage: make domain DOMAIN=bot.example.com [PORT=8080] [WEBHOOK=on|off|keep]"; \
		exit 1; \
	fi
	@CMD="python scripts/configure_domain.py"; \
	if [ -n "$(DOMAIN)" ]; then CMD="$$CMD --domain $(DOMAIN)"; fi; \
	if [ -n "$(PORT)" ]; then CMD="$$CMD --port $(PORT)"; fi; \
	if [ -n "$(WEBHOOK)" ]; then CMD="$$CMD --webhook $(WEBHOOK)"; fi; \
	echo ">> $$CMD"; \
	$$CMD

migrate:
	@echo "⚙️  Applying migrations..."
	@docker compose exec -T backend python -m alembic upgrade head

migrate-create:
	@if [ -z "$(NAME)" ]; then \
		echo "Usage: make migrate-create NAME=description"; \
		exit 1; \
	fi
	@echo "🧩 Generating migration: $(NAME)"
	@if [ ! -f "$(ENV_ABS)" ]; then \
		echo "Environment file not found: $(ENV_ABS)"; \
		echo "Set ENV_FILE=/path/to/.env or run make init"; \
		exit 1; \
	fi
	@$(COMPOSE_DEV) run --rm backend uv run alembic revision --autogenerate -m "$(NAME)"

# Development environment
dev:
	@echo "✨ Starting development environment..."
	@docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

# Production environment
prod:
	@echo "🚀 Starting production environment..."
	@docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Stop and clean up
down:
	@echo "- Stopping all services and cleaning up..."
	@-docker-compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.dev.yml down --remove-orphans

# Pre-commit hooks
pre-commit-install:
	@echo "🔧 Installing pre-commit hooks..."
	@uv run pre-commit install

pre-commit-run:
	@echo "🔍 Running pre-commit on all files..."
	@uv run pre-commit run --all-files

pre-commit-update:
	@echo "🔄 Updating pre-commit hooks..."
	@uv run pre-commit autoupdate
