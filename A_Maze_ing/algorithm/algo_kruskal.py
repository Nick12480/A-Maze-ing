"""Randomized Kruskal maze generator."""

from typing import Generator, List, Tuple

from .algo_nicki import _DisjointSet
from .base import Algorithm, Coordinate, GenerationStep
from .states import E, S


class Kruskal(Algorithm):
    """Generate a perfect maze with randomized Kruskal."""

    name = "kruskal"

    def generate(self) -> Generator[GenerationStep, None, None]:
        """Carve shuffled edges that connect distinct components."""
        cells = list(self.cells())
        components = _DisjointSet(cells)
        edges: List[Tuple[Coordinate, Coordinate, int]] = []
        self.visited = set(cells)

        for first in cells:
            for second, direction in self.neighbours(first):
                if direction in (E, S):
                    edges.append((first, second, direction))
        self.random.shuffle(edges)

        for first, second, direction in edges:
            if components.union(first, second):
                self.carve(first, second, direction)
                yield GenerationStep(second, "Kruskal join components")
