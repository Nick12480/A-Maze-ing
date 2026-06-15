"""Randomized depth-first-search maze generator."""

from typing import Generator

from .base import Algorithm, GenerationStep


class Dfs(Algorithm):
    """Generate a perfect maze with randomized recursive backtracking."""

    name = "dfs"

    def generate(self) -> Generator[GenerationStep, None, None]:
        """Carve a DFS spanning tree and yield each algorithm event."""
        stack = [self.entry]
        self.visited = {self.entry}
        yield GenerationStep(self.entry, "start DFS")

        while stack:
            current = stack[-1]
            choices = [
                (cell, direction)
                for cell, direction in self.neighbours(current)
                if cell not in self.visited
            ]
            if not choices:
                stack.pop()
                yield GenerationStep(
                    stack[-1] if stack else current,
                    "DFS backtrack",
                )
                continue
            neighbour, direction = self.random.choice(choices)
            self.carve(current, neighbour, direction)
            self.visited.add(neighbour)
            stack.append(neighbour)
            yield GenerationStep(neighbour, "DFS carve")
