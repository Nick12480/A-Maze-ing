import os
import sys
import random
from typing import Optional

from pydantic import model_validator, Field, TypeAdapter, BaseModel

from .maze import Maze
from .algorithm import ENTRY, EXIT, ALGORITHM, OUTPUT_FILE, COLOR
from .animate import Animate


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

        valid_algorithms = ('sidewinder', 'dfs')

        if self.WIDTH > max_width:
            raise ValueError(f"WIDTH must be <= {max_width} (terminal size).")
        if self.HEIGHT > max_height:
            raise ValueError(f"HEIGHT must be <= {max_height} (terminal size).")  # noqa: E501
        if self.ENTRY == self.EXIT:
            raise ValueError("ENTRY and EXIT must not be (identical.")
        if self.ALGORITHM not in valid_algorithms:
            raise ValueError("ALGORITHM must be 'sidewinder' or 'placeholder'.")  # noqa: E501

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
    Empty lines and comments are skipped.
    """
    config: dict = {}

    try:
        with open(filepath, 'r') as f:
            config = {
                key.strip(): value.strip() for key, value in
                (line.split("=", 1) for line in f
                    if "=" in line)
                if not key.startswith("#")
                }
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        raise
    except Exception as e:
        print(f"Parse error: {e}")
        raise

    try:
        config[ENTRY] = tuple(map(int, config[ENTRY].split(',')))
        config[EXIT] = tuple(map(int, config[EXIT].split(',')))
    except Exception as e:
        print(f"Entry or Exit not Tuple\n:{e}")

    return config


def main() -> None:
    """Parse CLI argument, read config, validate and start the maze."""
    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} <config>")
        print("Example: python3 a_maze_ing.py config.txt")
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
    obj = maze.run()
    match config[ALGORITHM]:
        case 'dfs':
            with open(config[OUTPUT_FILE], 'r') as f:
                buff = f.read()
            data = Animate.animate(buff)
            Animate.loop(data, config, COLOR)
        case 'sidewinder':
            if obj is None:
                raise ValueError("returned object is none")
            obj.interactive_menu()


if __name__ == "__main__":
    main()
