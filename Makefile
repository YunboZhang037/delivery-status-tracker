SHELL := /bin/bash
.PHONY: dev setup test seed help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

dev: ## Start all services (PostgreSQL + backend + frontend)
	@bash scripts/dev.sh

setup: ## Install dependencies and seed database
	cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
	cd frontend && npm install
	@echo "Creating database 'delivery_tracker' (if not exists)..."
	@psql -h localhost -p 5432 -U postgres -lqt 2>/dev/null | grep -qw delivery_tracker || \
		createdb -h localhost -p 5432 -U postgres delivery_tracker || \
		(echo "  Could not create database. Ensure PostgreSQL is running on :5432." && exit 1)
	cd backend && source .venv/bin/activate && python -m app.seed
	@echo ""
	@echo "Setup complete! Run 'make dev' to start."

test: ## Run backend test suite
	cd backend && source .venv/bin/activate && python -m pytest tests/ -v

seed: ## Re-seed database from CSV (idempotent)
	cd backend && source .venv/bin/activate && python -m app.seed
