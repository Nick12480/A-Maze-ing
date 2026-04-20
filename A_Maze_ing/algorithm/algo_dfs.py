import sys
import os
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
    ALGORITHM,
    TIME
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


class Animate:

    @staticmethod
    def animate(output: str, char: str) -> None:
        """
        receive standard output as str to generate maze fully
        based on given data, works independently
        """
        entry = ""
        exit = ""
        path = ""
        height = 0
        out_list = [item for item in output.split('\n')]
        width = len(out_list[0])
        for i, item in enumerate(out_list):
            if item == '':
                height = i
                entry = out_list[i + 1]
                exit = out_list[i + 2]
                path = out_list[i + 3]
                break

        entry = (int(item) for item in entry.split(','))
        exit = (int(item) for item in exit.split(','))

        buff = Animate.__animate_build_maze(out_list, height, width, char)

    @staticmethod
    def __animate_build_maze(out_list: list, height: int, width: int, char: str) -> list:
        buff = []
        top = ""
        curr = ""
        for y in range(height):
            for x in range(width):
                if Animate.isbit(int(out_list[y][x], 16), N):
                    top += char + char
                    print(char + char, end='', file=sys.stdout, flush=True)
                else:
                    top += char + " "
                    print(char + " ", end='', file=sys.stdout, flush=True)
                time.sleep(TIME)

            buff.append(top + char)
            print(char)
            top = ""

            for x in range(width):
                if Animate.isbit(int(out_list[y][x], 16), W):
                    curr += char + " "
                    print(char + " ", end='', file=sys.stdout, flush=True)
                else:
                    curr += "  "
                    print("  ", end='', file=sys.stdout, flush=True)
                time.sleep(TIME)

            buff.append(curr + char)
            print(char)
            curr = ""

        buff.append(char * (width * 2 + 1))
        os.system('cls' if os.name == 'nt' else 'clear')

        for i in buff:
            print(i)

    @staticmethod
    def isbit(num: int, bit: int) -> bool:
        return (num & bit) == bit


if __name__ == '__main__':

    with open('output.txt', 'r') as f:
        # print(f.read())
        Animate.animate(f.read(), '█')
