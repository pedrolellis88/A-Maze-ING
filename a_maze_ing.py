from __future__ import annotations

import sys
from pathlib import Path

import mazegen
from src.app import run
from src.model import AppConfig, RenderMode


def _print_usage() -> None:
    print("Usage: python3 a_maze_ing.py <config_file> [--no-render] [--show-path]") # noqa
    print("")
    print("Options:")
    print("  --no-render   Do not print ASCII render")
    print("  --show-path   Render with path overlay (if available)")
    print("  -h, --help    Show this help message")


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    show_path = False
    render_mode = RenderMode.ASCII

    positional: list[str] = []
    for arg in argv:
        if arg in {"-h", "--help"}:
            _print_usage()
            return 0
        if arg == "--no-render":
            render_mode = RenderMode.NONE
            continue
        if arg == "--show-path":
            show_path = True
            continue
        positional.append(arg)

    if len(positional) != 1:
        _print_usage()
        return 1

    config_path = Path(positional[0])

    try:
        choice = {1: 0, 2: 0, 3: 0, 4: 0}
        app_cfg = AppConfig(
            config_path=config_path,
            render_mode=render_mode,
            show_path=show_path,
            print_to_stdout=True,
            choice=choice,
        )
        run(app_cfg)
        print(
            """
            == A-Maze-ing ==
            1- Re-generate a new maze
            2- Show/Hide path from entry to exit
            3- Rotate maze colors
            4- Quit
            """
        )

        input_choice = int(input("Enter your choice (1-4): "))

        while input_choice != 4:

            if int(input_choice) in choice:
                choice[int(input_choice)] += 1

                if int(input_choice) == 2:
                    show_path = not show_path

                app_cfg = AppConfig(
                    config_path=config_path,
                    render_mode=render_mode,
                    show_path=show_path,
                    print_to_stdout=True,
                    choice=choice,
                    )

                run(app_cfg)

                print(
                    """
                    == A-Maze-ing ==
                    1- Re-generate a new maze
                    2- Show/Hide path from entry to exit
                    3- Rotate maze colors
                    4- Quit
                    """
                )
            else:
                print("Invalid choice. Should be 1, 2, 3 or 4.")
            input_choice = int(input("Enter your choice (1-4): "))

        print("Goodbye!")
        return 0

    except ValueError:
        print("Error: input must be a digit between 1 and 4")
        return 0
    except FileNotFoundError:
        print(f"Error: config file not found: {config_path}")
        return 0
    except mazegen.MazeConfigError as exc:
        print(f"Error: invalid configuration: {exc}")
        return 0
    except mazegen.MazeGenerationError as exc:
        print(f"Error: generation failed: {exc}")
        return 0
    except Exception as exc:
        print(f"Error: unexpected failure: {exc}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
