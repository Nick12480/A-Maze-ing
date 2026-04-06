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
from typing import Optional

from pydantic import model_validator, ValidationError, Field, TypeAdapter, BaseModel, field_validator

from algorithm import Maze
import algorithm as St


class Validation(BaseModel):
    HEIGHT: int = Field(..., ge=2)
    WIDTH: int = Field(..., ge=2)
    WEIGHT: int = Field(default=1, ge=1, le=10)
    SEED: Optional[int] = Field(default=random.randint(0, 0xFFFF_FFFF), ge=0)
    ANIMATE: Optional[bool] = Field(default=True)
    ENTRY: list | tuple = Field(...)
    EXIT: list | tuple = Field(...)
    OUTPUT_FILE: Optional[str] = Field(default='output_maze.txt')
    PERFECT: Optional[bool] = Field(default=False)
    ALGORITHM: Optional[str] = Field(default='sidewinder')

    @model_validator(mode='after')
    def validate(self):
        term_cols, term_rows = self.__get_terminal_size()
        max_width = (term_cols - 1) // 2
        max_height = term_rows - 2

        valid_algorithms = ('sidewinder', 'placeholder')
        constraints = [
            (self.WIDTH > max_width, f"WIDTH must be <= {max_width} (terminal\
            size)."),
            (self.HEIGHT > max_height,
            f"HEIGHT must be <= {max_height} (terminal size)."),
            (self.ENTRY == self.EXIT, "ENTRY and EXIT must not be\
            identical."),
            (self.ALGORITHM not in valid_algorithms,
            "ALGORITHM must be 'sidewinder' or 'placeholder'."),
        ]
        for condition, msg in constraints:
            if condition:
                raise ValueError(msg)

        for label, coord in\
                [('ENTRY', self.ENTRY), ('EXIT', self.EXIT)]:
            col, row = coord
            if not (0 <= col < self.WIDTH and 0 <= row < self.HEIGHT):
                raise ValueError(
                    f"{label} {coord} is outside the grid "
                    f"(0-{self.WIDTH - 1}, 0-{self.HEIGHT - 1})."
                )
        return self


    def __get_terminal_size(
        fallback_cols: int = 80, fallback_rows: int = 24
    ) -> tuple[int, int]:
        """Return the current terminal size with a fallback.
        """
        try:
            size = os.get_terminal_size()
            return (size.columns, size.lines)
        except OSError:
            return fallback_cols, fallback_rows


def parse_config(filepath: str) -> dict:
    """Read a plain-text configuration file into a dictionary.

    Each valid line follows the format ``KEY=VALUE``.
    Empty lines and comments (``#``) are skipped.
    """
    config: dict = {}
    try:
        with open(filepath, 'r') as f:
            config = {key.strip(): value.strip() for key, value in (line.split("=", 1) for line in f if "=" in line) if not key.startswith("#")}
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        raise
    except Exception as e:
        print(f"Parse error: {e}")
        raise
    try:
        config[St.ENTRY] = tuple(map(int, config[St.ENTRY].split(',')))
        config[St.EXIT] = tuple(map(int, config[St.EXIT].split(',')))
    except Exception as e:
        print(f"Entry or Exit not Tuple\n:{e}")
    return config


def main() -> None:
    """Parse CLI argument, read config, validate and start the maze."""
    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} <config>")
        print("  Example: python3 a_maze_ing.py config.txt")
        sys.exit(1)

    config_path = sys.argv[1]

    try:
        config = parse_config(config_path)
        ta = TypeAdapter(Validation)
        res = ta.validate_python(config)
        config = res.model_dump()
    except Exception as e:
        print(f"Configuration error: {e}")
        print("Exiting.")
        sys.exit(1)
        
    maze = Maze(config)
    maze.run(config)
    maze.interactive_menu()


if __name__ == "__main__":
    main()
