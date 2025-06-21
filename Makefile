# GitHub Talent Intelligence Platform Makefile

.PHONY: help install test lint format clean build release

help: ## Show this help message
	@echo "Robot Recruiter Development Commands"
	@echo "===================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt
	pip install -e .[dev]

test: ## Run tests
	pytest tests/ -v --cov=src --cov-report=term-missing

test-watch: ## Run tests in watch mode
	pytest tests/ -v --cov=src --cov-report=term-missing -f

lint: ## Run linting checks
	flake8 src/ tests/
	black --check src/ tests/
	isort --check-only src/ tests/

format: ## Format code
	black src/ tests/
	isort src/ tests/

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build: ## Build package
	python -m build

release: ## Create a new release (requires version bump)
	@echo "Creating release..."
	git tag -a v$(shell python -c "import src.github_talent_intelligence; print(src.github_talent_intelligence.__version__)") -m "Release v$(shell python -c "import src.github_talent_intelligence; print(src.github_talent_intelligence.__version__)")"
	git push --tags

security: ## Run security checks
	bandit -r src/
	safety check

ci: lint test security ## Run all CI checks

dev-setup: install ## Set up development environment
	@echo "Development environment setup complete!"
	@echo "Run 'make test' to verify everything works."
