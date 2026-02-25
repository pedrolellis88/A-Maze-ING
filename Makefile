SHELL := /bin/sh

PY ?= python3
VENV_DIR ?= .venv
PIP := $(VENV_DIR)/bin/pip
PYTHON := $(VENV_DIR)/bin/python

CONFIG ?= config_default.txt

.PHONY: help venv install run debug lint typecheck clean distclean build

help:
	@printf "Targets:\n"
	@printf "  venv       Create virtualenv in .venv\n"
	@printf "  install    Install deps (requirements*.txt)\n"
	@printf "  run        Run: a_maze_ing.py $(CONFIG)\n"
	@printf "  debug      Run with pdb\n"
	@printf "  lint       Run flake8\n"
	@printf "  typecheck  Run mypy\n"
	@printf "  clean      Remove caches/build artifacts\n"
	@printf "  distclean  clean + remove .venv\n"
	@printf "  build      Build pip package (mazegen-*)\n"

venv:
	$(PY) -m venv $(VENV_DIR)
	$(PIP) install --upgrade pip setuptools wheel

install: venv
	@if [ -f requirements.txt ]; then $(PIP) install -r requirements.txt; fi
	@if [ -f requirements-dev.txt ]; then $(PIP) install -r requirements-dev.txt; fi

run: install
	$(PYTHON) a_maze_ing.py $(CONFIG)

debug: install
	$(PYTHON) -m pdb a_maze_ing.py $(CONFIG)

lint: install
	$(VENV_DIR)/bin/flake8 .
	$(VENV_DIR)/bin/mypy . \
		--warn-return-any \
		--warn-unused-ignores \
		--ignore-missing-imports \
		--disallow-untyped-defs \
		--check-untyped-defs

typecheck: install
	$(VENV_DIR)/bin/mypy .

clean:
	@find . -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .mypy_cache .pytest_cache .ruff_cache 2>/dev/null || true
	@rm -rf dist build *.egg-info 2>/dev/null || true
	@rm -rf out 2>/dev/null || true

distclean: clean
	@rm -rf $(VENV_DIR)

build: install
	$(PYTHON) -m build
