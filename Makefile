# GitHub Talent Intelligence Platform Makefile

.PHONY: help install test test-unit test-integration test-all clean lint format docs

help: ## Show this help message
	@echo "Robot Recruiter - Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

test-unit: ## Run unit tests (SQLite, fast)
	pytest -m "unit and not slow" -v

test-integration: ## Run integration tests (PostgreSQL)
	pytest -m "integration and not slow" -v

test-all: ## Run all tests (both SQLite and PostgreSQL)
	pytest -m "not slow" -v

test-sqlite: ## Run tests with SQLite only
	pytest -m "sqlite and not slow" -v

test-postgresql: ## Run tests with PostgreSQL only
	pytest -m "postgresql and not slow" -v

test-slow: ## Run slow tests
	pytest -m "slow" -v

test-api: ## Run API tests
	pytest -m "api" -v

test-cli: ## Run CLI tests
	pytest -m "cli" -v

test-db: ## Run database tests
	pytest -m "db" -v

test: test-unit ## Default test target (unit tests only)

clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/

lint: ## Run linting
	flake8 src/ tests/
	pylint src/ tests/

format: ## Format code
	black src/ tests/
	isort src/ tests/

docs: ## Generate documentation
	python -m pydoc -w src/github_talent_intelligence/

# Database management
db-init: ## Initialize database
	python -m src.github_talent_intelligence.cli init-db

db-migrate: ## Run database migrations
	alembic upgrade head

db-reset: ## Reset database (drop and recreate)
	alembic downgrade base
	alembic upgrade head

# Development helpers
dev-setup: install db-init ## Setup development environment
	@echo "Development environment setup complete!"

dev-test: test-unit test-integration ## Run development test suite

# CI/CD helpers
ci-test: ## Run tests for CI/CD (all tests except slow)
	pytest -m "not slow" --cov=src --cov-report=xml --cov-report=html

# Quick commands
quick-test: test-unit ## Quick test run (unit tests only)
full-test: test-all ## Full test run (all tests)
