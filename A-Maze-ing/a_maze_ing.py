"""A-Maze-ing: Maze Generator.

Reads parameters from a config file, generates an animated ASCII maze
(Sidewinder or Placeholder algorithm) and solves it via BFS.
The '42' pattern is embedded as an impassable wall.
The result is saved as a hex output file.

Usage:
    python3 a_maze_ing.py config.txt

config.txt format (KEY=VALUE):
    WIDTH       -- Maze width in cells (int, > 1, default: 20)
    HEIGHT      -- Maze height in cells (int, > 1, default: WIDTH)
    WEIGHT      -- North-carve bias for Sidewinder (int >= 1, default: 2)
    SEED        -- Random seed (int, optional - random if omitted)
    ANIMATE     -- Enable animation ('true'/'false', default: true)
    ENTRY       -- Entry coordinates as 'col,row' (default: '0,0')
    EXIT        -- Exit coordinates as 'col,row' (default: WIDTH-1,HEIGHT-1)
    OUTPUT_FILE -- Output filename for hex representation (default: 'maze.txt')
    PERFECT     -- Generate a perfect maze ('true'/'false', default: true)
    ALGORITHM   -- 'sidewinder' or 'placeholder' (default: 'sidewinder')
"""

import os
import sys
import random
from typing_extensions import TypedDict

from pydantic import model_validator, ValidationError, Field, TypeAdapter, BaseModel

from algorithm import Maze
import algorithm as St


class Validation(BaseModel):
    HEIGHT: int = Field(..., ge=1)


def get_terminal_size(
    fallback_cols: int = 80, fallback_rows: int = 24
) -> tuple[int, int]:
    """Return the current terminal size with a fallback.

    Args:
        fallback_cols: Column count if detection fails.
        fallback_rows: Row count if detection fails.

    Returns:
        A ``(columns, rows)`` tuple.
    """
    try:
        size = os.get_terminal_size()
        return size.columns, size.lines
    except OSError:
        return fallback_cols, fallback_rows


def parse_config(filepath: str) -> dict:
    """Read a plain-text configuration file into a dictionary.

    Each valid line follows the format ``KEY=VALUE``.
    Empty lines and comments (``#``) are skipped.

    Args:
        filepath: Path to the configuration file.

    Returns:
        A dictionary with string keys and string values.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If a line contains no ``=`` character.
    """
    config: dict = {}
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' not in line:
                    raise ValueError(f"Invalid line: '{line}'")
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        raise
    except ValueError as e:
        print(f"Parse error: {e}")
        raise
    return config


def convert_config(config: dict) -> tuple:
    """Convert a raw config dictionary into typed parameters.

    All fields are optional and have sensible defaults.

    Args:
        config: String dictionary from :func:`parse_config`.

    Returns:
        A tuple ``(width, height, weight, seed, animate, entry,
        exit_coord, output_file, perfect, algorithm)`` with types:

        - **width** (*int*): Maze width in cells.
        - **height** (*int*): Maze height in cells.
        - **weight** (*int*): Bias weight for Sidewinder (>= 1).
        - **seed** (*int*): Random seed.
        - **animate** (*bool*): Animation enabled.
        - **entry** (*tuple[int, int]*): Entry as ``(col, row)``.
        - **exit_coord** (*tuple[int, int]*): Exit as ``(col, row)``.
        - **output_file** (*str*): Output file path.
        - **perfect** (*bool*): Perfect maze flag.
        - **algorithm** (*str*): Algorithm name.

    Raises:
        ValueError: If a value cannot be converted.
    """
    input: dict = {}

    try:
        input[St.WIDTH] = int(config.get('WIDTH', 20))
        input[St.HEIGHT] = int(config.get('HEIGHT', input[St.WIDTH]))
        input[St.WEIGHT] = max(1, int(config.get('WEIGHT', 2)))
        input[St.SEED] = (
            int(config['SEED'])
            if 'SEED' in config
            else random.randint(0, 0xFFFF_FFFF)
        )
        input[St.ANIMATE] = config.get('ANIMATE', 'true').lower() == 'true'
        input[St.ENTRY] = (
            tuple(map(int, config['ENTRY'].split(',')))
            if 'ENTRY' in config
            else (0, 0)
        )
        input[St.EXIT] = (
            tuple(map(int, config['EXIT'].split(',')))
            if 'EXIT' in config
            else (input[St.WIDTH] - 1, input[St.HEIGHT] - 1)
        )
        input[St.OUTPUT_FILE] = config.get('OUTPUT_FILE', 'output_maze.txt')
        input[St.PERFECT] = config.get('PERFECT', 'true').lower() == 'true'
        input[St.ALGORITHM] = config.get('ALGORITHM', 'sidewinder').lower()
    except ValueError as e:
        print(f"Type conversion error: {e}")
        raise
    return input


def validate_config(input: dict) -> None:
    """Validate maze dimensions and coordinates.

    Ensures the maze fits the terminal, both dimensions are at least 2,
    entry and exit are within the grid and are not identical.

    Args:
        width: Maze width in cells.
        height: Maze height in cells.
        entry: Entry as ``(col, row)``.
        exit_coord: Exit as ``(col, row)``.
        algorithm: Algorithm name ('sidewinder' or 'placeholder').

    Raises:
        ValueError: For each violated constraint with a clear message.
    """
    term_cols, term_rows = get_terminal_size()
    max_width = (term_cols - 1) // 2
    max_height = term_rows - 2

    valid_algorithms = ('sidewinder', 'placeholder')
    constraints = [
        (input[St.WIDTH] <= 1, "WIDTH must be greater than 1."),
        (input[St.HEIGHT] <= 1, "HEIGHT must be greater than 1."),
        (input[St.WIDTH] > max_width, f"WIDTH must be <= {max_width} (terminal\
         size)."),
        (input[St.HEIGHT] > max_height,
         f"HEIGHT must be <= {max_height} (terminal size)."),
        (input[St.ENTRY] == input[St.EXIT], "ENTRY and EXIT must not be\
         identical."),
        (input[St.ALGORITHM] not in valid_algorithms,
         "ALGORITHM must be 'sidewinder' or 'placeholder'."),
    ]
    for condition, msg in constraints:
        if condition:
            raise ValueError(msg)

    for label, coord in\
            [('ENTRY', input[St.ENTRY]), ('EXIT', input[St.ENTRY])]:
        col, row = coord
        if not (0 <= col < input[St.WIDTH] and 0 <= row < input[St.HEIGHT]):
            raise ValueError(
                f"{label} {coord} is outside the grid "
                f"(0-{input[St.WIDTH] - 1}, 0-{input[St.HEIGHT] - 1})."
            )


def main() -> None:
    """Parse CLI argument, read config, validate and start the maze."""
    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} <config>")
        print("  Example: python3 a_maze_ing.py config.txt")
        sys.exit(1)

    config_path = sys.argv[1]

    try:
        config = parse_config(config_path)
        # input: dict = convert_config(config)
        # validate_config(input)
        ta = TypeAdapter(Validation)
        res = ta.validate_python(config)
        print(res)
        
    except (FileNotFoundError, KeyError, ValueError) as e:
        print(f"Configuration error: {e}")
        print("Exiting.")
        sys.exit(1)
    except ValidationError as e:
        print(f"test {e}")

    # maze = Maze(input)
    # maze.run(input)
    # maze.interactive_menu()


if __name__ == "__main__":
    main()
