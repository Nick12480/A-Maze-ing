"""Sidewinder maze generator with obstacle-aware connectivity repair."""

from typing import Dict, Generator, List, Tuple

from .base import Algorithm, Coordinate, GenerationStep
from .states import E, N, WEIGHT


class _DisjointSet:
    """Track connected components without introducing cycles."""

    def __init__(self, cells: List[Coordinate]) -> None:
        """Create one component for each supplied cell."""
        self.parent: Dict[Coordinate, Coordinate] = {
            cell: cell for cell in cells
        }

    def find(self, cell: Coordinate) -> Coordinate:
        """Return a cell component root with path compression."""
        if self.parent[cell] != cell:
            self.parent[cell] = self.find(self.parent[cell])
        return self.parent[cell]

    def union(self, first: Coordinate, second: Coordinate) -> bool:
        """Join two components and report whether a join occurred."""
        root_a = self.find(first)
        root_b = self.find(second)
        if root_a == root_b:
            return False
        self.parent[root_b] = root_a
        return True


class Sidewinder(Algorithm):
    """Generate a row-biased Sidewinder maze."""

    name = "sidewinder"

    def generate(self) -> Generator[GenerationStep, None, None]:
        """Carve Sidewinder runs, then join obstacle-separated forests."""
        self.visited = set()
        weight = int(self.config[WEIGHT])

        for y in range(self.height):
            run: List[Coordinate] = []
            for x in range(self.width):
                current = (x, y)
                if current in self.pattern:
                    run = []
                    continue
                self.visited.add(current)
                run.append(current)
                east = (x + 1, y)
                at_run_end = x + 1 == self.width or east in self.pattern
                north_choices = [
                    cell for cell in run
                    if (cell[0], cell[1] - 1) not in self.pattern
                    and cell[1] > 0
                ]
                close_run = (
                    y > 0
                    and bool(north_choices)
                    and (
                        at_run_end
                        or self.random.randrange(weight + 1) == 0
                    )
                )
                if close_run:
                    chosen = self.random.choice(north_choices)
                    north = (chosen[0], chosen[1] - 1)
                    self.carve(chosen, north, N)
                    run = []
                    yield GenerationStep(chosen, "Sidewinder close run")
                elif not at_run_end:
                    self.carve(current, east, E)
                    yield GenerationStep(east, "Sidewinder extend run")
                elif at_run_end:
                    run = []

        yield from self._repair_components()

    def _repair_components(
        self,
    ) -> Generator[GenerationStep, None, None]:
        """Join Sidewinder forest components while preserving a tree."""
        cells = list(self.cells())
        components = _DisjointSet(cells)
        candidates: List[Tuple[Coordinate, Coordinate, int]] = []

        for first in cells:
            x, y = first
            for second, direction in self.neighbours(first):
                if direction not in (E, N):
                    continue
                if self.passages[y][x] & direction:
                    components.union(first, second)
                else:
                    candidates.append((first, second, direction))

        self.random.shuffle(candidates)
        for first, second, direction in candidates:
            if components.union(first, second):
                self.carve(first, second, direction)
                yield GenerationStep(second, "Sidewinder repair component")
