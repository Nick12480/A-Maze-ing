"""Shared maze model, validation helpers, solving, and output."""

from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
import random
from typing import Deque, Dict, Generator, Iterable, List, Optional, Set
from typing import Tuple

from .states import (
    DIRECTIONS,
    E,
    ENTRY,
    EXIT,
    HEIGHT,
    N,
    OPPOSITE,
    OUTPUT_FILE,
    PERFECT,
    S,
    SEED,
    W,
    WIDTH,
    DIGIT_2,
    DIGIT_4,
)

Coordinate = Tuple[int, int]
PassageGrid = List[List[int]]


class LogicError(Exception):
    """Report an invalid or impossible maze-generation state."""


@dataclass(frozen=True)
class GenerationStep:
    """Describe one algorithm event for the independent ANSI animator."""

    current: Optional[Coordinate]
    action: str


class Algorithm(ABC):
    """Provide common behavior for every maze-generation algorithm."""

    name = "base"

    def __init__(self, config: Dict[str, object]) -> None:
        """Initialize a deterministic empty maze from validated config."""
        self.config = config
        self.width = int(config[WIDTH])
        self.height = int(config[HEIGHT])
        self.entry = tuple(config[ENTRY])  # type: ignore[arg-type]
        self.exit = tuple(config[EXIT])  # type: ignore[arg-type]
        self.random = random.Random(int(config[SEED]))
        self.pattern = self._make_pattern()
        self.passages: PassageGrid = []
        self.path: List[Coordinate] = []
        self.visited: Set[Coordinate] = set()
        self.reset()

    @abstractmethod
    def generate(self) -> Generator[GenerationStep, None, None]:
        """Yield events while carving a spanning tree."""

    def reset(self) -> None:
        """Clear generated passages and transient algorithm state."""
        self.passages = [
            [0 for _ in range(self.width)] for _ in range(self.height)
        ]
        self.path = []
        self.visited = set()
        self.random.seed(int(self.config[SEED]))

    def steps(self) -> Generator[GenerationStep, None, None]:
        """Yield a complete perfect or imperfect maze generation."""
        self.reset()
        yield from self.generate()
        self._validate_perfect_tree()
        if not bool(self.config[PERFECT]):
            yield from self._add_loops()
        self.solve()

    def run(self) -> None:
        """Generate, solve, and write the configured output file."""
        for _ in self.steps():
            pass
        output_file = str(self.config[OUTPUT_FILE])
        if output_file:
            self.write_output(output_file)

    def _make_pattern(self) -> Set[Coordinate]:
        """Return centered blocked cells forming the digits ``42``."""
        if self.width < 9 or self.height < 7:
            return set()
        x_offset = (self.width - 7) // 2
        y_offset = (self.height - 5) // 2
        four = {
            (x_offset + x, y_offset + y) for x, y in DIGIT_4
        }
        two = {
            (x_offset + 4 + x, y_offset + y) for x, y in DIGIT_2
        }
        return four | two

    def cells(self) -> Iterable[Coordinate]:
        """Iterate over all non-pattern maze cells."""
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) not in self.pattern:
                    yield (x, y)

    def neighbours(
        self,
        cell: Coordinate,
    ) -> List[Tuple[Coordinate, int]]:
        """Return passable-grid neighbours and their direction bits."""
        x, y = cell
        result = []
        for direction, dx, dy in DIRECTIONS:
            neighbour = (x + dx, y + dy)
            nx, ny = neighbour
            if (
                0 <= nx < self.width
                and 0 <= ny < self.height
                and neighbour not in self.pattern
            ):
                result.append((neighbour, direction))
        return result

    def connected_neighbours(self, cell: Coordinate) -> List[Coordinate]:
        """Return neighbours connected to a cell by carved passages."""
        x, y = cell
        return [
            neighbour
            for neighbour, direction in self.neighbours(cell)
            if self.passages[y][x] & direction
        ]

    def carve(
        self,
        first: Coordinate,
        second: Coordinate,
        direction: int,
    ) -> None:
        """Open a symmetric passage between two adjacent cells."""
        x1, y1 = first
        x2, y2 = second
        if (second, direction) not in self.neighbours(first):
            raise LogicError(
                "Cannot carve between non-adjacent or blocked cells."
            )
        self.passages[y1][x1] |= direction
        self.passages[y2][x2] |= OPPOSITE[direction]

    def solve(self) -> List[Coordinate]:
        """Find and store the shortest entrance-to-exit path using BFS."""
        parents: Dict[Coordinate, Optional[Coordinate]] = {
            self.entry: None
        }
        queue: Deque[Coordinate] = deque([self.entry])
        while queue:
            current = queue.popleft()
            if current == self.exit:
                break
            for neighbour in self.connected_neighbours(current):
                if neighbour not in parents:
                    parents[neighbour] = current
                    queue.append(neighbour)
        if self.exit not in parents:
            raise LogicError("Generated maze has no entrance-to-exit path.")
        current: Optional[Coordinate] = self.exit
        reverse_path = []
        while current is not None:
            reverse_path.append(current)
            current = parents[current]
        self.path = list(reversed(reverse_path))
        return self.path

    def _add_loops(self) -> Generator[GenerationStep, None, None]:
        """Open walls while guaranteeing an alternate solution path."""
        self.solve()
        solution_edges = self._edge_set(self.path)
        candidates = self._closed_edges()
        self.random.shuffle(candidates)

        required = None
        for first, second, direction in candidates:
            cycle_path = self._path_between(first, second)
            if self._edge_set(cycle_path) & solution_edges:
                required = (first, second, direction)
                break
        if required is None:
            raise LogicError(
                "This grid cannot provide multiple entrance-to-exit paths."
            )

        first, second, direction = required
        self.carve(first, second, direction)
        yield GenerationStep(second, "add required solution loop")

        remaining = [
            edge for edge in candidates if edge != required
        ]
        extra_count = max(0, len(list(self.cells())) // 12 - 1)
        for first, second, direction in remaining[:extra_count]:
            self.carve(first, second, direction)
            yield GenerationStep(second, "add optional loop")

        self.solve()
        if not self.has_multiple_solutions():
            raise LogicError("Imperfect maze still has only one solution.")

    def _closed_edges(
        self,
    ) -> List[Tuple[Coordinate, Coordinate, int]]:
        """Return each closed internal edge exactly once."""
        result = []
        for first in self.cells():
            x, y = first
            for second, direction in self.neighbours(first):
                if direction not in (E, S):
                    continue
                if not self.passages[y][x] & direction:
                    result.append((first, second, direction))
        return result

    def _path_between(
        self,
        start: Coordinate,
        end: Coordinate,
        ignored_edge: Optional[Tuple[Coordinate, Coordinate]] = None,
    ) -> List[Coordinate]:
        """Return a BFS path, optionally treating one passage as closed."""
        parents: Dict[Coordinate, Optional[Coordinate]] = {start: None}
        queue: Deque[Coordinate] = deque([start])
        ignored = frozenset(ignored_edge) if ignored_edge else frozenset()
        while queue:
            current = queue.popleft()
            if current == end:
                break
            for neighbour in self.connected_neighbours(current):
                if frozenset((current, neighbour)) == ignored:
                    continue
                if neighbour not in parents:
                    parents[neighbour] = current
                    queue.append(neighbour)
        if end not in parents:
            return []
        current: Optional[Coordinate] = end
        reverse_path = []
        while current is not None:
            reverse_path.append(current)
            current = parents[current]
        return list(reversed(reverse_path))

    @staticmethod
    def _edge_set(path: List[Coordinate]) -> Set[frozenset]:
        """Convert an ordered path into an unordered set of its edges."""
        return {
            frozenset((path[index], path[index + 1]))
            for index in range(len(path) - 1)
        }

    def has_multiple_solutions(self) -> bool:
        """Return whether at least two simple entrance-to-exit paths exist."""
        if not self.path:
            self.solve()
        for first, second in zip(self.path, self.path[1:]):
            if self._path_between(self.entry, self.exit, (first, second)):
                return True
        return False

    def can_have_multiple_solutions(self) -> bool:
        """Return whether the usable grid permits alternate endpoint paths."""
        path = self._grid_path_between(self.entry, self.exit)
        if not path:
            return False
        bridges = self._grid_bridges()
        return any(
            frozenset((first, second)) not in bridges
            for first, second in zip(path, path[1:])
        )

    def _grid_path_between(
        self,
        start: Coordinate,
        end: Coordinate,
    ) -> List[Coordinate]:
        """Return a BFS path using every available non-pattern grid edge."""
        parents: Dict[Coordinate, Optional[Coordinate]] = {start: None}
        queue: Deque[Coordinate] = deque([start])
        while queue:
            current = queue.popleft()
            if current == end:
                break
            for neighbour, _ in self.neighbours(current):
                if neighbour not in parents:
                    parents[neighbour] = current
                    queue.append(neighbour)
        if end not in parents:
            return []
        current: Optional[Coordinate] = end
        reverse_path = []
        while current is not None:
            reverse_path.append(current)
            current = parents[current]
        return list(reversed(reverse_path))

    def _grid_bridges(self) -> Set[frozenset]:
        """Return bridge edges in the full usable grid without recursion."""
        discovered: Dict[Coordinate, int] = {}
        low: Dict[Coordinate, int] = {}
        parent: Dict[Coordinate, Optional[Coordinate]] = {}
        bridges: Set[frozenset] = set()
        index = 0

        for root in self.cells():
            if root in discovered:
                continue
            parent[root] = None
            discovered[root] = index
            low[root] = index
            index += 1
            stack = [(root, iter(self.neighbours(root)))]

            while stack:
                current, neighbours = stack[-1]
                try:
                    neighbour, _ = next(neighbours)
                except StopIteration:
                    stack.pop()
                    previous = parent[current]
                    if previous is not None:
                        low[previous] = min(low[previous], low[current])
                        if low[current] > discovered[previous]:
                            bridges.add(frozenset((previous, current)))
                    continue

                if neighbour == parent[current]:
                    continue
                if neighbour not in discovered:
                    parent[neighbour] = current
                    discovered[neighbour] = index
                    low[neighbour] = index
                    index += 1
                    stack.append((neighbour, iter(self.neighbours(neighbour))))
                else:
                    low[current] = min(low[current], discovered[neighbour])
        return bridges

    def edge_count(self) -> int:
        """Count carved undirected passages."""
        return sum(
            1
            for y in range(self.height)
            for x in range(self.width)
            for direction in (E, S)
            if self.passages[y][x] & direction
        )

    def _validate_perfect_tree(self) -> None:
        """Ensure the generator produced one connected acyclic maze."""
        cells = list(self.cells())
        if not cells:
            raise LogicError("Maze contains no usable cells.")
        reachable = {cells[0]}
        queue: Deque[Coordinate] = deque([cells[0]])
        while queue:
            current = queue.popleft()
            for neighbour in self.connected_neighbours(current):
                if neighbour not in reachable:
                    reachable.add(neighbour)
                    queue.append(neighbour)
        if len(reachable) != len(cells):
            raise LogicError("Generator left disconnected maze cells.")
        if self.edge_count() != len(cells) - 1:
            raise LogicError("Generator did not produce a perfect maze.")

    def wall_grid(self) -> List[List[int]]:
        """Convert internal passage bits to required wall-bit encoding."""
        result = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                if (x, y) in self.pattern:
                    row.append(N | E | S | W)
                    continue
                walls = 0
                for direction, _, _ in DIRECTIONS:
                    if not self.passages[y][x] & direction:
                        walls |= direction
                row.append(walls)
            result.append(row)
        return result

    def path_directions(self) -> str:
        """Convert the shortest solution path to ``N/E/S/W`` text."""
        directions = {
            (0, -1): "N",
            (1, 0): "E",
            (0, 1): "S",
            (-1, 0): "W",
        }
        return "".join(
            directions[
                (
                    second[0] - first[0],
                    second[1] - first[1],
                )
            ]
            for first, second in zip(self.path, self.path[1:])
        )

    def write_output(self, filepath: str) -> None:
        """Write wall hex digits, endpoints, and shortest path to a file."""
        walls = self.wall_grid()
        with open(filepath, "w", encoding="utf-8") as output:
            for row in walls:
                output.write("".join(format(cell, "x") for cell in row))
                output.write("\n")
            output.write("\n")
            output.write("{},{}\n".format(*self.entry))
            output.write("{},{}\n".format(*self.exit))
            output.write(self.path_directions() + "\n")
