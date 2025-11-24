# Makefile for Browser Isolation System
# Common development tasks and commands

.PHONY: help install install-dev setup test test-cov lint format clean docker-build docker-up docker-down run-api run-dashboard run-cli docs security

# Default target
.DEFAULT_GOAL := help

# Python interpreter
PYTHON := python3
PIP := $(PYTHON) -m pip
COMPOSE ?= docker compose

# Project directories
SRC_DIRS := engine api client cli headless logging_mod reporting
TEST_DIR := tests

##@ Help

help: ## Display this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\n\033[1m\033[36mBrowser Isolation System - Makefile\033[0m\n\n\033[1mUsage:\033[0m\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Installation

install: ## Install production dependencies
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	playwright install chromium

install-dev: install ## Install development dependencies
	$(PIP) install -r requirements-dev.txt
	pre-commit install

setup: install-dev ## Complete setup (install + configure)
	mkdir -p logs reports
	@echo "✅ Setup complete! Run 'make test' to verify."

##@ Development

run-api: ## Start the API server
	$(PYTHON) api/server.py

run-dashboard: ## Start the Streamlit dashboard
	streamlit run client/safe_viewer.py

run-cli: ## Show CLI help
	$(PYTHON) cli/isolationctl.py --help

##@ Testing

test: ## Run all tests
	pytest $(TEST_DIR)/ -v

test-cov: ## Run tests with coverage report
	pytest $(TEST_DIR)/ -v --cov=$(SRC_DIRS) --cov-report=html --cov-report=term

test-unit: ## Run unit tests only
	pytest $(TEST_DIR)/ -v -m unit

test-integration: ## Run integration tests only
	pytest $(TEST_DIR)/ -v -m integration

test-security: ## Run security-focused tests
	pytest $(TEST_DIR)/ -v -m security

test-watch: ## Run tests in watch mode
	pytest-watch -- $(TEST_DIR)/ -v

##@ Code Quality

lint: ## Run all linters
	@echo "🔍 Running Black..."
	black --check $(SRC_DIRS) $(TEST_DIR)
	@echo "🔍 Running isort..."
	isort --check-only $(SRC_DIRS) $(TEST_DIR)
	@echo "🔍 Running Flake8..."
	flake8 $(SRC_DIRS) $(TEST_DIR)
	@echo "✅ All linting passed!"

format: ## Format code with Black and isort
	@echo "✨ Formatting with Black..."
	black $(SRC_DIRS) $(TEST_DIR)
	@echo "✨ Sorting imports with isort..."
	isort $(SRC_DIRS) $(TEST_DIR)
	@echo "✅ Code formatted!"

typecheck: ## Run type checking with MyPy
	mypy $(SRC_DIRS) --ignore-missing-imports

##@ Security

security: ## Run security checks
	@echo "🔒 Running Bandit..."
	bandit -r $(SRC_DIRS) -c .bandit.yml
	@echo "🔒 Running Safety..."
	safety check --json
	@echo "✅ Security checks complete!"

security-audit: ## Comprehensive security audit
	@echo "🔍 Full security audit..."
	bandit -r . -f json -o reports/bandit-report.json
	safety check --json > reports/safety-report.json || true
	@echo "✅ Reports saved to reports/"

##@ Docker

docker-build: ## Build Docker images
	$(COMPOSE) build

docker-up: ## Start Docker containers
	$(COMPOSE) up -d

docker-down: ## Stop Docker containers
	$(COMPOSE) down

docker-logs: ## Show Docker logs
	$(COMPOSE) logs -f

docker-clean: ## Remove Docker containers and volumes
	$(COMPOSE) down -v
	docker system prune -f

docker-test: ## Run tests in Docker
	$(COMPOSE) run --rm api pytest tests/ -v

##@ Documentation

docs: ## Generate documentation
	@echo "📚 Generating documentation..."
	@echo "✅ See README.md, ARCHITECTURE.md, and other docs!"

docs-serve: ## Serve documentation locally
	@echo "📚 Documentation available at:"
	@echo "  README.md - Main documentation"
	@echo "  ARCHITECTURE.md - Technical architecture"
	@echo "  QUICKSTART.md - Quick start guide"
	@echo "  API docs: http://localhost:8000/docs (run 'make run-api')"

##@ Utilities

clean: ## Clean generated files and caches
	@echo "🧹 Cleaning..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf htmlcov/ .coverage coverage.xml
	rm -rf dist/ build/
	rm -rf logs/*.log
	@echo "✅ Cleaned!"

clean-all: clean docker-clean ## Deep clean (including Docker)
	rm -rf venv/ env/ .venv/
	@echo "✅ Deep clean complete!"

render: ## Quick test: render example.com
	$(PYTHON) cli/isolationctl.py render https://example.com

stats: ## Show isolation statistics
	$(PYTHON) cli/isolationctl.py stats

##@ Release

build: clean ## Build distribution packages
	$(PYTHON) -m build

release-check: ## Check if ready for release
	@echo "🔍 Pre-release checks..."
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) security
	@echo "✅ Ready for release!"

version: ## Show current version
	@grep "version=" setup.py | cut -d'"' -f2

##@ Quick Actions

quick-test: ## Quick smoke test
	@echo "🚀 Quick smoke test..."
	$(PYTHON) -c "import engine, api, client; print('✅ Imports OK')"
	pytest $(TEST_DIR)/test_dom_sanitizer.py::TestDOMSanitizer::test_remove_script_tags -v
	@echo "✅ Quick test passed!"

dev: install-dev ## Setup and start development environment
	@echo "🚀 Starting development environment..."
	@echo "1. API will start on http://localhost:8000"
	@echo "2. Dashboard will start on localhost:8501"
	@$(MAKE) run-api &
	@sleep 3
	@$(MAKE) run-dashboard

all: clean install-dev lint test security ## Run everything
	@echo "✅ All tasks completed successfully!"

##@ Examples

example-safe: ## Test with safe page
	$(PYTHON) cli/isolationctl.py render file://$(PWD)/examples/safe_page.html

example-dangerous: ## Test with dangerous page
	$(PYTHON) cli/isolationctl.py render file://$(PWD)/examples/dangerous_page.html --report dangerous-report.md

example-report: ## Generate example report
	$(PYTHON) cli/isolationctl.py report --format markdown --output example-report.md

