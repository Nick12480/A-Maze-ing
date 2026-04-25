import sys
import os
from typing import Generator, Optional, Any, Callable
import random
import time

import functools

from .base import Algorithm as Alg
from .states import (
    W,
    S,
    E,
    N,
    YELLOW,
    PURPLE,
    RESET,
    UNDERLINE,
    DIGIT_4,
    DIGIT_2,
    WIDTH,
    HEIGHT,
    WEIGHT,
    SEED,
    ANIMATE,
    ENTRY,
    EXIT,
    OUTPUT_FILE,
    PERFECT,
    ALGORITHM,
    TIME,
    RED,
    COLOR,
    HEX
)


def timer(func: Callable) -> Callable:
    def wrapper(*args, **kwargs):
        start = time.time()
        func(*args, **kwargs)
        end = time.time()
        print(f"\nfinished {func.__name__} in {round(end - start, 4)}s")
    return wrapper


class Dfs(Alg):
    """
    look for random undiscovered area next to current
    explore, repeat
    if at dead end, backtrace to first undiscovered nearby block

    if nearby block is = NESW its undiscovered
    """

    def __init__(self, config):
        self.config = config
        self.walls = Alg.Init._init_outer_walls(self.config[WIDTH], self.config[HEIGHT])

        self.field = [] # 0 undiscovered note; 1 discovered note
        for y in range(config[HEIGHT]):
                self.field.append([])
                for x in range(config[WIDTH]):
                    self.field[y].append(0)

        self.walls, self.field = Alg.Init._init_pattern(self.config[WIDTH], self.config[HEIGHT], self.walls, self.field)
        self.route = ""

    @timer 
    def run(self):
        """
        use starting node,
        randomly choose next undiscovered neighbour
        explore
        if stuck call backtrace
        """
        path = []
        solution = []
        position: tuple = self.config[ENTRY]
        prev_direction = 0
        while any(0 in row for row in self.field):
            self.walls = Alg.Logic._adjust_to_neighbour(self.config, position, self.walls)

            if position == self.config[EXIT]:
                solution = path

            x, y = position

            self.field[y][x] = 1

            direction: int = Alg.Logic._get_new_neighbour(self.config[WIDTH], self.config[HEIGHT], position, self.field)
            if direction:
                """
                Need to field as found and set walls according to nextdoor any neighbours walls
                """
                path.append(position)
                self.walls = Alg.Logic._add_walls(self.walls, position, direction + prev_direction)
                position = Alg.Logic._move_direction(direction, position)
                prev_direction = int(direction)
            else:
                position, path = Alg.Logic._backtrack(path)
            
        res: str = Alg.Output._walls_to_str(Alg.Output._walls_to_hex(self.walls))
        entry: str = [str(coord) for coord in self.config[ENTRY]]
        res += '\n' + ','.join(entry) + '\n'
        exit: str = [str(coord) for coord in self.config[EXIT]]
        res += ','.join(exit) + '\n'
        res += Alg.Output._coords_to_dir(solution) + '\n'
        Alg.Output._write_output(self.config[OUTPUT_FILE], res)
    
    
    