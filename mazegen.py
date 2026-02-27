from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
import random


class MazeConfigError(ValueError):
    """Raised when the maze configuration is invalid or malformed."""


class MazeGenerationError(RuntimeError):
    """Raised when maze generation or solving fails."""


class Direction(IntEnum):
    """Cardinal directions used to navigate the maze grid."""

    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3


DIR_TO_BIT: dict[Direction, int] = {
    Direction.NORTH: 0,
    Direction.EAST: 1,
    Direction.SOUTH: 2,
    Direction.WEST: 3,
}

DIR_TO_DELTA: dict[Direction, tuple[int, int]] = {
    Direction.NORTH: (0, -1),
    Direction.EAST: (1, 0),
    Direction.SOUTH: (0, 1),
    Direction.WEST: (-1, 0),
}

OPPOSITE: dict[Direction, Direction] = {
    Direction.NORTH: Direction.SOUTH,
    Direction.EAST: Direction.WEST,
    Direction.SOUTH: Direction.NORTH,
    Direction.WEST: Direction.EAST,
}

DIR_TO_LETTER: dict[Direction, str] = {
    Direction.NORTH: "N",
    Direction.EAST: "E",
    Direction.SOUTH: "S",
    Direction.WEST: "W",
}


@dataclass(frozen=True, slots=True)
class Point:
    """2D coordinate on the maze grid (x, y)."""

    x: int
    y: int


@dataclass(slots=True)
class MazeConfig:
    """Configuration for maze generation and output."""

    width: int
    height: int
    entry: Point
    exit: Point
    output_file: Path
    perfect: bool
    seed: int | None = None

    @staticmethod
    def from_file(path: Path) -> "MazeConfig":
        """Load a MazeConfig from a KEY=VALUE config file."""
        text = path.read_text(encoding="utf-8")
        kv = _parse_kv_config(text)

        width = _parse_int_required(kv, "WIDTH")
        height = _parse_int_required(kv, "HEIGHT")
        entry = _parse_point_required(kv, "ENTRY")
        exit_ = _parse_point_required(kv, "EXIT")
        output_file = Path(_parse_str_required(kv, "OUTPUT_FILE"))
        perfect = _parse_bool_required(kv, "PERFECT")

        seed: int | None = None
        if "SEED" in kv:
            seed = _parse_int(kv["SEED"], "SEED")

        cfg = MazeConfig(
            width=width,
            height=height,
            entry=entry,
            exit=exit_,
            output_file=output_file,
            perfect=perfect,
            seed=seed,
        )
        _validate_config(cfg)
        return cfg


@dataclass(slots=True)
class Cell:
    """A single maze cell encoded as a 4-bit wall mask (WSEN)."""

    walls: int = 0b1111


@dataclass(slots=True)
class Maze:
    """Maze grid and metadata (dimensions, entry, exit)."""

    width: int
    height: int
    entry: Point
    exit: Point
    grid: list[list[Cell]]

    def in_bounds(self, p: Point) -> bool:
        """Return True if point p is inside the maze boundaries."""
        return 0 <= p.x < self.width and 0 <= p.y < self.height

    def cell(self, p: Point) -> Cell:
        """Return the Cell at position p (assumes p is in bounds)."""
        return self.grid[p.y][p.x]


