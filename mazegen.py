from __future__ import annotations

from collections import deque
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

LETTER_TO_DIR: dict[str, Direction] = {
    "N": Direction.NORTH,
    "E": Direction.EAST,
    "S": Direction.SOUTH,
    "W": Direction.WEST,
}


@dataclass(frozen=True, slots=True)
class Point:
    """2D coordinate on the maze grid (x, y)."""

    x: int
    y: int


@dataclass(slots=True)
class MazeConfig:
    """
    Configuration for maze generation and output.

    Required by subject:
      WIDTH, HEIGHT, ENTRY, EXIT, OUTPUT_FILE, PERFECT
    Optional:
      SEED (recommended for reproducibility), PATTERN_42 (default True)
    """

    width: int
    height: int
    entry: Point
    exit: Point
    output_file: Path
    perfect: bool
    seed: int
    pattern_42: bool = True
    colors: str | None = None

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

        seed = 0
        if "SEED" in kv:
            seed = _parse_int(kv["SEED"], "SEED")

        pattern_42 = True
        if "PATTERN_42" in kv:
            pattern_42 = _parse_bool_required(kv, "PATTERN_42")

        colors = None
        if "COLORS" in kv:
            colors = kv["COLORS"].strip()
            if not colors:
                raise MazeConfigError("COLORS cannot be empty (expected KEY:VALUE pairs).") # noqa    

        cfg = MazeConfig(
            width=width,
            height=height,
            entry=entry,
            exit=exit_,
            output_file=output_file,
            perfect=perfect,
            seed=seed,
            pattern_42=pattern_42,
            colors=colors,
        )
        _validate_config(cfg)
        return cfg


@dataclass(slots=True)
class Cell:
    """A single maze cell encoded as a 4-bit wall mask (N,E,S,W)."""

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


FULLY_CLOSED = 0b1111


def has_wall(cell: Cell, d: Direction) -> bool:
    """Return True if the cell has a wall in direction d."""
    return bool(cell.walls & (1 << DIR_TO_BIT[d]))


def _open_wall_between(maze: Maze, a: Point, d: Direction) -> None:
    """Open wall at cell a in direction d and open opposite wall in neighbor.""" # noqa
    dx, dy = DIR_TO_DELTA[d]
    b = Point(a.x + dx, a.y + dy)
    if not maze.in_bounds(b):
        return

    ca = maze.cell(a)
    cb = maze.cell(b)
    ca.walls &= ~(1 << DIR_TO_BIT[d])
    cb.walls &= ~(1 << DIR_TO_BIT[OPPOSITE[d]])


def _close_wall(cell: Cell, d: Direction) -> None:
    """Close (set) the wall bit for direction d."""
    cell.walls |= (1 << DIR_TO_BIT[d])


def _fully_close_cell_and_sync_neighbors(maze: Maze, p: Point) -> None:
    """
    Set this cell to fully closed and ensure neighbor walls match coherently.
    """
    maze.cell(p).walls = FULLY_CLOSED
    for d, (dx, dy) in DIR_TO_DELTA.items():
        np = Point(p.x + dx, p.y + dy)
        if not maze.in_bounds(np):
            continue
        _close_wall(maze.cell(np), OPPOSITE[d])


def _neighbors_in_bounds(maze: Maze, p: Point) -> list[tuple[Direction, Point]]: # noqa
    """Return list of (direction, neighbor_point) for in-bounds neighbors."""
    out: list[tuple[Direction, Point]] = []
    for d, (dx, dy) in DIR_TO_DELTA.items():
        np = Point(p.x + dx, p.y + dy)
        if maze.in_bounds(np):
            out.append((d, np))
    return out


def _cell_to_hex(cell: Cell) -> str:
    """Convert a Cell's 4-bit wall mask into a single hex digit (0..F)."""
    return format(cell.walls & 0xF, "X")


_42_BITMAP: list[str] = [
    "X...XXX",
    "X.....X",
    "XXX.XXX",
    "..X.X..",
    "..X.XXX",
]


