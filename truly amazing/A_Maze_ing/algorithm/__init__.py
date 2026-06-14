"""Public maze algorithm API."""

from .algo_dfs import Dfs
from .algo_kruskal import Kruskal
from .algo_nicki import Sidewinder
from .base import Algorithm, GenerationStep, LogicError
from .states import (
    ALGORITHM,
    ANIMATE,
    COLOR,
    E,
    ENTRY,
    EXIT,
    HEIGHT,
    N,
    OUTPUT_FILE,
    PERFECT,
    S,
    SEED,
    TIME,
    W,
    WEIGHT,
    WIDTH,
)

__all__ = [
    "Algorithm",
    "Dfs",
    "GenerationStep",
    "Kruskal",
    "LogicError",
    "Sidewinder",
    "ALGORITHM",
    "ANIMATE",
    "COLOR",
    "E",
    "ENTRY",
    "EXIT",
    "HEIGHT",
    "N",
    "OUTPUT_FILE",
    "PERFECT",
    "S",
    "SEED",
    "TIME",
    "W",
    "WEIGHT",
    "WIDTH",
]
