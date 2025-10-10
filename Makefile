.PHONY: init help dev prod down pre-commit-install pre-commit-run pre-commit-update

# Default target
help:
	@echo "Available commands:"
	@echo "  make init    - Project initialization (.env and config setup)"
	@echo "  make dev     - Starts the development environment"
	@echo "  make prod    - Starts the production environment"
	@echo "  make down    - Stops all services and cleans up"
	@echo "  make pre-commit-install  - Install pre-commit hooks"
	@echo "  make pre-commit-run      - Run pre-commit on all files"
	@echo "  make pre-commit-update   - Update pre-commit hooks"
	@echo "  make help    - Show this help message"

# Project initialization
init:
	@echo "🚀 Project initialization..."
	@chmod +x scripts/init.sh
	@./scripts/init.sh

# Development environment
dev:
	@echo "✨ Starting development environment..."
	@docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
	@echo "Installing/updating frontend dependencies..."
	@npm -C frontend install
	@echo "Starting frontend dev server..."
	@npm -C frontend run dev

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