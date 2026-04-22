

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
        def _init_outer_walls(config: dict) -> list[list]:
            walls = []
            for y in range(config[HEIGHT]):
                walls.append([])
                for x in range(config[WIDTH]):
                    walls[y].append(0)

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
        def _init_pattern(config, walls, field) -> tuple[list, list]:
            """
            Return: (walls, field)
            """
            #TODO right now it just sets top left corner to patterns
            total = N + E + S + W
            for i in DIGIT_2:
                x, y = i
                field[y][x] = 1
                walls[y][x] = total
            for i in DIGIT_4:
                x, y = i
                field[y][x] = 1
                walls[y][x] = total
            return(walls, field)


    class Logic:

        @staticmethod
        def _backtrack(path: list) -> tuple:
            """
            access previous node of path
            if no new field -> go back further repeat
            if new field found, return to explore further
            """

            path.pop(-1)
            return (path[-1], path)

        @staticmethod
        def _add_walls(walls: list[list], position: tuple, exception: int) -> list[list]:
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
        def _move_direction(direction: int, position: list) -> list:
            """
            directions N, E, S, W
            position = [x, y]

            Return updated position
            """
            position = list(position)
            if direction == N:
                position[1] -= 1
            if direction == E:
                position[0] += 1
            if direction == S:
                position[1] += 1
            if direction == W:
                position[0] -= 1
            return position

        @staticmethod
        def _get_new_neighbour(position: tuple, field: list) -> int:
            """
            check if current cell has undiscoverd neighbours

            returns: one random direction bitwise int
            """
            x, y = position
            poss = [None]
            neighbour = None

            if field[y + 1][x]:
                poss.append(S)
            if field[y - 1][x]:
                poss.append(N)
            if field[y][x + 1]:
                poss.append(E)
            if field[y][x - 1]:
                poss.append(W)

            if poss[0] is not None:
                neighbour = poss[int(random.random) % len(poss)]
            return neighbour

        @staticmethod
        def _adjust_to_neighbour(position: tuple, field: list) -> list:
            x, y = position
            if field[y][x + 1] & W:
                field[x][y] |= E
            if field[y][x - 1] & E:
                field[x][y] |= W
            if field[y + 1][x] & N:
                field[x][y] |= S
            if field[y - 1][x] & S:
                field[x][y] |= N
            return field
            

    class Output:

        @staticmethod
        def _coords_to_dir(final_path: list[list]) -> str:
            """
            change coords into N, E, S, W directions
            coords = [[x1,y1], [x2,y2], ...]
            """
            res = ""
            for i in final_path:
                prev_i = i
                if i == final_path[0]:
                    continue
                if (i - prev_i) == (0, 1):
                    res += 'S'
                elif (i - prev_i) == (0, -1):
                    res += 'N'
                elif (i - prev_i) == (1, 0):
                    res += 'E'
                elif (i - prev_i) == (-1, 0):
                    res += 'W'
            return res

        @staticmethod
        def _write_output(output_file: str, result: str) -> None:
            try:
                with open(output_file, 'w') as f:
                    f.write(result)
            except Exception as e:
                print(f"Couldn't write to file:\n{e}")
