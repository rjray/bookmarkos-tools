# Makefile for BookmarkOS Tools testing and development

# Executable Python scripts that don't end in .py
EXE_SCRIPTS = bin/bookmarks2json bin/bookmarks_report bin/restore_bookmarks

.PHONY: help test test-unit test-integration test-all coverage lint clean install-test-deps

help:  ## Show this help message
	@echo 'BookmarkOS Tools Development Commands:'
	@echo
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install-test-deps:  ## Install testing dependencies
	pip install -r requirements-test.txt

test: test-unit  ## Run unit tests (default)

test-unit:  ## Run unit tests only
	pytest tests/unit/ -v

test-integration:  ## Run integration tests only
	pytest tests/integration/ -v

test-all:  ## Run all tests (unit + integration)
	pytest tests/ -v

test-fast:  ## Run tests without coverage (faster)
	pytest tests/ -v --no-cov

test-parallel:  ## Run tests in parallel (requires pytest-xdist)
	pytest tests/ -v -n auto

coverage:  ## Generate detailed coverage report
	pytest tests/ --cov=bin/bookmarkos --cov-report=html --cov-report=term-missing

coverage-xml:  ## Generate XML coverage report (for CI)
	pytest tests/ --cov=bin/bookmarkos --cov-report=xml

lint:  ## Run linting (if available)
	pylint --max-line-length=80 $(EXE_SCRIPTS) bin/bookmarkos

clean:  ## Clean up test artifacts
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete

test-watch:  ## Run tests continuously (requires pytest-watch if installed)
	@command -v ptw >/dev/null 2>&1 && ptw tests/ || echo "Install pytest-watch: pip install pytest-watch"

benchmark:  ## Run performance benchmarks
	pytest tests/ -v -m benchmark --benchmark-only

test-parser:  ## Run parser-specific tests
	pytest tests/ -v -m parser

test-metrics:  ## Run metrics-specific tests
	pytest tests/ -v -m metrics

test-io:  ## Run I/O-specific tests
	pytest tests/ -v -m io

test-cli:  ## Run CLI tool tests
	pytest tests/ -v -m cli

# Development helpers
dev-setup:  ## Set up development environment
	pip install -r requirements-test.txt
	@echo "Development environment ready!"

test-verbose:  ## Run tests with maximum verbosity
	pytest tests/ -vvv --tb=long

test-debug:  ## Run tests with debugging enabled
	pytest tests/ -v --pdb --pdbcls=IPython.terminal.debugger:TerminalPdb