def _compute_42_points(width: int, height: int) -> set[Point] | None:
    """
    Return the set of cells that must be fully closed to draw the "42" pattern.
    If the maze is too small, return None.
    """
    ph = len(_42_BITMAP)
    pw = len(_42_BITMAP[0])

    if width < pw or height < ph:
        return None

    x0 = (width - pw) // 2
    y0 = (height - ph) // 2

    pts: set[Point] = set()
    for dy, row in enumerate(_42_BITMAP):
        for dx, ch in enumerate(row):
            if ch == "X":
                pts.add(Point(x0 + dx, y0 + dy))
    return pts


def _is_unblocked_connected(
    width: int,
    height: int,
    entry: Point,
    blocked: set[Point],
) -> bool:
    """
    Check if all non-blocked cells are connected (4-neighborhood),
    starting from entry.
    """
    if entry in blocked:
        return False

    total_open = width * height - len(blocked)
    if total_open <= 0:
        return False

    q: deque[Point] = deque([entry])
    seen: set[Point] = {entry}

    while q:
        p = q.popleft()
        for d, (dx, dy) in DIR_TO_DELTA.items():
            _ = d
            np = Point(p.x + dx, p.y + dy)
            if not (0 <= np.x < width and 0 <= np.y < height):
                continue
            if np in blocked or np in seen:
                continue
            seen.add(np)
            q.append(np)

    return len(seen) == total_open


