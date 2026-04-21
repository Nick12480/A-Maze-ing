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

    

    @timer
    def run(self):
        pass

