def parse_config(filepath: str) -> dict:
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
    print(f"Maze: {width}x{height}")
    print(f"Entry: {entry}, Exit: {exit}")
    print(f"Output: {output_file}, Perfect: {perfect}")


def main():
    try:
        config = parse_config("config.txt")
        width, height, entry, exit_coord, \
            output_file, perfect = convert_config(config)
        process_maze(width, height, entry, exit_coord, output_file, perfect)

    except (FileNotFoundError, KeyError, ValueError):
        print("Programm wird beendet.")


main()