class MazeGenerator:
    """
    Generate mazes and compute shortest paths based on MazeConfig.

    - If PERFECT=True, generate a spanning tree over all non-blocked cells.
      This guarantees exactly one path between any two non-blocked cells,
      including ENTRY -> EXIT.
    - The "42" pattern is drawn with fully closed cells; it may be omitted if
      the size doesn't allow it (prints an error message).
    """

    def __init__(self, config: MazeConfig) -> None:
        self.cfg = config
        self.rng = random.Random(config.seed)
        self._maze: Maze | None = None
        self._blocked: set[Point] = set()

    @property
    def blocked_cells(self) -> set[Point]:
        """Cells used to draw the '42' pattern (fully closed)."""
        return set(self._blocked)

    def generate(self) -> Maze:
        """Generate and return a new maze instance."""
        maze = Maze(
            width=self.cfg.width,
            height=self.cfg.height,
            entry=self.cfg.entry,
            exit=self.cfg.exit,
            grid=[[Cell() for _ in range(self.cfg.width)] for __ in range(self.cfg.height)], # noqa
        )

        self._blocked = set()
        if self.cfg.pattern_42:
            blocked = _compute_42_points(maze.width, maze.height)
            if blocked is None:
                print("Error: maze too small to draw '42' pattern; omitting it.") # noqa
            elif maze.entry in blocked or maze.exit in blocked:
                print("Error: '42' pattern overlaps ENTRY/EXIT; omitting it.")
            elif not _is_unblocked_connected(
                maze.width, maze.height, maze.entry, blocked
            ):
                print("Error: '42' pattern would break connectivity; omitting it.") # noqa
            else:
                self._blocked = blocked
                for p in self._blocked:
                    _fully_close_cell_and_sync_neighbors(maze, p)

        self._carve_perfect_backtracker(maze)
        if not self.cfg.perfect:
            self._add_loops(maze, probability=0.1)

        self._maze = maze
        return maze

    def solve_shortest_path(self) -> str:
        """
        Return a shortest valid path string from ENTRY to EXIT using N/E/S/W.

        Requires generate() to be called first.
        """
        if self._maze is None:
            raise MazeGenerationError("solve_shortest_path() requires a generated maze") # noqa
        return self._bfs_shortest_path(self._maze)

    def write_output_file(self, maze: Maze, path: str) -> None:
        """
        Write maze to OUTPUT_FILE:
        - hex rows (one digit per cell)
        - blank line
        - entry "x,y"
        - exit "x,y"
        - shortest path string
        """
        lines: list[str] = []
        for y in range(maze.height):
            lines.append("".join(_cell_to_hex(maze.grid[y][x]) for x in range(maze.width))) # noqa

        lines.append("")
        lines.append(f"{maze.entry.x},{maze.entry.y}")
        lines.append(f"{maze.exit.x},{maze.exit.y}")
        lines.append(path)

        self.cfg.output_file.write_text("\n".join(lines) + "\n", encoding="utf-8") # noqa

    def _carve_perfect_backtracker(self, maze: Maze) -> None:
        """
        Generate a spanning tree over the grid excluding blocked cells
        using iterative DFS (recursive backtracker).
        """
        if maze.entry in self._blocked or maze.exit in self._blocked:
            raise MazeGenerationError("ENTRY/EXIT cannot be blocked")

        visited = [[False for _ in range(maze.width)] for __ in range(maze.height)] # noqa

        start = maze.entry
        visited[start.y][start.x] = True
        stack: list[Point] = [start]

        while stack:
            cur = stack[-1]

            candidates: list[tuple[Direction, Point]] = []
            for d, np in _neighbors_in_bounds(maze, cur):
                if np in self._blocked:
                    continue
                if visited[np.y][np.x]:
                    continue
                candidates.append((d, np))

            if not candidates:
                stack.pop()
                continue

            d, nxt = self.rng.choice(candidates)
            _open_wall_between(maze, cur, d)
            visited[nxt.y][nxt.x] = True
            stack.append(nxt)

        # Validate that every non-blocked cell was reached (full connectivity)
        total_open = maze.width * maze.height - len(self._blocked)
        reached = sum(
            1
            for y in range(maze.height)
            for x in range(maze.width)
            if Point(x, y) not in self._blocked and visited[y][x]
        )
        if reached != total_open:
            raise MazeGenerationError(
                "Generation failed: not all non-blocked cells are connected"
            )

    def _add_loops(self, maze: Maze, probability: float = 0.1) -> None:
        for y in range(maze.height):
            for x in range(maze.width):

                cur = Point(x, y)
                if cur in self._blocked:
                    continue

                for d, np in _neighbors_in_bounds(maze, cur):

                    if np in self._blocked:
                        continue

                    if has_wall(maze.cell(cur), d):

                        if self.rng.random() < probability:
                            _open_wall_between(maze, cur, d)

    def _open_between(self, maze: Maze, a: Point, d: Direction) -> bool:
        """Return True if there is a passage from a to its neighbor in direction d.""" # noqa
        dx, dy = DIR_TO_DELTA[d]
        b = Point(a.x + dx, a.y + dy)
        if not maze.in_bounds(b):
            return False
        if a in self._blocked or b in self._blocked:
            return False
        ca = maze.cell(a)
        cb = maze.cell(b)
        # passage means no wall on that side (and coherent on the other)
        return (not has_wall(ca, d)) and (not has_wall(cb, OPPOSITE[d]))

    def _bfs_shortest_path(self, maze: Maze) -> str:
        """Compute shortest path from entry to exit using BFS."""
        start = maze.entry
        goal = maze.exit

        if start in self._blocked or goal in self._blocked:
            raise MazeGenerationError("ENTRY/EXIT cannot be blocked")

        q: deque[Point] = deque([start])
        prev: dict[Point, tuple[Point, Direction]] = {}
        seen: set[Point] = {start}

        while q:
            cur = q.popleft()
            if cur == goal:
                break

            for d, _np in _neighbors_in_bounds(maze, cur):
                if not self._open_between(maze, cur, d):
                    continue
                dx, dy = DIR_TO_DELTA[d]
                np = Point(cur.x + dx, cur.y + dy)
                if np in seen:
                    continue
                seen.add(np)
                prev[np] = (cur, d)
                q.append(np)

        if goal not in seen:
            raise MazeGenerationError("No path found from ENTRY to EXIT")

        # Reconstruct as letters from goal -> start
        letters: list[str] = []
        cur = goal
        while cur != start:
            pprev, d = prev[cur]
            letters.append(DIR_TO_LETTER[d])
            cur = pprev
        letters.reverse()
        return "".join(letters)


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
        raise MazeConfigError(f"{key} must be an integer, got {value!r}") from exc # noqa


def _parse_bool_required(kv: dict[str, str], key: str) -> bool:
    """Return required boolean value for key."""
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
    """Validate semantic constraints."""
    if cfg.width <= 0 or cfg.height <= 0:
        raise MazeConfigError("WIDTH and HEIGHT must be positive")
    if cfg.entry == cfg.exit:
        raise MazeConfigError("ENTRY and EXIT must be different")

    if not (0 <= cfg.entry.x < cfg.width and 0 <= cfg.entry.y < cfg.height):
        raise MazeConfigError("ENTRY out of bounds")
    if not (0 <= cfg.exit.x < cfg.width and 0 <= cfg.exit.y < cfg.height):
        raise MazeConfigError("EXIT out of bounds")
