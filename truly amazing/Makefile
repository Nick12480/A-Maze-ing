NAME := A_Maze_ing/a_maze_ing.py
PYTHON ?= python3
CONFIG ?= config.txt
OUTPUT ?= output_maze.txt
FLAKE8 := uv run -m flake8
FLAKE8_FLAGS := --count --show-source --filename [./*.py]
MYPY := uv run mypy
MYPY_FLAGS := --warn-return-any \
			  --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs \
			  --check-untyped-defs
UV_VENV := python -m uv sync

all: install run

install:
	$(UV_VENV)

run:
	$(PYTHON) -m uv run $(NAME) $(CONFIG) --interactive

# test:
# 	$(PYTHON) -m unittest discover -s tests -v

validate:
	$(PYTHON) output_validator.py $(OUTPUT)

lint:
	$(FLAKE8) $(FLAKE8_FLAGS) .
	$(MYPY) . $(MYPY_FLAGS)

lint-strict:
	$(FLAKE8) $(FLAKE8_FLAGS) .
	$(MYPY) . --strict

clean:
	rm -rf .mypy_cache .pytest_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

.PHONY: all install run test lint validate clean
