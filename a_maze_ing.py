from __future__ import annotations

import sys
from pathlib import Path

from mazegen import (
    MazeConfig,
    MazeGenerator,
    MazeConfigError,
    MazeGenerationError,
)


def _print_usage() -> None:
    print("Usage: python3 a_maze_ing.py <config_file>")


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) != 1:
        _print_usage()
        return 1

    config_path = Path(argv[0])

    try:
        cfg = MazeConfig.from_file(config_path)
        gen = MazeGenerator(cfg)

        maze = gen.generate()
        path = gen.solve_shortest_path()

        print(gen.render_ascii(maze, show_path=False, path=path))

        gen.write_output_file(maze=maze, path=path)

    except FileNotFoundError:
        print(f"Error: config file not found: {config_path}")
        return 1
    except MazeConfigError as e:
        print(f"Error: invalid configuration: {e}")
        return 1
    except MazeGenerationError as e:
        print(f"Error: generation failed: {e}")
        return 1
    except Exception as e:
        print(f"Error: unexpected failure: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
