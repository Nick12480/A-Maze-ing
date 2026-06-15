"""Command-line entry point for A-Maze-ing."""

import random
import sys
from typing import Dict, List, Optional, Tuple, cast

from algorithm import (
    ALGORITHM,
    ANIMATE,
    Algorithm,
    ENTRY,
    EXIT,
    HEIGHT,
    LogicError,
    OUTPUT_FILE,
    PERFECT,
    SEED,
    WEIGHT,
    WIDTH,
)
from animate import AnsiAnimator, ERASE_LINE_END, RESET, _PALETTES
from maze import Maze

DEFAULTS: Dict[str, object] = {
    WEIGHT: 1,
    SEED: None,
    ANIMATE: True,
    OUTPUT_FILE: "output_maze.txt",
    PERFECT: False,
    ALGORITHM: "sidewinder",
}
REQUIRED_KEYS = (WIDTH, HEIGHT, ENTRY, EXIT)
KNOWN_KEYS = set(DEFAULTS) | set(REQUIRED_KEYS)


def parse_config(filepath: str) -> Dict[str, object]:
    """Read key-value configuration text while ignoring comments."""
    config: Dict[str, object] = {}
    with open(filepath, "r", encoding="utf-8") as config_file:
        for raw_line in config_file:
            line = raw_line.split("#", 1)[0].strip()
            if not line:
                continue
            if "=" not in line:
                raise ValueError("Invalid config line: {!r}".format(raw_line))
            key, value = line.split("=", 1)
            config[key.strip().upper()] = value.strip()
    return config


def parse_bool(value: object, key: str) -> bool:
    """Parse a strict textual or native boolean config value."""
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes", "on"}:
        return True
    if normalized in {"false", "0", "no", "off"}:
        return False
    raise ValueError("{} must be true or false.".format(key))


def parse_coordinate(value: object, key: str) -> Tuple[int, int]:
    """Parse a coordinate in ``x,y`` form."""
    raw_parts = (
        value
        if isinstance(value, (list, tuple))
        else str(value).split(",")
    )
    if len(raw_parts) != 2:
        raise ValueError("{} must use x,y format.".format(key))
    try:
        parts = tuple(int(str(part).strip()) for part in raw_parts)
    except (TypeError, ValueError) as error:
        raise ValueError("{} must contain integers.".format(key)) from error
    return parts  # type: ignore[return-value]


def validate_config(raw_config: Dict[str, object]) -> Dict[str, object]:
    """Normalize config types and enforce all maze preconditions."""
    unknown = sorted(set(raw_config) - KNOWN_KEYS)
    if unknown:
        raise ValueError("Unknown config keys: {}.".format(", ".join(unknown)))
    config = dict(DEFAULTS)
    config.update(raw_config)
    missing = [key for key in REQUIRED_KEYS if key not in config]
    if missing:
        raise ValueError("Missing config keys: {}".format(", ".join(missing)))

    for key in (WIDTH, HEIGHT, WEIGHT):
        config[key] = int(cast(str, config[key]))
    if cast(int, config[WIDTH]) < 2 or cast(int, config[HEIGHT]) < 2:
        raise ValueError("WIDTH and HEIGHT must be at least 2.")
    if not 1 <= cast(int, config[WEIGHT]) <= 10:
        raise ValueError("WEIGHT must be between 1 and 10.")

    seed = config[SEED]
    config[SEED] = (
        random.SystemRandom().randrange(0, 2 ** 32)
        if seed is None
        else int(cast(str, seed))
    )
    if cast(int, config[SEED]) < 0:
        raise ValueError("SEED cannot be negative.")

    config[ANIMATE] = parse_bool(config[ANIMATE], ANIMATE)
    config[PERFECT] = parse_bool(config[PERFECT], PERFECT)
    config[ENTRY] = parse_coordinate(config[ENTRY], ENTRY)
    config[EXIT] = parse_coordinate(config[EXIT], EXIT)
    if config[ENTRY] == config[EXIT]:
        raise ValueError("ENTRY and EXIT must be different.")

    width = cast(int, config[WIDTH])
    height = cast(int, config[HEIGHT])
    for key in (ENTRY, EXIT):
        coord = cast(Tuple[int, int], config[key])
        x, y = coord
        if not 0 <= x < width or not 0 <= y < height:
            raise ValueError("{} lies outside the maze.".format(key))

    algorithm = str(config[ALGORITHM]).strip().lower()
    if algorithm not in Maze.algorithms:
        choices = ", ".join(sorted(Maze.algorithms))
        raise ValueError("ALGORITHM must be one of: {}.".format(choices))
    config[ALGORITHM] = algorithm
    output_file = config[OUTPUT_FILE]
    config[OUTPUT_FILE] = "" if output_file is None else str(output_file)
    candidate = Maze(config).create()
    if not candidate.pattern:
        print("\033[31mError: Maze size is too small to "
              "allow the '42' pattern. Omiting pattern.\033[0m",
              file=sys.stderr)

    candidate = Maze(config).create()
    endpoint_in_pattern = (
        candidate.entry in candidate.pattern
        or candidate.exit in candidate.pattern
    )
    if endpoint_in_pattern:
        raise ValueError("ENTRY and EXIT cannot overlap the 42 pattern.")
    if (
        not bool(config[PERFECT])
        and not candidate.can_have_multiple_solutions()
    ):
        raise ValueError(
            "ENTRY and EXIT cannot have multiple paths on this grid."
        )
    return config


