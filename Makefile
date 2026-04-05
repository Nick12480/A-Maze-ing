NAME := a_maze_ing.py
FLAKE8 := uv run -m flake8
FLAKE8_FLAGS := --count --show-source --filename [./*.py]
MYPY := uv run mypy
MYPY_FLAGS := --warn-return-any \
			  --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs \
			  --check-untyped-defs
UV_VENV := uv sync


install:
	$(UV_VENV)

run:
	uv run $(NAME)

debug:
	

clean:
	rm -rf __pycache__ .mypy_cache

lint:
	$(FLAKE8) $(FLAKE8_FLAGS) .
	$(MYPY) . $(MYPY_FLAGS)

lint-strict:
	$(FLAKE8) $(FLAKE8_FLAGS) .
	$(MYPY) . --strict