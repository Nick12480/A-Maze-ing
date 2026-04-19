NAME := A-Maze-ing/a_maze_ing.py
FLAKE8 := uv run -m flake8
FLAKE8_FLAGS := --count --show-source --filename [./*.py]
MYPY := uv run mypy
MYPY_FLAGS := --warn-return-any \
			  --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs \
			  --check-untyped-defs
UV_VENV := python -m uv sync
FILE := A-Maze-ing/config.txt
OUT := output_maze.txt


install:
	$(UV_VENV)

run:
	python -m uv run $(NAME) $(FILE)

debug:
	
validate:
	python -m uv run output_validator.py $(OUT)

clean:
	rm -rf __pycache__ .mypy_cache

lint:
	$(FLAKE8) $(FLAKE8_FLAGS) .
	$(MYPY) . $(MYPY_FLAGS)

lint-strict:
	$(FLAKE8) $(FLAKE8_FLAGS) .
	$(MYPY) . --strict