# GitHub Talent Intelligence Platform Makefile

.PHONY: install test lint format docs clean

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/
	isort src/ tests/

docs:
	cd docs && make html

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

setup:
	python talent_analyzer.py setup

analyze-example:
	python talent_analyzer.py analyze --org ChainSafe --output results

run-example:
	python examples/ai_recruiting_integration.py