class MazeGenerator:
    """Generate mazes and compute shortest paths based on MazeConfig."""

    def __init__(self, config: MazeConfig) -> None:
        """Create a generator with a reproducible RNG from config.seed."""
        self.cfg = config
        self.rng = random.Random(config.seed)
        self._maze: Maze | None = None

    def generate(self) -> Maze:
        """Generate and return a new maze instance."""
        maze = Maze(
            width=self.cfg.width,
            height=self.cfg.height,
            entry=self.cfg.entry,
            exit=self.cfg.exit,
            grid=[
                [Cell() for _ in range(self.cfg.width)]
                for __ in range(self.cfg.height)
            ],
        )

        self._ensure_outer_borders_closed(maze)
        self._maze = maze
        raise MazeGenerationError("generate() not implemented yet (algorithm missing)") # noqa

    def solve_shortest_path(self) -> str:
        """Solve and return a shortest path string (e.g. 'NNEESW')."""
        if self._maze is None:
            raise MazeGenerationError("solve_shortest_path() requires a generated maze") # noqa
        raise MazeGenerationError("solve_shortest_path() not implemented yet")

    def write_output_file(self, maze: Maze, path: str) -> None:
        """Write maze walls (hex), entry/exit, and the path to output_file."""
        lines: list[str] = []
        for y in range(maze.height):
            row_hex = "".join(
                _cell_to_hex(maze.grid[y][x]) for x in range(maze.width)
            )
            lines.append(row_hex)

        lines.append("")
        lines.append(f"{maze.entry.x},{maze.entry.y}")
        lines.append(f"{maze.exit.x},{maze.exit.y}")
        lines.append(path)

        content = "\n".join(lines) + "\n"
        self.cfg.output_file.write_text(content, encoding="utf-8")

    def render_ascii(self, maze: Maze, show_path: bool, path: str | None) -> str: # noqa
        """Render the maze as an ASCII string (stub placeholder)."""
        _ = (show_path, path)
        return f"Maze {maze.width}x{maze.height} entry={maze.entry} exit={maze.exit}" # noqa

    def _ensure_outer_borders_closed(self, maze: Maze) -> None:
        """Ensure boundary walls remain closed for all outer cells (stub)."""
        _ = maze
        return

    def _open_wall(self, maze: Maze, p: Point, d: Direction) -> None:
        """Open wall at cell p in direction d and open opposite wall in neighbor.""" # noqa
        dx, dy = DIR_TO_DELTA[d]
        np = Point(p.x + dx, p.y + dy)
        if not maze.in_bounds(np):
            return

        cell = maze.cell(p)
        neigh = maze.cell(np)

        cell.walls &= ~(1 << DIR_TO_BIT[d])
        neigh.walls &= ~(1 << DIR_TO_BIT[OPPOSITE[d]])


def _parse_kv_config(text: str) -> dict[str, str]:
    """Parse a KEY=VALUE config string into a dict (ignores blanks/comments).""" # noqa
    kv: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise MazeConfigError(f"Bad line (expected KEY=VALUE): {raw!r}")
        key, value = line.split("=", 1)
        key = key.strip().upper()
        value = value.strip()
        if not key:
            raise MazeConfigError(f"Empty key in line: {raw!r}")
        kv[key] = value
    return kv


def _parse_str_required(kv: dict[str, str], key: str) -> str:
    """Return required string value for key or raise MazeConfigError."""
    if key not in kv:
        raise MazeConfigError(f"Missing required key: {key}")
    if not kv[key]:
        raise MazeConfigError(f"Empty value for key: {key}")
    return kv[key]


def _parse_int_required(kv: dict[str, str], key: str) -> int:
    """Return required integer value for key or raise MazeConfigError."""
    return _parse_int(_parse_str_required(kv, key), key)


def _parse_int(value: str, key: str) -> int:
    """Parse an int or raise MazeConfigError with a clear message."""
    try:
        return int(value)
    except ValueError as exc:
        raise MazeConfigError(
            f"{key} must be an integer, got {value!r}"
        ) from exc


def _parse_bool_required(kv: dict[str, str], key: str) -> bool:
    """Return required boolean value for key (accepts common truthy/falsey tokens).""" # noqa
    raw = _parse_str_required(kv, key).lower()
    if raw in {"true", "1", "yes", "y"}:
        return True
    if raw in {"false", "0", "no", "n"}:
        return False
    raise MazeConfigError(f"{key} must be a boolean (True/False), got {raw!r}")


def _parse_point_required(kv: dict[str, str], key: str) -> Point:
    """Parse a required 'x,y' point into a Point instance."""
    raw = _parse_str_required(kv, key)
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) != 2:
        raise MazeConfigError(f"{key} must be 'x,y', got {raw!r}")
    x = _parse_int(parts[0], key)
    y = _parse_int(parts[1], key)
    return Point(x=x, y=y)


def _validate_config(cfg: MazeConfig) -> None:
    """Validate config semantic constraints (bounds, sizes, entry/exit)."""
    if cfg.width <= 0 or cfg.height <= 0:
        raise MazeConfigError("WIDTH and HEIGHT must be positive")
    if cfg.entry == cfg.exit:
        raise MazeConfigError("ENTRY and EXIT must be different")

    if not (0 <= cfg.entry.x < cfg.width and 0 <= cfg.entry.y < cfg.height):
        raise MazeConfigError("ENTRY out of bounds")
    if not (0 <= cfg.exit.x < cfg.width and 0 <= cfg.exit.y < cfg.height):
        raise MazeConfigError("EXIT out of bounds")


def _cell_to_hex(cell: Cell) -> str:
    """Convert a Cell's 4-bit wall mask into a single hex digit (0..F)."""
    v = cell.walls & 0xF
    return format(v, "X")
