def parse_config(filepath: str) -> dict:
    """Parse a configuration file into a dictionary.

    Reads a plain-text config file where each line follows the format
    'KEY = VALUE'. Lines starting with '#' and empty lines are ignored.
    Args:
        filepath: Path to the configuration file.
    Returns:
        A dictionary mapping configuration keys to their string values.
    Raises:
        FileNotFoundError: If the file at filepath does not exist.
        ValueError: If a line contains no '=' separator.
    """
    config = {}

    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()

                if not line or line.startswith('#'):
                    continue

                if '=' not in line:
                    raise ValueError(f"Ungültige Zeile: '{line}'")

                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()

    except FileNotFoundError:
        print(f"Fehler: Datei '{filepath}' nicht gefunden.")
        raise
    except ValueError as e:
        print(f"Fehler beim Parsen: {e}")
        raise

    return config


def convert_config(config: dict) -> tuple:
    """Convert a raw config dictionary into typed maze parameters.

    Validates that all required keys are present and converts each value
    to its expected type (int, tuple, str, bool).
    Args:
        config: Dictionary of string key-value pairs from parse_config().
    Returns:
        A tuple of (width, height, entry, exit_coord, output_file, perfect):
            - width (int): Maze width in cells.
            - height (int): Maze height in cells.
            - entry (tuple): Entry coordinates as (row, col).
            - exit_coord (tuple): Exit coordinates as (row, col).
            - output_file (str): Path for the output file.
            - perfect (bool): Whether to generate a perfect maze.
    Raises:
        KeyError: If a required key is missing from config.
        ValueError: If a value cannot be converted to its expected type.
    """
    required_keys = [
        'WIDTH', 'HEIGHT', 'ENTRY', 'EXIT', 'OUTPUT_FILE', 'PERFECT'
        ]

    try:
        for key in required_keys:
            if key not in config:
                raise KeyError(f"Pflichtfeld fehlt: '{key}'")

        width = int(config['WIDTH'])
        height = int(config['HEIGHT'])
        entry = tuple(map(int, config['ENTRY'].split(',')))
        exit_coord = tuple(map(int, config['EXIT'].split(',')))
        output_file = config['OUTPUT_FILE']
        perfect = config['PERFECT'].lower() == 'true'

    except KeyError as e:
        print(f"Fehler: {e}")
        raise
    except ValueError as e:
        print(f"Fehler bei Typkonvertierung: {e}")
        raise

    return width, height, entry, exit_coord, output_file, perfect


def process_maze(width: int, height: int, entry: tuple,
                 exit: tuple, output_file: str, perfect: bool):
    """Process and display maze configuration parameters.

    Prints the maze dimensions, entry and exit coordinates, output path,
    and whether the maze should be generated as a perfect maze.
    Args:
        width: Maze width in cells.
        height: Maze height in cells.
        entry: Entry coordinates as (row, col).
        exit: Exit coordinates as (row, col).
        output_file: Path for the output file.
        perfect: Whether to generate a perfect maze.
    """
    print(f"Maze: {width}x{height}")
    print(f"Entry: {entry}, Exit: {exit}")
    print(f"Output: {output_file}, Perfect: {perfect}")


def main():
    """Run the maze configuration pipeline.

    Parses the config file, converts values to the correct types, and
    passes them to the maze processor. Exits gracefully on known errors.
    """
    try:
        config = parse_config("config.txt")
        width, height, entry, exit_coord, \
            output_file, perfect = convert_config(config)
        process_maze(width, height, entry, exit_coord, output_file, perfect)

    except (FileNotFoundError, KeyError, ValueError):
        print("Programm wird beendet.")


main()