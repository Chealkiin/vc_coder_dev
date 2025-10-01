# Developer convenience targets for Coding Agents repo
# Usage: run `make <target>` from the repository root.

PYTHON ?= python3
VENV ?= .venv
VENV_BIN := $(VENV)/bin

ifeq ($(OS),Windows_NT)
    ACTIVATE = $(VENV)\Scripts\activate
    PYTHON_BIN = $(VENV)\Scripts\python.exe
    PIP_BIN = $(VENV)\Scripts\pip.exe
else
    ACTIVATE = source $(VENV_BIN)/activate
    PYTHON_BIN = $(VENV_BIN)/python
    PIP_BIN = $(VENV_BIN)/pip
endif

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  make bootstrap   # Create venv and install dependencies"
	@echo "  make demo        # Run the happy-path demo pipeline"
	@echo "  make export-demo # Run demo and export artifacts to demo_run/"
	@echo "  make test        # Run pytest test suite"
	@echo "  make lint        # Run Ruff lint checks"
	@echo "  make format      # Run Black and isort formatters"

.PHONY: bootstrap
bootstrap: $(VENV)/.completed

$(VENV)/.completed:
	$(PYTHON) -m venv $(VENV)
	$(PYTHON_BIN) -m pip install --upgrade pip
	$(PYTHON_BIN) -m pip install -e .[dev]
	@touch $(VENV)/.completed

.PHONY: demo
demo: bootstrap
	$(PYTHON_BIN) scripts/demo_happy_path.py

.PHONY: export-demo
export-demo: bootstrap
	$(PYTHON_BIN) scripts/export_demo_run.py --output demo_run

.PHONY: test
test: bootstrap
	$(PYTHON_BIN) -m pytest

.PHONY: lint
lint: bootstrap
	$(PYTHON_BIN) -m ruff check backend core scripts tests

.PHONY: format
format: bootstrap
	$(PYTHON_BIN) -m black backend core scripts tests
	$(PYTHON_BIN) -m isort backend core scripts tests
