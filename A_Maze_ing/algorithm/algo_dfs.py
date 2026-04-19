import sys
from typing import Generator, Optional, Any, Callable
import random
import time

from states import (
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
    ALGORITHM
)


def timer(func: Callable) -> Callable:
    def wrapper(*args, **kwargs):
        start = time.time()
        func(*args, **kwargs)
        end = time.time()
        print(f"\nfinished {func.__name__} in {round(end - start, 4)}s")
    return wrapper


class Maze:
    """
    look for random undiscovered area next to current
    explore, repeat
    if at dead end, backtrace to first undiscovered nearby block

    if nearby block is = NESW its undiscovered
    """

    def __init__(self, config: dict[str: Any]):
        self.config = config


    @timer
    def run(self):
        pass

    @staticmethod
    def animate(output: str, char: str) -> None:
        """
        receive standard output as str to generate maze fully
        based on given data, works independently
        """
        height = 0
        out_list = [item for item in output.split('\n')]
        width = len(out_list[0])
        for count, i in enumerate(out_list):
            if i == '':
                height = count
                break

        buff = []
        top = ""
        curr = ""

        for y in range(height):
            for x in range(width):
                if Maze.isbit(int(out_list[y][x], 16), N):
                    top += char + char
                else:
                    top += char + " "

                if Maze.isbit(int(out_list[y][x], 16), W):
                    curr += char + " "
                else:
                    curr += "  "
            buff.append(top + char)
            buff.append(curr + char)
            top = ""
            curr = ""
        buff.append(char * (width * 2 + 1))

        for i in buff:
            print(i)

    @staticmethod
    def isbit(num: int, bit: int) -> bool:
        return (num & bit) == bit


if __name__ == '__main__':

    with open('output.txt', 'r') as f:
        # print(f.read())
        Maze.animate(f.read(), '█')
