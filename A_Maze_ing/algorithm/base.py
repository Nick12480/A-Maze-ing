

from abc import ABC, abstractmethod
import time
import sys
import random
from typing import Any
from reprlib import repr as short_repr


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
    TIME,
    RED,
    COLOR,
    HEX
)

class LogicError(Exception):
    """
    Raised when maze generation reaches an impossible or invalid logic state.

    Extra variables can be passed as keyword arguments and later read from
    error.context.
    """

    def __init__(self, message: str, **context: Any) -> None:
        self.message = message
        self.context = context
        super().__init__(message)

    def __str__(self) -> str:
        if not self.context:
            return self.message

        details = ":\t".join(
            f"{name}={short_repr(value)}"
            for name, value in self.context.items()
        )

        return f"{self.message} | {details}"

class Algorithm(ABC):

    @abstractmethod
    def __init__(self, config):
        config = config

    @abstractmethod
    def run(self):
        pass

    class Init:

        @staticmethod
        def _init_outer_walls(width: int, height: int) -> list[list]:
            """
            Create matrix of given size where edges are respective walls in bitwise

            Returns
            -------
                walls matrix
            """
            if width == 0 or height == 0:
                raise LogicError("impossible size of maze")
            walls = []
            for y in range(height):
                walls.append([])
                for x in range(width):
                    walls[y].append(0)

            for y in range(height):
                for x in range(width):
                    if y == 0:
                        walls[y][x] |= N
                    if y == (height - 1):
                        walls[y][x] |= S
                    if x == 0:
                        walls[y][x] |= W
                    if x == (width - 1):
                        walls[y][x] |= E
            return walls

        @staticmethod
        def _init_pattern(width: int, height: int, walls: list[list], field: list[list]) -> tuple[list, list]:
            """
            Init 42 pattern in walls matrix

            Return: (walls, field)

            Params
            ------
            walls : matrix with bitwise walls
            field : matrix of 0/1 for discovered cells
            """
            if width < 7 and height < 9:
                raise LogicError("Size too small for 42-pattern")
            x_mod = int((width / 2) - 4)
            y_mod = int((height / 2) - 3)

            try:
                total = N + E + S + W
                for i in DIGIT_4:
                    x, y = i
                    x += x_mod
                    y += y_mod
                    field[y][x] = 1
                    walls[y][x] = total
                for i in DIGIT_2:
                    x, y = i
                    x += 4
                    x += x_mod
                    y += y_mod
                    field[y][x] = 1
                    walls[y][x] = total
            except IndexError:
                raise LogicError(
                    "Parameters not initialized as required",
                    walls=walls,
                    field=field,
                    x=x,
                    y=y
                )

            return(walls, field)


    class Logic:

        @staticmethod
        def _backtrack(path: list[list]) -> tuple:
            """
            access previous node of path

            path : previous order of positions from entry

            Returns
            -------
            path[-1] : new position
            path : updated path
            """
            try:
                path.pop(-1)
                return (tuple(path[-1]), path)
            except IndexError:
                print("Maze start inside of enclosed block\nTERMINATING")
                sys.exit(1)

        @staticmethod
        def _add_walls(walls: list[list], position: tuple, exception: int) -> list[list]:
            """
            add walls to current node except for given directions

            Return finished walls

            Params
            ------
            walls : matrix of bitwise walls
            position : (x, y)
            exception : sum of bitwise exceptions
            """
            x, y = tuple(position)
            #exception                  0001
            total = N + E + S + W #     1111
            total -= exception #        1110
            walls[y][x] |= total #      1110 + walls[y][x](before)
            return walls

        @staticmethod
        def _move_direction(direction: int, position: tuple) -> tuple:
            """
            update position toward direction

            Params
            ------
            directions : N, E, S, W
            position : (x, y)

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
            return tuple(position)

        @staticmethod
        def _get_new_neighbour(width: int, height: int, position: tuple, field: list) -> int:
            """
            get bitwise direction of any undiscovered neighbour

            Params
            ------
            position : (x, y)
            field : matrix of 0/1 for discovered cells

            Returns one random direction bitwise int
            """
            x, y = position
            poss = []
            neighbour = None

            if (height - 1) > y and field[y + 1][x] == 0:
                poss.append(S)
            if y > 0 and field[y - 1][x] == 0:
                poss.append(N)
            if (width - 1) > x and field[y][x + 1] == 0:
                poss.append(E)
            if x > 0 and field[y][x - 1] == 0:
                poss.append(W)

            poss.append(0)
            if poss[0] != 0:
                poss.pop(-1)
                neighbour = poss[int(random.randint(1, 1000) % len(poss))]
            return neighbour

        @staticmethod
        def _adjust_to_neighbour(width: int, height: int, walls: list[list], position: tuple) -> list[list]:
            """
            Add walls depending on neighbours walls

            Params
            ------
            walls : matrix of bitwise walls
            position : (x, y)

            returns walls
            """
            x, y = position
            if (width - 1) > x and walls[y][x + 1] & W:
                walls[y][x] |= E
            if x > 0 and walls[y][x - 1] & E:
                walls[y][x] |= W
            if (height - 1) > y and walls[y + 1][x] & N:
                walls[y][x] |= S
            if y > 0 and walls[y - 1][x] & S:
                walls[y][x] |= N
            return walls
            

    class Output:

        @staticmethod
        def _walls_to_hex(walls: list[list[int]]) -> list[list[str]]:
            """
            change walls[int] matrix to walls[hex]
            """
            hex_walls = []
            for y, i in enumerate(walls):
                hex_walls.append([])
                for num in i:
                    hex_walls[y].append(HEX[num % 16])
            return hex_walls

        @staticmethod
        def _walls_to_str(walls: list[list[str]]) -> str:
            """
            change walls[hex] matrix to single str
            """
            res = ''
            for y in walls:
                res += ''.join(y)
                res += '\n'
            return res

        @staticmethod
        def _coords_to_dir(final_path: list[list]) -> str:
            """
            change coords in path into N, E, S, W directions

            final_path : [[x1,y1], [x2,y2], ...]
            """
            final_path = list(final_path)
            for i, coord in enumerate(final_path):
                final_path[i] = list(coord)
            res = ""
            for i in final_path:
                
                if i == final_path[0]:
                    prev_i = i
                    continue
                calc = [a_i - b_i for a_i, b_i in zip(i, prev_i)]
                if calc == [0, 1]:
                    res += 'S'
                elif calc == [0, -1]:
                    res += 'N'
                elif calc == [1, 0]:
                    res += 'E'
                elif calc == [-1, 0]:
                    res += 'W'
                prev_i = i
            return res

        @staticmethod
        def _write_output(output_file: str, result: str) -> None:
            """
            write str to file
            """
            try:
                with open(output_file, 'w') as f:
                    f.write(result)
            except Exception as e:
                print(f"Couldn't write to file:\n{e}")
                raise


if __name__ == "__main__":
    res = Algorithm.Init._init_outer_walls(1, 0)
    for i in res:
        print(i)
    # Algorithm.Init._init_pattern()

    # Algorithm.Logic._add_walls()
    # Algorithm.Logic._adjust_to_neighbour()
    # Algorithm.Logic._backtrack()
    # Algorithm.Logic._get_new_neighbour()
    # Algorithm.Logic._move_direction()

    # Algorithm.Output._coords_to_dir()
    # Algorithm.Output._walls_to_hex()
    # Algorithm.Output._walls_to_str()
    # Algorithm.Output._write_output()
    