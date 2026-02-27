SHELL := /bin/sh

# ====== Config ======
PY ?= python3
VENV_DIR ?= .venv
PIP := $(VENV_DIR)/bin/pip
PYTHON := $(VENV_DIR)/bin/python
FLAKE8 := $(VENV_DIR)/bin/flake8
MYPY := $(VENV_DIR)/bin/mypy

CONFIG ?= config_default.txt

EXCLUDES := .venv,__pycache__,.mypy_cache,.pytest_cache,build,dist
MYPY_FLAGS := --warn-return-any \
	--warn-unused-ignores \
	--ignore-missing-imports \
	--disallow-untyped-defs \
	--check-untyped-defs

# ====== UX helpers ======
OK    = \033[0;32m✓\033[0m
WARN  = \033[0;33m!\033[0m
INFO  = \033[0;34m>\033[0m
ERR   = \033[0;31m✗\033[0m

.PHONY: help venv install run debug lint typecheck clean distclean build nuke

help:
	@printf "Targets:\n"
	@printf "  venv       Create virtualenv in $(VENV_DIR)\n"
	@printf "  install    Install deps (requirements*.txt)\n"
	@printf "  run        Run: a_maze_ing.py $(CONFIG)\n"
	@printf "  debug      Run with pdb\n"
	@printf "  lint       Run flake8 + mypy (subject flags)\n"
	@printf "  typecheck  Run mypy (default)\n"
	@printf "  clean      Remove caches/build artifacts\n"
	@printf "  distclean  clean + remove $(VENV_DIR)\n"
	@printf "  build      Build pip package (mazegen-*)\n"

venv:
	@printf "$(INFO) Creating virtualenv in '$(VENV_DIR)'\n"
	@$(PY) -m venv $(VENV_DIR)
	@printf "$(INFO) Upgrading pip/setuptools/wheel\n"
	@$(PIP) install --upgrade pip setuptools wheel >/dev/null
	@printf "$(OK) Virtualenv ready\n"

install: venv
	@printf "$(INFO) Installing dependencies (if files exist)\n"
	@if [ -f requirements.txt ]; then \
		printf "$(INFO) - requirements.txt\n"; \
		$(PIP) install -r requirements.txt >/dev/null; \
	else \
		printf "$(WARN) requirements.txt not found (skipping)\n"; \
	fi
	@if [ -f requirements-dev.txt ]; then \
		printf "$(INFO) - requirements-dev.txt\n"; \
		$(PIP) install -r requirements-dev.txt >/dev/null; \
	else \
		printf "$(INFO) requirements-dev.txt not found (skipping)\n"; \
	fi
	@printf "$(OK) Dependencies installed\n"

run: install
	@printf "$(INFO) Running: $(PYTHON) a_maze_ing.py $(CONFIG)\n"
	@$(PYTHON) a_maze_ing.py $(CONFIG)

debug: install
	@printf "$(INFO) Debugging with pdb: $(PYTHON) -m pdb a_maze_ing.py $(CONFIG)\n"
	@$(PYTHON) -m pdb a_maze_ing.py $(CONFIG)

lint: install
	@printf "$(INFO) flake8 (excluding: $(EXCLUDES))\n"
	@$(FLAKE8) . --exclude $(EXCLUDES) || ( \
		printf "$(ERR) flake8 failed. Tip: check tabs vs spaces + line length.\n"; \
		exit 1 )
	@printf "$(OK) flake8 passed\n"
	@printf "$(INFO) mypy (subject flags)\n"
	@$(MYPY) . $(MYPY_FLAGS) || ( \
		printf "$(ERR) mypy failed. Tip: add type hints or adjust annotations.\n"; \
		exit 1 )
	@printf "$(OK) mypy passed\n"
	@printf "$(OK) Lint OK\n"

typecheck: install
	@printf "$(INFO) mypy (default)\n"
	@$(MYPY) . || ( \
		printf "$(ERR) mypy failed.\n"; \
		exit 1 )
	@printf "$(OK) typecheck OK\n"

clean:
	@printf "$(INFO) Cleaning caches and build artifacts\n"
	@find . -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .mypy_cache .pytest_cache .ruff_cache 2>/dev/null || true
	@rm -rf dist build *.egg-info 2>/dev/null || true
	@rm -rf out 2>/dev/null || true
	@printf "$(OK) Clean done\n"

distclean: clean
	@printf "$(INFO) Removing virtualenv: $(VENV_DIR)\n"
	@rm -rf $(VENV_DIR)
	@printf "$(OK) distclean done\n"

build: install
	@printf "$(INFO) Building package (python -m build)\n"
	@$(PYTHON) -m build || ( \
		printf "$(ERR) build failed. Tip: check pyproject.toml and that mazegen.py exists at repo root.\n"; \
		exit 1 )
	@printf "$(OK) Build done. Check dist/\n"

nuke: distclean
	@printf "$(WARN) Removing EVERYTHING generated (builds, caches, outputs, logs)\n"
	@rm -rf dist build *.egg-info 2>/dev/null || true
	@rm -rf .mypy_cache .pytest_cache .ruff_cache 2>/dev/null || true
	@find . -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
	@rm -rf out 2>/dev/null || true
	@rm -f maze.txt *.log 2>/dev/null || true
	@printf "$(OK) Nuke complete (repo back to clean state)\n"
