"""Maze algorithm factory and execution facade."""

from typing import Dict, Type

from algorithm import ALGORITHM, Algorithm, Dfs, Kruskal, Sidewinder


class Maze:
    """Create and run the algorithm selected by validated configuration."""

    algorithms: Dict[str, Type[Algorithm]] = {
        "dfs": Dfs,
        "sidewinder": Sidewinder,
        "kruskal": Kruskal,
    }

    def __init__(self, config: Dict[str, object]) -> None:
        """Store validated configuration."""
        self.config = config

    def create(self) -> Algorithm:
        """Return a new configured algorithm instance."""
        algorithm_name = str(self.config[ALGORITHM])
        return self.algorithms[algorithm_name](self.config)

    def run(self) -> Algorithm:
        """Generate, solve, write, and return the selected algorithm."""
        algorithm = self.create()
        algorithm.run()
        return algorithm
