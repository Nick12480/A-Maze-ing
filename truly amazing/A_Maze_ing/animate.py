"""Buffered ANSI terminal animation driven by yielded algorithm events."""

import sys
import time
from typing import Dict, Generator, Iterable, List, Optional, TextIO

from .algorithm import Algorithm, GenerationStep
from .algorithm.states import E, RESET, S

BLOCK = "  "
BG_WALL = "\033[48;5;255m"
BG_EMPTY = "\033[48;5;232m"
BG_PATTERN = "\033[48;5;250m"
BG_PATH = "\033[48;5;214m"
BG_ENTRY = "\033[48;5;93m"
BG_EXIT = "\033[48;5;160m"
BG_CURRENT = "\033[48;5;45m"
FG_STATUS = "\033[38;5;250m"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
DISABLE_WRAP = "\033[?7l"
ENABLE_WRAP = "\033[?7h"
CLEAR_SCREEN = "\033[2J"
CURSOR_HOME = "\033[H"
ERASE_LINE_END = "\033[K"
SYNC_BEGIN = "\033[?2026h"
SYNC_END = "\033[?2026l"

# ---------------------------------------------------------------------------
# Colour palettes – each dict must contain all seven canvas-cell keys.
# The first entry is the default; interactive_menu cycles through all of them.
# ---------------------------------------------------------------------------
_PALETTES: List[Dict[str, str]] = [
    # 0 – original dark theme
    {
        "wall":    BG_WALL,
        "empty":   BG_EMPTY,
        "pattern": BG_PATTERN,
        "path":    BG_PATH,
        "entry":   BG_ENTRY,
        "exit":    BG_EXIT,
        "current": BG_CURRENT,
    },
    # 1 – blue-green theme
    {
        "wall":    "\033[48;5;24m",
        "empty":   "\033[48;5;17m",
        "pattern": "\033[48;5;31m",
        "path":    "\033[48;5;46m",
        "entry":   "\033[48;5;51m",
        "exit":    "\033[48;5;196m",
        "current": "\033[48;5;226m",
    },
    # 2 – warm red-gold theme
    {
        "wall":    "\033[48;5;130m",
        "empty":   "\033[48;5;52m",
        "pattern": "\033[48;5;94m",
        "path":    "\033[48;5;220m",
        "entry":   "\033[48;5;46m",
        "exit":    "\033[48;5;201m",
        "current": "\033[48;5;255m",
    },
    # 3 – greyscale theme
    {
        "wall":    "\033[48;5;250m",
        "empty":   "\033[48;5;235m",
        "pattern": "\033[48;5;244m",
        "path":    "\033[48;5;255m",
        "entry":   "\033[48;5;240m",
        "exit":    "\033[48;5;232m",
        "current": "\033[48;5;15m",
    },
]

# Active palette used by _render_row; replaced at runtime by interactive_menu.
_palette_idx = 0


class AnsiAnimator:
    """Render any maze algorithm without coupling rendering to generation."""

    def __init__(
        self,
        delay: float = 0.02,
        stream: Optional[TextIO] = None,
    ) -> None:
        """Store frame delay and destination terminal stream."""
        self.delay = delay
        self.stream = sys.stdout if stream is None else stream

    def frames(
        self,
        algorithm: Algorithm,
        steps: Iterable[GenerationStep],
    ) -> Generator[str, None, None]:
        """Yield ANSI frames adapted to events from a maze algorithm."""
        first_frame = True
        for step in steps:
            yield self._buffer_frame(
                self.render(
                    algorithm,
                    current=step.current,
                    action=step.action,
                    show_path=False
                ),
                clear=first_frame,
                hide_cursor=first_frame,
            )
            first_frame = False

    def play(
        self,
        algorithm: Algorithm,
        steps: Iterable[GenerationStep],
    ) -> None:
        """Print yielded ANSI frames and finish on the solved maze."""
        wrote_frame = False
        try:
            for frame in self.frames(algorithm, steps):
                self.stream.write(frame)
                self.stream.flush()
                wrote_frame = True
                if self.delay:
                    time.sleep(self.delay)
            self.stream.write(
                self._buffer_frame(
                    self.render(algorithm, action="shortest path"),
                    clear=not wrote_frame,
                    hide_cursor=not wrote_frame,
                )
            )
            self.stream.flush()
        finally:
            self.stream.write(
                SYNC_END + ENABLE_WRAP + SHOW_CURSOR + RESET + "\n"
            )
            self.stream.flush()

    @staticmethod
    def render(
        algorithm: Algorithm,
        current: Optional[tuple] = None,
        action: str = "",
        show_path: bool = True,
    ) -> str:
        """Return one buffered, background-colored ANSI maze frame."""
        rows = algorithm.height * 2 + 1
        columns = algorithm.width * 2 + 1
        canvas = [["wall" for _ in range(columns)] for _ in range(rows)]

        for x, y in algorithm.cells():
            center_x = x * 2 + 1
            center_y = y * 2 + 1
            canvas[center_y][center_x] = "empty"
            if algorithm.passages[y][x] & E:
                canvas[center_y][center_x + 1] = "empty"
            if algorithm.passages[y][x] & S:
                canvas[center_y + 1][center_x] = "empty"

        for x, y in algorithm.pattern:
            canvas[y * 2 + 1][x * 2 + 1] = "pattern"

        if show_path:
            AnsiAnimator._draw_path(canvas, algorithm.path)
        if current is not None:
            x, y = current
            canvas[y * 2 + 1][x * 2 + 1] = "current"
        entry_x, entry_y = algorithm.entry
        exit_x, exit_y = algorithm.exit
        canvas[entry_y * 2 + 1][entry_x * 2 + 1] = "entry"
        canvas[exit_y * 2 + 1][exit_x * 2 + 1] = "exit"

        lines = [AnsiAnimator._render_row(row) for row in canvas]
        status = "{}{} | {}{}".format(
            FG_STATUS,
            algorithm.name.upper(),
            action,
            RESET,
        )
        lines.append(status + ERASE_LINE_END)
        return "\n".join(lines)

    @staticmethod
    def _buffer_frame(
        frame: str,
        clear: bool = False,
        hide_cursor: bool = False,
    ) -> str:
        """Wrap one frame in synchronized terminal update controls."""
        prefix = HIDE_CURSOR + DISABLE_WRAP if hide_cursor else ""
        prefix += SYNC_BEGIN
        if clear:
            prefix += CLEAR_SCREEN
        return prefix + CURSOR_HOME + frame + SYNC_END

    @staticmethod
    def _render_row(row: List[str]) -> str:
        """Render one maze row while minimizing ANSI color transitions."""
        parts = []
        active = ""
        for cell in row:
            color = _PALETTES[_palette_idx][cell]
            if color != active:
                parts.append(color)
                active = color
            parts.append(BLOCK)
        parts.append(RESET)
        return "".join(parts)

    @staticmethod
    def _draw_path(canvas: List[List[str]], path: List[tuple]) -> None:
        """Color path cells and the passages joining consecutive cells."""
        for x, y in path:
            canvas[y * 2 + 1][x * 2 + 1] = "path"
        for first, second in zip(path, path[1:]):
            between_x = first[0] + second[0] + 1
            between_y = first[1] + second[1] + 1
            canvas[between_y][between_x] = "path"
