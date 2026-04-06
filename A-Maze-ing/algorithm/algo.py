import time
import os
import sys
import random
from collections import deque
from typing import Generator, Optional

import functools

import algorithm as St


def timer(func):
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        func(*args, **kwargs)
        end = time.time()
        print(f"finished in {round(end-start, 3)}s")
    return wrapper


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

    def __init__(self, input: dict) -> None:
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
        self.input = input
        self.grid = [[0] * input[St.WIDTH] for _ in range(input[St.HEIGHT])]
        self.path = []

        ox = (input[St.WIDTH] - 7) // 2
        oy = (input[St.HEIGHT] - 5) // 2
        if ox >= 0 and oy >= 0:
            self.pattern: set = (
                {(ox + x, oy + y) for y, x in St.DIGIT_4} |
                {((ox + 4) + x, oy + y) for y, x in St.DIGIT_2}
            )
            self.pattern = {
                (x, y) for (x, y) in self.pattern
                if 0 <= x < input[St.WIDTH] and 0 <= y < input[St.HEIGHT]
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
        random.seed(self.input[St.SEED])
        for y in range(self.input[St.HEIGHT]):
            run_start = 0
            for x in range(self.input[St.WIDTH]):
                yield
                if (x, y) in self.pattern:
                    run_start = x + 1
                    continue

                at_east_wall = (x + 1 == self.input[St.WIDTH])
                next_blocked = (x + 1, y) in self.pattern
                carve_north = (
                    y > 0
                    and (at_east_wall or next_blocked
                         or random.randint(0, self.input[St.WEIGHT] - 1) == 0)
                )

                if carve_north:
                    valid = [
                        c for c in range(run_start, x + 1)
                        if (c, y) not in self.pattern
                        and (c, y - 1) not in self.pattern
                    ]
                    if valid:
                        cell = random.choice(valid)
                        self.grid[y][cell] |= St.N
                        self.grid[y - 1][cell] |= St.S
                    elif not at_east_wall and not next_blocked:
                        self.grid[y][x] |= St.E
                        self.grid[y][x + 1] |= St.W
                    run_start = x + 1
                elif not at_east_wall and not next_blocked:
                    self.grid[y][x] |= St.E
                    self.grid[y][x + 1] |= St.W

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
        extra = max(1, (self.input[St.WIDTH] * self.input[St.HEIGHT]) // 7)
        candidates = []
        for y in range(self.input[St.HEIGHT]):
            for x in range(self.input[St.WIDTH]):
                if (x, y) in self.pattern:
                    continue
                if (
                    not (self.grid[y][x] & St.E)
                    and x + 1 < self.input[St.WIDTH]
                    and (x + 1, y) not in self.pattern
                ):
                    candidates.append(('E', x, y))
                if (
                    not (self.grid[y][x] & St.S)
                    and y + 1 < self.input[St.HEIGHT]
                    and (x, y + 1) not in self.pattern
                ):
                    candidates.append(('S', x, y))

        random.shuffle(candidates)
        for direction, x, y in candidates[:extra]:
            if direction == 'E':
                self.grid[y][x] |= St.E
                self.grid[y][x + 1] |= St.W
            else:
                self.grid[y][x] |= St.S
                self.grid[y + 1][x] |= St.N

    def generate(self) -> Generator[None, None, None]:
        """Generate the maze using the configured algorithm.

        Automatically selects between Sidewinder and Placeholder based
        on ``self.algorithm``. Adds loops afterwards if
        ``self.perfect`` is ``False``.

        Yields:
            After each processed step for animation.
        """
        if self.input[St.ALGORITHM] == 'placeholder':
            yield from self._generate_placeholder()
        else:
            yield from self._generate_sidewinder()
        if not self.input[St.PERFECT]:
            self._add_loops()

    def solve(self) -> None:
        """Solve the maze via BFS and store the shortest path.

        The result (ordered list of cells) is stored in :attr:`path`.
        If no path exists, ``path`` remains empty.
        """
        self.path = []
        queue: deque = deque([(self.input[St.ENTRY], [self.input[St.ENTRY]])])
        visited: set = {self.input[St.ENTRY]}
        dirs = {St.N: (0, -1), St.S: (0, 1), St.E: (1, 0), St.W: (-1, 0)}

        while queue:
            (x, y), current_path = queue.popleft()
            if (x, y) == self.input[St.EXIT]:
                self.path = current_path
                return
            for bit, (dx, dy) in dirs.items():
                if self.grid[y][x] & bit:
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < self.input[St.WIDTH]
                        and 0 <= ny < self.input[St.HEIGHT]
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
        buf.append(" " + "_" * (self.input[St.WIDTH] * 2 - 1) + "\n")

        for y in range(self.input[St.HEIGHT]):
            buf.append("|")
            for x in range(self.input[St.WIDTH]):
                cell = self.grid[y][x]
                in_pattern = (x, y) in self.pattern
                on_path = (x, y) in path_set
                is_entry = (x, y) == self.input[St.ENTRY]
                is_exit = (x, y) == self.input[St.EXIT]

                if in_pattern:
                    buf.append(f"{St.PURPLE}_|{St.RESET}")
                    continue

                if is_entry:
                    buf.append(f"{St.YELLOW}E{St.RESET}")
                elif is_exit:
                    buf.append(f"{St.YELLOW}X{St.RESET}")
                elif on_path:
                    buf.append(f"{St.YELLOW}*{St.RESET}")
                else:
                    buf.append(" " if (cell & St.S) else "_")

                if not (cell & St.E):
                    buf.append("|")
                else:
                    if (
                        not (cell & St.S) and x + 1 < self.input[St.WIDTH]
                        and not (self.grid[y][x + 1] & St.S)
                    ):
                        buf.append("_")
                    else:
                        buf.append(" ")
            buf.append("\n")

        print("".join(buf), end="", flush=True)

    def interactive_menu(self) -> None:
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
                self.input[St.SEED] += 1
                self.grid = [[0] * self.input[St.WIDTH] for _ in range(self.input[St.HEIGHT])]
                self.path = []
                if self.input[St.ANIMATE]:
                    print("\033[2J", end="", flush=True)
                for _ in self.generate():
                    if self.input[St.ANIMATE]:
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
                f.write(f"{self.input[St.ENTRY][0]},{self.input[St.ENTRY][1]}\n")
                f.write(f"{self.input[St.EXIT][0]},{self.input[St.EXIT][1]}\n")
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

    @timer
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
                # time.sleep(0)

        self.solve()
        self.display()

        if output_file:
            self.write_output(output_file)

        print(
            f"Algorithm: {self.input[St.ALGORITHM]}  "
            f"{self.input[St.WIDTH]}x{self.input[St.HEIGHT]}  "
            f"seed={self.input[St.SEED]}"
        )
