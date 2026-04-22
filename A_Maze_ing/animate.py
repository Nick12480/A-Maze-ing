import sys
import os
from typing import Generator, Optional, Any, Callable
import random
import time

import functools

from maze import Maze
from algorithm import (
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


class Animate:

    @staticmethod
    def animate(output: str, char: str = '█', color: str = RESET) -> dict[str, str]:
        """
        receive standard output as str to generate maze fully
        based on given data, works independently
        """
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

        entry = tuple(int(item) for item in entry.split(','))
        exit = tuple(int(item) for item in exit.split(','))

        path = Animate.__transfer_path(path, entry, exit)

        init_animate = functools.partial(Animate.__display_maze, out_list, entry, exit, path, height, width, char, color=color)

        display = init_animate()

        buff_no_path = []
        buff_path = []

        for i in display:
            buff_no_path.append(i)
            print(i, end='', flush=True)
            time.sleep(TIME)

        os.system('cls' if os.name == 'nt' else 'clear')

        display = init_animate(show_path=True)
        for i in display:
            buff_path.append(i)
            print(i, end='', flush=True)

        return {'path': ''.join(buff_path), 'no_path': ''.join(buff_no_path)}

    @staticmethod
    def __transfer_path(path: str, entry: tuple, exit: tuple) -> list[tuple]:
        """
        changes path str to tuple of respective coordinates
        """
        buff = []
        entry = list(entry)
        for i in path:
            match i:
                case 'N':
                    entry[1] -= 1
                    buff.append((entry[0], entry[1]))
                case 'E':
                    entry[0] += 1
                    buff.append((entry[0], entry[1]))
                case 'S':
                    entry[1] += 1
                    buff.append((entry[0], entry[1]))
                case 'W':
                    entry[0] -= 1
                    buff.append((entry[0], entry[1]))
        if buff[-1] == exit:
            return buff
        raise ValueError("Path doesnt end at exit")

    @staticmethod
    def __display_maze(
        out_list: list,
        entry: tuple,
        exit: tuple,
        path: str,
        height: int,
        width: int,
        char: str,
        color: str = RESET,
        show_path: bool = False
            ) -> Generator[str, None, None]:

        buff = " "
        wall = color + char + RESET

        for y in range(height):
            for x in range(width):

                if (x, y) in path and show_path and (x, y - 1) in path:
                    buff = char
                if Animate.isbit(int(out_list[y][x], 16), N):
                    yield wall + wall
                else:
                    yield wall + buff
                buff = " "

            yield wall + '\n'

            for x in range(width):

                if (x, y) == entry:
                    buff = f"{RED}{char}{RESET}"
                elif (x, y) == exit:
                    buff = f"{RED}{char}{RESET}"
                elif (x, y) in path and show_path:
                    buff = char

                if Animate.isbit(int(out_list[y][x], 16), W):
                    yield wall + buff
                else:
                    if (x, y) in path and show_path and (x - 1, y) in path or (x - 1, y) == entry:
                        yield buff + buff
                    else:
                        yield " " + buff

                buff = " "

            yield wall + '\n'

        yield wall * ((width * 2) + 1) + ' \n'

    @staticmethod
    def isbit(num: int, bit: int) -> bool:
        return (num & bit) == bit

    @staticmethod
    def loop(data: dict[str, str], config: dict = None, color: list = None) -> None:
        curr = data['no_path']
        col = 0
        while True:
            print(
                "\n==== A-Maze-ing ====\n"
                "1. Regenerate maze\n"
                "2. Toggle path\n"
                "3. Rotate colours\n"
                "4. Quit\n"
            )
            choice = input("Choice (1-4): ").strip()

            os.system('cls' if os.name == 'nt' else 'clear')

            match choice:
                case '1':
                    maze = Maze(config)
                    maze.run()
                    return
                case '2':
                    print(curr)
                    if curr == data['path']:
                        curr = data['no_path']
                    else:
                        curr = data['path']
                case '3':
                    global TIME
                    save = TIME
                    TIME = 0
                    data = Animate.animate(config[OUTPUT_FILE], color=color[col])
                    col = (col + 1) % 3
                    TIME = save
                    curr = data['no_path']
                case '4':
                    sys.exit()


if __name__ == '__main__':

    with open('output.txt', 'r') as f:
        # try:
        buff = f.read()
        data = Animate.animate(buff, color=PURPLE)
        while True:
            Animate.loop(data, buff, color=COLOR)
        # except Exception as e:
            # print(e)
