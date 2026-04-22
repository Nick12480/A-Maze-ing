from typing import Any, Optional



from algorithm import Dfs, Sidewinder, Algorithm, ALGORITHM


class Maze:

    def __init__(self, config: dict[str: Any]):
        self.config = config

    def run(self) -> Optional[Algorithm]:
        match self.config[ALGORITHM]:
            case 'sidewinder':
                sidewinder = Sidewinder(self.config)
                sidewinder.run()
                return sidewinder
            case 'dfs':
                dfs = Dfs(self.config)
                dfs.run()
