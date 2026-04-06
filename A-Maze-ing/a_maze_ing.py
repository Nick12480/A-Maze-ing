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
import time
from collections import deque
from typing import Generator, Optional


W, S, E, N = 8, 4, 2, 1


YELLOW = "\033[33m"
PURPLE = "\033[37;45m"
RESET = "\033[0m"


DIGIT_4 = [
    (0, 0),
    (1, 0),
    (2, 0), (2, 1), (2, 2),
            (3, 1),
            (4, 1),
]

DIGIT_2 = [
    (0, 0), (0, 1), (0, 2),
                    (1, 2),
    (2, 0), (2, 1), (2, 2),
    (3, 0),
    (4, 0), (4, 1), (4, 2),
]


def build_pattern(offset_x: int, offset_y: int, digit: list) -> set:
    """Build a set of grid positions for a digit shape.

    Shifts all points of the pattern by the given offset.

    Args:
        offset_x: Horizontal offset in cells.
        offset_y: Vertical offset in cells.
        digit: List of ``(row, col)`` tuples describing the pixel pattern.

    Returns:
        A set of ``(col, row)`` tuples in grid coordinate space.
    """
    return {(offset_x + x, offset_y + y) for y, x in digit}


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
    try:
        width = int(config.get('WIDTH', 20))
        height = int(config.get('HEIGHT', width))
        weight = max(1, int(config.get('WEIGHT', 2)))
        seed = (
            int(config['SEED'])
            if 'SEED' in config
            else random.randint(0, 0xFFFF_FFFF)
        )
        animate = config.get('ANIMATE', 'true').lower() == 'true'
        entry = (
            tuple(map(int, config['ENTRY'].split(',')))
            if 'ENTRY' in config
            else (0, 0)
        )
        exit_coord = (
            tuple(map(int, config['EXIT'].split(',')))
            if 'EXIT' in config
            else (width - 1, height - 1)
        )
        output_file = config.get('OUTPUT_FILE', 'output_maze.txt')
        perfect = config.get('PERFECT', 'true').lower() == 'true'
        algorithm = config.get('ALGORITHM', 'sidewinder').lower()
    except ValueError as e:
        print(f"Type conversion error: {e}")
        raise
    return (width, height, weight, seed, animate,
            entry, exit_coord, output_file, perfect, algorithm)


def validate_config(
    width: int, height: int, entry: tuple, exit_coord: tuple,
    algorithm: str
) -> None:
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
        (width <= 1, "WIDTH must be greater than 1."),
        (height <= 1, "HEIGHT must be greater than 1."),
        (width > max_width, f"WIDTH must be <= {max_width} (terminal size)."),
        (height > max_height,
         f"HEIGHT must be <= {max_height} (terminal size)."),
        (entry == exit_coord, "ENTRY and EXIT must not be identical."),
        (algorithm not in valid_algorithms,
         "ALGORITHM must be 'sidewinder' or 'placeholder'."),
    ]
    for condition, msg in constraints:
        if condition:
            raise ValueError(msg)

    for label, coord in [('ENTRY', entry), ('EXIT', exit_coord)]:
        col, row = coord
        if not (0 <= col < width and 0 <= row < height):
            raise ValueError(
                f"{label} {coord} is outside the grid "
                f"(0-{width - 1}, 0-{height - 1})."
            )


