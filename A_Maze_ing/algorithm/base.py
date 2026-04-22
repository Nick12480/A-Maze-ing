

from abc import ABC, abstractmethod
import time
import sys
import random


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

class Algorithm(ABC):

    @abstractmethod
    def __init__(self, config):
        config = config

    @abstractmethod
    def run(self):
        pass

    class Init:

        @staticmethod
        def __init_outer_walls(config: dict) -> list[list]:
            walls = []
            for y in range(config[HEIGHT]):
                for x in range(config[WIDTH]):
                    if y == 0:
                        walls[y][x] |= N
                    elif y == (config[HEIGHT] - 1):
                        walls[y][x] |= S
                    if x == 0:
                        walls[y][x] |= W
                    elif x == (config[WIDTH] - 1):
                        walls[y][x] |= E
            return walls

        @staticmethod
        def __init_pattern(config, walls, field) -> tuple[list, list]:
            """
            Return: (walls, field)
            """
            #TODO right now it just sets top left corner to patterns
            total = N + E + S + W
            for i in DIGIT_2:
                field[i] = 1
                walls[i] = total
            for i in DIGIT_4:
                field[i] = 1
                walls[i] = total
            return(walls, field)


    class Logic:

        @staticmethod
        def __backtrack(path: list) -> list:
            """
            access previous node of path
            if no new field -> go back further repeat
            if new field found, return to explore further
            """
            pass

        @staticmethod
        def __add_walls(walls: list[list], position: tuple, exception: int) -> list[list]:
            """
            add walls to current node except for given directions
            exception: sum of bitwise exceptions

            Return finished walls
            """
            x, y = tuple(position)
            #exception                  0001
            total = N + E + S + W #     1111
            total -= exception #        1110
            walls[y][x] |= total #      1110 + walls[y][x](before)

        @staticmethod
        def __move_direction(direction: str, position: list) -> list:
            """
            directions N, E, S, W
            position = [x, y]

            Return updated position
            """
            position = list(position)
            match direction:
                case 'N':
                    position[1] -= 1
                case 'E':
                    position[0] += 1
                case 'S':
                    position[1] += 1
                case 'W':
                    position[0] -= 1
            return position

        @staticmethod
        def __get_new_neighbour(position: tuple, field: list) -> str:
            """
            check if current cell has undiscoverd neighbours

            returns: one random direction as str
            """
            x, y = position
            poss = [None]
            neighbour = None

            if field[y + 1][x]:
                poss.append((1, 0))
            if field[y - 1][x]:
                poss.append((-1, 0))
            if field[y][x + 1]:
                poss.append((0, 1))
            if field[y][x - 1]:
                poss.append((0, -1))

            if poss[0] is not None:
                neighbour = poss[int(random.random) % len(poss)]
            return neighbour

        @staticmethod
        def __adjust_to_neighbour():
            pass

    class Output:

        @staticmethod
        def __coords_to_dir(coords: list[list]) -> str:
            """
            change coords into N, E, S, W directions
            coords = [[x1,y1], [x2,y2], ...]
            """
            res = ""
            for i in coords:
                if i[0] == 1:
                    res += 'S'
                elif i[0] == -1:
                    res += 'N'
                elif i[1] == 1:
                    res += 'E'
                elif i[1] == -1:
                    res += 'W'

        @staticmethod
        def __write_output(self, result: str) -> None:
            try:
                with open(self.config[OUTPUT_FILE], 'w') as f:
                    f.write(result)
            except Exception as e:
                print(f"Couldn't write to file:\n{e}")
