.PHONY: venv install lint format typecheck complexity test test-unit test-integration test-contract \
        coverage ci version-bump docs docs-serve help

VENV = .venv/bin
PYTHON ?= python

# Setup
venv:
	python -m venv .venv

install:
	$(VENV)/pip install -e ".[dev]"

# Quality
lint:
	$(VENV)/ruff check .

format:
	$(VENV)/ruff format .

typecheck:
	$(VENV)/pyright

complexity:
	@echo "=== Cyclomatic Complexity (C+ rated functions) ==="
	@$(VENV)/radon cc src/unifi_topology -a -nc -s
	@echo ""
	@echo "=== Maintainability Index (B or lower) ==="
	@$(VENV)/radon mi src/unifi_topology -s -nb
	@echo ""
	@echo "=== Threshold Checks (max function: 12, max module avg: B, overall avg: A) ==="
	$(VENV)/xenon src/unifi_topology --max-absolute C --max-modules B --max-average A
	@./scripts/check_complexity.sh 12

# Testing
test:
	$(VENV)/pytest

test-unit:
	$(VENV)/pytest -m unit

test-integration:
	$(VENV)/pytest -m integration

test-contract:
	$(VENV)/pytest -m contract

coverage:
	$(VENV)/pytest --cov=unifi_topology --cov-report=term-missing

# CI
ci:
	@echo "=== Lint ==="
	$(VENV)/ruff check .
	@echo ""
	@echo "=== Format Check ==="
	$(VENV)/ruff format --check .
	@echo ""
	@echo "=== Typecheck ==="
	$(VENV)/pyright
	@echo ""
	@echo "=== Complexity ==="
	$(VENV)/xenon src/unifi_topology --max-absolute C --max-modules B --max-average A
	@./scripts/check_complexity.sh 12
	@echo ""
	@echo "=== Tests ==="
	$(VENV)/pytest -q
	@echo ""
	@echo "=== All checks passed ==="

# Docs
docs:
	$(VENV)/mkdocs build

docs-serve:
	$(VENV)/mkdocs serve

# Release
version-bump:
	@scripts/version_bump.sh

# Help
help:
	@echo "Available targets:"
	@echo "  venv        - Create virtual environment"
	@echo "  install     - Install package in editable mode with dev dependencies"
	@echo "  lint        - Run ruff linter"
	@echo "  format      - Run ruff formatter"
	@echo "  typecheck   - Run pyright type checker"
	@echo "  complexity  - Run complexity checks"
	@echo "  test        - Run all tests"
	@echo "  test-unit   - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-contract - Run contract tests only"
	@echo "  coverage    - Run tests with coverage report"
	@echo "  ci          - Run all CI checks"
	@echo "  docs        - Build documentation"
	@echo "  docs-serve  - Serve documentation locally"
	@echo "  version-bump - Bump version, commit, tag, and push"
