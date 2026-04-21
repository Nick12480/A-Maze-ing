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
        super().__init__(config)
        self.walls = []
        self.route = ""
        self.map = [] # 0 undiscovered note; 1 discovered note
        self.map.append([0 for _ in range(config[WIDTH] for _ in range(config[HEIGHT]))])

    @timer
    def run(self):
        """
        use starting node,
        randomly choose next undiscovered neigbhour
        explore
        if stuck call backtrace
        """
        position = []
        while 0 in self.map:
            if self.__has_new_neigbhour():
                pass
            else:
                position = self.__backtrace()
        res = self.walls
        res.append([
            f"\n{self.config[ENTRY][0]},"
            f"{self.config[ENTRY][0]}\n"
            f"{self.config[EXIT][0]}"
            f",{self.config[EXIT][0]}\n"
            ])
        res.append([self.__coords_to_dir()])
        self.__write_output()
    
    @staticmethod
    def __coords_to_dir(coords: list[list]) -> str:
        pass

    def __backtrace(self, path: list) -> list:
        """
        access previous node of path
        if no new field -> go back further repeat
        if new field found, return to explore further
        """
        pass

    def __has_new_neigbhour(self) -> bool:
        pass

    def __write_output(self, result: str) -> None:
        try:
            with open(self.config[OUTPUT_FILE], 'w') as f:
                f.write(result)
        except Exception as e:
            print(f"Couldn't write to file:\n{e}")