class Maze:
    """Maze generator, solver and renderer.

    Supports two algorithms: Sidewinder and Placeholder.
    Embeds the '42' pattern as a wall, solves via BFS, renders as a
    coloured ASCII image and can write the result to a hex output file.

    Attributes:
        width: Maze width in cells.
        height: Maze height in cells.
        weight: Bias weight for Sidewinder (east passages).
        seed: Random seed for reproducible mazes.
        entry: Entry position as ``(col, row)``.
        exit_coord: Exit position as ``(col, row)``.
        algorithm: Chosen algorithm ('sidewinder' / 'placeholder').
        perfect: If ``False``, extra loops are added after generation.
        grid: 2-D list of bitmask ints (N/E/S/W).
        path: Ordered list of cells on the shortest solution path.
        pattern: Set of cells that form the '42' pattern.
    """

    def __init__(
        self, width: int, height: int, weight: int, seed: int, entry: tuple,
        exit_coord: tuple, algorithm: str = 'sidewinder', perfect: bool = True
    ) -> None:
        """Initialise the maze and compute the '42' pattern.

        Args:
            width: Width in cells.
            height: Height in cells.
            weight: Bias weight for Sidewinder.
            seed: Random seed.
            entry: Entry as ``(col, row)``.
            exit_coord: Exit as ``(col, row)``.
            algorithm: 'sidewinder' (default) or 'placeholder'.
            perfect: If ``False``, extra loops are added after generation.
        """
        self.width = width
        self.height = height
        self.weight = weight
        self.seed = seed
        self.entry = entry
        self.exit_coord = exit_coord
        self.algorithm = algorithm
        self.perfect = perfect
        self.grid: list = [[0] * width for _ in range(height)]
        self.path: list = []

        ox = (width - 7) // 2
        oy = (height - 5) // 2
        if ox >= 0 and oy >= 0:
            self.pattern: set = (
                build_pattern(ox,     oy, DIGIT_4) |
                build_pattern(ox + 4, oy, DIGIT_2)
            )
            self.pattern = {
                (x, y) for (x, y) in self.pattern
                if 0 <= x < width and 0 <= y < height
            }
        else:
            self.pattern = set()
            print(
                "Warning: maze too small for the '42' pattern. "
                "Pattern will be omitted."
            )

    def _generate_sidewinder(self) -> Generator[None, None, None]:
        """Generate the maze using the Sidewinder algorithm.

        Yields:
            After each processed step for animation.
        """
        random.seed(self.seed)
        for y in range(self.height):
            run_start = 0
            for x in range(self.width):
                yield
                if (x, y) in self.pattern:
                    run_start = x + 1
                    continue

                at_east_wall = (x + 1 == self.width)
                next_blocked = (x + 1, y) in self.pattern
                carve_north = (
                    y > 0
                    and (at_east_wall or next_blocked
                         or random.randint(0, self.weight - 1) == 0)
                )

                if carve_north:
                    valid = [
                        c for c in range(run_start, x + 1)
                        if (c, y) not in self.pattern
                        and (c, y - 1) not in self.pattern
                    ]
                    if valid:
                        cell = random.choice(valid)
                        self.grid[y][cell] |= N
                        self.grid[y - 1][cell] |= S
                    elif not at_east_wall and not next_blocked:
                        self.grid[y][x] |= E
                        self.grid[y][x + 1] |= W
                    run_start = x + 1
                elif not at_east_wall and not next_blocked:
                    self.grid[y][x] |= E
                    self.grid[y][x + 1] |= W

    # Algorithm 2: Placeholder

    def _generate_placeholder(self) -> Generator[None, None, None]:
        pass

    def _add_loops(self) -> None:
        """Randomly remove walls to create loops in the maze.

        Only called when ``self.perfect`` is ``False``.
        Removes roughly 1/7 of remaining inner walls so that multiple
        paths exist between entry and exit.
        """
        random.seed(self.seed + 1)
        extra = max(1, (self.width * self.height) // 7)
        candidates = []
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) in self.pattern:
                    continue
                if (
                    not (self.grid[y][x] & E)
                    and x + 1 < self.width
                    and (x + 1, y) not in self.pattern
                ):
                    candidates.append(('E', x, y))
                if (
                    not (self.grid[y][x] & S)
                    and y + 1 < self.height
                    and (x, y + 1) not in self.pattern
                ):
                    candidates.append(('S', x, y))

        random.shuffle(candidates)
        for direction, x, y in candidates[:extra]:
            if direction == 'E':
                self.grid[y][x] |= E
                self.grid[y][x + 1] |= W
            else:
                self.grid[y][x] |= S
                self.grid[y + 1][x] |= N

    def generate(self) -> Generator[None, None, None]:
        """Generate the maze using the configured algorithm.

        Automatically selects between Sidewinder and Placeholder based
        on ``self.algorithm``. Adds loops afterwards if
        ``self.perfect`` is ``False``.

        Yields:
            After each processed step for animation.
        """
        if self.algorithm == 'placeholder':
            yield from self._generate_placeholder()
        else:
            yield from self._generate_sidewinder()
        if not self.perfect:
            self._add_loops()

    def solve(self) -> None:
        """Solve the maze via BFS and store the shortest path.

        The result (ordered list of cells) is stored in :attr:`path`.
        If no path exists, ``path`` remains empty.
        """
        self.path = []
        queue: deque = deque([(self.entry, [self.entry])])
        visited: set = {self.entry}
        dirs = {N: (0, -1), S: (0, 1), E: (1, 0), W: (-1, 0)}

        while queue:
            (x, y), current_path = queue.popleft()
            if (x, y) == self.exit_coord:
                self.path = current_path
                return
            for bit, (dx, dy) in dirs.items():
                if self.grid[y][x] & bit:
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < self.width
                        and 0 <= ny < self.height
                        and (nx, ny) not in visited
                        and (nx, ny) not in self.pattern
                    ):
                        visited.add((nx, ny))
                        queue.append(
                            ((nx, ny), current_path + [(nx, ny)])
                        )

    def display(self) -> None:
        """Render the maze as a coloured ASCII image in the terminal.

        Special characters:
        - ``E`` - Entry
        - ``X`` - Exit
        - Purple block - '42' pattern cell
        - ``*`` (yellow) - Solution path
        """
        path_set = set(self.path)
        buf = ["\033[H"]
        buf.append(" " + "_" * (self.width * 2 - 1) + "\n")

        for y in range(self.height):
            buf.append("|")
            for x in range(self.width):
                cell = self.grid[y][x]
                in_pattern = (x, y) in self.pattern
                on_path = (x, y) in path_set
                is_entry = (x, y) == self.entry
                is_exit = (x, y) == self.exit_coord

                if in_pattern:
                    buf.append(f"{PURPLE}_|{RESET}")
                    continue

                if is_entry:
                    buf.append(f"{YELLOW}E{RESET}")
                elif is_exit:
                    buf.append(f"{YELLOW}X{RESET}")
                elif on_path:
                    buf.append(f"{YELLOW}*{RESET}")
                else:
                    buf.append(" " if (cell & S) else "_")

                if not (cell & E):
                    buf.append("|")
                else:
                    if (
                        not (cell & S) and x + 1 < self.width
                        and not (self.grid[y][x + 1] & S)
                    ):
                        buf.append("_")
                    else:
                        buf.append(" ")
            buf.append("\n")

        print("".join(buf), end="", flush=True)

    def interactive_menu(self, animate: bool) -> None:
        """Show the interactive terminal menu and handle user input.

        Options: regenerate, toggle path, rotate colours, quit.

        Args:
            animate: Whether animation is active when regenerating.
        """
        colors = [
            ("\033[33m", "\033[37;45m"),   # Yellow / Purple
            ("\033[36m", "\033[37;44m"),   # Cyan / Blue
            ("\033[32m", "\033[37;42m"),   # Green / Dark green
            ("\033[35m", "\033[37;41m"),   # Magenta / Red
        ]
        color_idx = 0
        show_path = True

        while True:
            print("\n==== A-Maze-ing ====")
            print("1. Regenerate maze")
            print("2. Toggle path")
            print("3. Rotate colours")
            print("4. Quit")
            choice = input("Choice (1-4): ").strip()

            if choice == '1':
                self.seed += 1
                self.grid = [[0] * self.width for _ in range(self.height)]
                self.path = []
                if animate:
                    print("\033[2J", end="", flush=True)
                for _ in self.generate():
                    if animate:
                        self.display()
                        time.sleep(0.02)
                self.solve()
                self.display()
            elif choice == '2':
                show_path = not show_path
                if not show_path:
                    saved = self.path
                    self.path = []
                    self.display()
                    self.path = saved
                else:
                    self.display()
            elif choice == '3':
                color_idx = (color_idx + 1) % len(colors)
                global YELLOW, PURPLE
                YELLOW, PURPLE = colors[color_idx]
                self.display()
            elif choice == '4':
                print("Goodbye!")
                break
            else:
                print("Invalid input.")

    def write_output(self, filepath: str) -> None:
        """Write the maze in hex format to a file.

        Format as per subject specification:
        - One hex digit per cell, row by row
        - Empty line
        - Entry coordinates
        - Exit coordinates
        - Shortest path as a direction sequence (N/E/S/W)

        Args:
            filepath: Path to the output file.

        Raises:
            OSError: If the file cannot be written.
        """
        path_str = self._path_to_directions()

        try:
            with open(filepath, 'w') as f:
                for row in self.grid:
                    line = "".join(format(cell, 'X') for cell in row)
                    f.write(line + "\n")
                f.write("\n")
                f.write(f"{self.entry[0]},{self.entry[1]}\n")
                f.write(f"{self.exit_coord[0]},{self.exit_coord[1]}\n")
                f.write(path_str + "\n")
            print(f"Output saved: {filepath}")
        except OSError as e:
            print(f"Error writing output file: {e}")
            raise

    def _path_to_directions(self) -> str:
        """Convert the BFS path to a direction sequence string.

        Returns:
            String of N/E/S/W characters (empty if no path exists).
        """
        if len(self.path) < 2:
            return ""
        result = []
        dir_map: dict = {
            (0, -1): 'N',
            (0,  1): 'S',
            (1,  0): 'E',
            (-1, 0): 'W',
        }
        for i in range(len(self.path) - 1):
            x0, y0 = self.path[i]
            x1, y1 = self.path[i + 1]
            delta = (x1 - x0, y1 - y0)
            result.append(dir_map.get(delta, '?'))
        return "".join(result)

    def run(self, animate: bool, output_file: Optional[str] = None) -> None:
        """Generate, solve, display and write the output file.

        Args:
            animate: If ``True``, each generation step is animated.
            output_file: Path to the output file. If ``None``, no file
                is written.
        """
        if animate:
            print("\033[2J", end="", flush=True)

        for _ in self.generate():
            if animate:
                self.display()
                time.sleep(0.02)

        self.solve()
        self.display()

        if output_file:
            self.write_output(output_file)

        print(
            f"Algorithm: {self.algorithm}  "
            f"{self.width}x{self.height}  "
            f"seed={self.seed}"
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
        (width, height, weight, seed, animate,
         entry, exit_coord, output_file, perfect, algorithm) = (
            convert_config(config)
        )
        validate_config(width, height, entry, exit_coord, algorithm)
    except (FileNotFoundError, KeyError, ValueError) as e:
        print(f"Configuration error: {e}")
        print("Exiting.")
        sys.exit(1)

    maze = Maze(
        width, height, weight, seed,
        entry, exit_coord, algorithm, perfect
    )
    maze.run(animate, output_file)
    maze.interactive_menu(animate)


if __name__ == "__main__":
    main()
