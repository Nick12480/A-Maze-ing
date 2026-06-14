"""Shared constants for maze generation, output, and rendering."""

N, E, S, W = 1, 2, 4, 8

DIRECTIONS = (
    (N, 0, -1),
    (E, 1, 0),
    (S, 0, 1),
    (W, -1, 0),
)
OPPOSITE = {N: S, E: W, S: N, W: E}

YELLOW = "\033[38;5;220m"
PURPLE = "\033[38;5;135m"
RED = "\033[38;5;196m"
CYAN = "\033[38;5;51m"
DIM = "\033[38;5;240m"
RESET = "\033[0m"

COLOR = [YELLOW, PURPLE, RED, RESET]

DIGIT_4 = [
    (0, 0),
    (0, 1),
    (0, 2), (1, 2), (2, 2),
    (2, 3),
    (2, 4),
]

DIGIT_2 = [
    (0, 0), (1, 0), (2, 0),
    (2, 1),
    (0, 2), (1, 2), (2, 2),
    (0, 3),
    (0, 4), (1, 4), (2, 4),
]

WIDTH = "WIDTH"
HEIGHT = "HEIGHT"
WEIGHT = "WEIGHT"
SEED = "SEED"
ANIMATE = "ANIMATE"
ENTRY = "ENTRY"
EXIT = "EXIT"
OUTPUT_FILE = "OUTPUT_FILE"
PERFECT = "PERFECT"
ALGORITHM = "ALGORITHM"

TIME = 0.02
