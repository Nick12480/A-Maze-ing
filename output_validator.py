"""Validate symmetric wall encoding in an A-Maze-ing output file."""

import sys
from typing import List, Optional


def read_grid(filepath: str) -> List[List[int]]:
    """Read hexadecimal wall rows from an output file."""
    grid = []
    with open(filepath, "r", encoding="utf-8") as output:
        for line in output:
            if not line.strip():
                break
            grid.append([int(character, 16) for character in line.strip()])
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("Output does not contain a rectangular wall grid.")
    return grid


def validate_walls(grid: List[List[int]]) -> Optional[str]:
    """Return the first asymmetric wall error, or ``None``."""
    for row in range(len(grid)):
        for column in range(len(grid[0])):
            value = grid[row][column]
            boundary_closed = (
                row > 0 or bool(value & 1),
                column < len(grid[0]) - 1 or bool(value & 2),
                row < len(grid) - 1 or bool(value & 4),
                column > 0 or bool(value & 8),
            )
            if not all(boundary_closed):
                return "Open outer boundary at ({},{})".format(column, row)
            valid = (
                row < 1 or value & 1 == (grid[row - 1][column] >> 2) & 1,
                column >= len(grid[0]) - 1
                or (value >> 1) & 1 == (
                    grid[row][column + 1] >> 3
                ) & 1,
                row >= len(grid) - 1
                or (value >> 2) & 1 == grid[row + 1][column] & 1,
                column < 1
                or (value >> 3) & 1 == (
                    grid[row][column - 1] >> 1
                ) & 1,
            )
            if not all(valid):
                return "Wrong encoding for ({},{})".format(column, row)
    return None


def main(arguments: List[str]) -> int:
    """Validate one output filepath supplied on the command line."""
    if len(arguments) != 1:
        print("Usage: python3 output_validator.py <output_file>")
        return 1
    try:
        error = validate_walls(read_grid(arguments[0]))
    except (OSError, ValueError) as exception:
        print("Error: {}".format(exception))
        return 1
    if error:
        print(error)
        return 1
    print("Everything works")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
