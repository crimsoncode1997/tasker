.PHONY: help start stop build test lint clean migrate seed

# Default target
help:
	@echo "Available commands:"
	@echo "  start     - Start development environment"
	@echo "  stop      - Stop development environment"
	@echo "  build     - Build production images"
	@echo "  test      - Run all tests"
	@echo "  lint      - Run linters"
	@echo "  clean     - Clean up containers and volumes"
	@echo "  migrate   - Run database migrations"
	@echo "  seed      - Seed database with sample data"
	@echo "  logs      - Show logs from all services"

# Development
start:
	docker-compose -f docker-compose.dev.yml up --build

start-detached:
	docker-compose -f docker-compose.dev.yml up --build -d

stop:
	docker-compose -f docker-compose.dev.yml down

# Database
migrate:
	docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head

migrate-create:
	docker-compose -f docker-compose.dev.yml exec backend alembic revision --autogenerate -m "$(message)"

seed:
	docker-compose -f docker-compose.dev.yml exec backend python -m app.scripts.seed_data

# Testing
test:
	docker-compose -f docker-compose.dev.yml exec backend pytest
	docker-compose -f docker-compose.dev.yml exec frontend npm test

test-backend:
	docker-compose -f docker-compose.dev.yml exec backend pytest

test-frontend:
	docker-compose -f docker-compose.dev.yml exec frontend npm test

test-e2e:
	docker-compose -f docker-compose.dev.yml exec frontend npm run test:e2e

# Linting
lint:
	docker-compose -f docker-compose.dev.yml exec backend black . && docker-compose -f docker-compose.dev.yml exec backend isort . && docker-compose -f docker-compose.dev.yml exec backend flake8
	docker-compose -f docker-compose.dev.yml exec frontend npm run lint

lint-backend:
	docker-compose -f docker-compose.dev.yml exec backend black . && docker-compose -f docker-compose.dev.yml exec backend isort . && docker-compose -f docker-compose.dev.yml exec backend flake8

lint-frontend:
	docker-compose -f docker-compose.dev.yml exec frontend npm run lint

# Production
build:
	docker-compose -f docker-compose.prod.yml build

deploy:
	docker-compose -f docker-compose.prod.yml up -d

# Utilities
logs:
	docker-compose -f docker-compose.dev.yml logs -f

logs-backend:
	docker-compose -f docker-compose.dev.yml logs -f backend

logs-frontend:
	docker-compose -f docker-compose.dev.yml logs -f frontend

clean:
	docker-compose -f docker-compose.dev.yml down -v
	docker system prune -f

# Development shortcuts
shell-backend:
	docker-compose -f docker-compose.dev.yml exec backend bash

shell-frontend:
	docker-compose -f docker-compose.dev.yml exec frontend bash

shell-db:
	docker-compose -f docker-compose.dev.yml exec postgres psql -U tasker -d tasker_db