def print_final(algorithm: Algorithm) -> None:
    """Print the final solved maze and concise run metadata."""
    print(AnsiAnimator.render(algorithm))
    print(
        "Algorithm: {} | {}x{} | seed={} | perfect={}".format(
            algorithm.name,
            algorithm.width,
            algorithm.height,
            algorithm.config[SEED],
            algorithm.config[PERFECT],
        )
    )


def interactive_menu(config: Dict[str, object]) -> None:
    """Run the interactive terminal menu for maze exploration.

    Switches to the alternate screen buffer so the main terminal history is
    preserved, then lets the user regenerate, toggle the solution path, and
    cycle through colour palettes – all without leaving the program.
    """
    import animate as _animate_module

    # ── state ──────────────────────────────────────────────────────────────
    show_path: bool = True
    palette_idx: int = 0
    pattern_error: str = ""  # Speichert die Fehlermeldung für das UI

    animator = AnsiAnimator(delay=0.02 if sys.stdout.isatty() else 0.0)

    def _rebuild(new_seed: Optional[int] = None) -> Algorithm:
        """Create and fully generate a fresh Algorithm instance."""
        nonlocal pattern_error
        if new_seed is not None:
            config[SEED] = new_seed
        algorithm = Maze(config).create()

        if not algorithm.pattern:
            pattern_error = ("\033[31m[ERROR] Maze size too small:"
                             " '42' pattern omitted!\033[0m\n")
        else:
            pattern_error = ""

        if bool(config[ANIMATE]):
            animator.play(algorithm, algorithm.steps())
        else:
            algorithm.run()
        return algorithm

    def _display(algorithm: Algorithm) -> None:
        """Render the current maze to stdout respecting show_path."""
        frame = AnsiAnimator.render(algorithm, show_path=show_path)
        sys.stdout.write("\033[2J\033[H" + frame + "\n")
        sys.stdout.flush()

    # ── enter alternate screen ─────────────────────────────────────────────
    sys.stdout.write("\033[?1049h\033[?25l")
    sys.stdout.flush()

    try:
        algorithm = _rebuild()
        running = True

        while running:
            _display(algorithm)
            sys.stdout.write(
                "\n\033[1m==== A-Maze-ing ====\033[0m\n"
                "Seed: {seed}  |  Palette: {pal}/{total}\n"
                "{err}"  # Platzhalter für die Fehlermeldung
                "\n"
                "1. Regenerate (same seed)\n"
                "2. Regenerate (new seed)\n"
                "3. Toggle path  [{path}]\n"
                "4. Rotate colours\n"
                "5. Quit\n"
                "{eol}".format(
                    seed=config[SEED],
                    pal=palette_idx + 1,
                    total=len(_PALETTES),
                    err=pattern_error,
                    path="ON" if show_path else "OFF",
                    eol=ERASE_LINE_END,
                )
            )
            sys.stdout.flush()

            choice = input("Choice (1-5): ").strip()

            if choice == "1":
                algorithm = _rebuild()

            elif choice == "2":
                new_seed = (cast(int, config[SEED]) + 1) % (2 ** 32)
                algorithm = _rebuild(new_seed=new_seed)

            elif choice == "3":
                show_path = not show_path

            elif choice == "4":
                # Unser sauberer Index-Fix bleibt erhalten!
                palette_idx = (palette_idx + 1) % len(_PALETTES)
                _animate_module._palette_idx = palette_idx

            elif choice == "5":
                running = False

    finally:
        # Always restore the normal screen and cursor on exit
        sys.stdout.write("\033[?1049l\033[?25h" + RESET + "\n")
        sys.stdout.flush()
        print("Goodbye!")


def main(argv: Optional[List[str]] = None) -> int:
    """Validate CLI config, generate the maze, and render its solution.

    Pass ``--interactive`` as the second argument to enter the interactive
    menu instead of the one-shot render::

        python3 -m A_Maze_ing.a_maze_ing config.txt --interactive
    """
    arguments = sys.argv[1:] if argv is None else argv

    interactive = "--interactive" in arguments
    positional = [a for a in arguments if a != "--interactive"]

    if len(positional) != 1:
        print(
            "Usage: python3 -m A_Maze_ing.a_maze_ing <config> [--interactive]",
            file=sys.stderr,
        )
        return 1

    try:
        config = validate_config(parse_config(positional[0]))

        if interactive:
            interactive_menu(config)
            return 0

        maze = Maze(config)
        algorithm = maze.create()
        if bool(config[ANIMATE]):
            delay = 0.02 if sys.stdout.isatty() else 0.0
            AnsiAnimator(delay=delay).play(algorithm, algorithm.steps())
            output_file = str(config[OUTPUT_FILE])
            if output_file:
                algorithm.write_output(output_file)
        else:
            algorithm.run()
            print_final(algorithm)

    except (LogicError, OSError, TypeError, ValueError) as error:
        print("Error: {}".format(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
