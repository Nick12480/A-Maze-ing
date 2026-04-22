import sys
import os
from typing import Generator, Optional, Any, Callable
import random
import time

import functools

from .base import Algorithm
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
    COLOR
)


def timer(func: Callable) -> Callable:
    def wrapper(*args, **kwargs):
        start = time.time()
        func(*args, **kwargs)
        end = time.time()
        print(f"\nfinished {func.__name__} in {round(end - start, 4)}s")
    return wrapper


class Dfs(Algorithm):
    """
    look for random undiscovered area next to current
    explore, repeat
    if at dead end, backtrace to first undiscovered nearby block

    if nearby block is = NESW its undiscovered
    """

    def __init__(self, config):
        self.config = config
        self.walls = self.Init.__init_outer_walls(self.config)

        self.field = [] # 0 undiscovered note; 1 discovered note
        self.field.append([0 for _ in range(config[WIDTH] for _ in range(config[HEIGHT]))])

        self.walls, self.field = self.Init.__init_pattern(self.config, self.walls, self.field)
        self.route = ""

    @timer 
    def run(self):
        """
        use starting node,
        randomly choose next undiscovered neighbour
        explore
        if stuck call backtrace
        """
        position = list(self.config(ENTRY))
        while 0 in self.field:
            x, y = tuple(position)
            self.field[y][x] = 1
            direction = self.Logic.__get_new_neighbour(position, self.field)
            if self.Logic.__get_new_neighbour(position):
                """
                Need to field as found and set walls according to nextdoor any neighbours walls
                """
                self.Logic.__adjust_to_neighbour
                # position += next
            else:
                position = self.Logic.__backtrack()

        res = self.walls
        res.append([
            f"\n{self.config[ENTRY][0]},"
            f"{self.config[ENTRY][0]}\n"
            f"{self.config[EXIT][0]}"
            f",{self.config[EXIT][0]}\n"
            ])
        res.append([self.Output.__coords_to_dir()])
        self.Output.__write_output()
    
    
    