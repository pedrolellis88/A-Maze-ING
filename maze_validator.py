from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional
from collections import deque
from mazegen import (
    DIR_TO_BIT,
    DIR_TO_DELTA,
    OPPOSITE,
    Direction,
    Maze,
    Point,
)


class MazeValidationError(ValueError):
    """Raised when a maze or its output file violates the subject constraints.""" # noqa


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Result of a validation run."""

    ok: bool
    errors: tuple[str, ...]


def _has_wall(cell_walls: int, d: Direction) -> bool:
    """Return True if the cell has a wall in direction d."""
    return bool(cell_walls & (1 << DIR_TO_BIT[d]))


def _open_between(maze: Maze, a: Point, d: Direction) -> bool:
    """Return True if there is a passage from a to its neighbor in direction d.""" # noqa
    dx, dy = DIR_TO_DELTA[d]
    b = Point(a.x + dx, a.y + dy)
    if not maze.in_bounds(b):
        return False
    aw = maze.cell(a).walls
    bw = maze.cell(b).walls
    return (not _has_wall(aw, d)) and (not _has_wall(bw, OPPOSITE[d]))


def _iter_points(width: int, height: int) -> Iterable[Point]:
    """Yield all grid points from (0,0) to (width-1,height-1)."""
    for y in range(height):
        for x in range(width):
            yield Point(x, y)


def _neighbors(maze: Maze, p: Point) -> Iterable[tuple[Direction, Point]]:
    """Yield (direction, neighbor_point) for all in-bounds neighbors of p."""
    for d, (dx, dy) in DIR_TO_DELTA.items():
        np = Point(p.x + dx, p.y + dy)
        if maze.in_bounds(np):
            yield d, np


def _is_fully_closed(cell_walls: int) -> bool:
    """Return True if all four walls are present."""
    return (cell_walls & 0b1111) == 0b1111


def _bfs_distances(
    maze: Maze,
    start: Point,
    blocked: set[Point],
) -> dict[Point, int]:
    """Compute BFS distances from start, avoiding blocked cells."""
    if start in blocked:
        return {}
    if not maze.in_bounds(start):
        return {}

    q: deque[Point] = deque([start])
    dist: dict[Point, int] = {start: 0}

    while q:
        cur = q.popleft()
        for d, nxt in _neighbors(maze, cur):
            if nxt in blocked:
                continue
            if nxt in dist:
                continue
            if _open_between(maze, cur, d):
                dist[nxt] = dist[cur] + 1
                q.append(nxt)

    return dist


def _count_edges_undirected(maze: Maze, blocked: set[Point]) -> int:
    """Count open passages as undirected edges (only EAST and SOUTH)."""
    edges = 0
    for p in _iter_points(maze.width, maze.height):
        if p in blocked:
            continue
        for d in (Direction.EAST, Direction.SOUTH):
            dx, dy = DIR_TO_DELTA[d]
            np = Point(p.x + dx, p.y + dy)
            if not maze.in_bounds(np) or np in blocked:
                continue
            if _open_between(maze, p, d):
                edges += 1
    return edges


def _parse_hex_grid_and_tail(content: str) -> tuple[list[str], str, str, str]:
    """Return (grid_lines, entry_line, exit_line, path_line) from output text.
    Look page 10/18 of the subject
    """
    lines = content.splitlines()
    sep: int | None = None
    for i, line in enumerate(lines):
        if line.strip() == "":
            sep = i
            break
    if sep is None:
        msg = "Output file: missing empty line separator before tail"
        raise MazeValidationError(msg)

    grid_lines = lines[:sep]
    tail = lines[sep + 1:]

    if len(tail) < 3:
        msg = "Output file: tail must have 3 lines (entry, exit, path)"
        raise MazeValidationError(msg)

    entry_line, exit_line, path_line = tail[0], tail[1], tail[2]
    return grid_lines, entry_line, exit_line, path_line


def _parse_point_line(s: str, label: str) -> Point:
    """Parse a 'x,y' line into a Point."""
    try:
        xs, ys = s.split(",", 1)
        x = int(xs.strip())
        y = int(ys.strip())
        return Point(x, y)
    except Exception as exc:
        msg = f"Output file: invalid {label} line {s!r}: {exc}"
        raise MazeValidationError(msg) from exc  # noqa


def _path_to_dirs(path: str) -> list[Direction]:
    """Convert a path string (N/E/S/W) into a list of Direction."""
    mapping = {
        "N": Direction.NORTH,
        "E": Direction.EAST,
        "S": Direction.SOUTH,
        "W": Direction.WEST,
    }
    out: list[Direction] = []
    for ch in path.strip():
        if ch not in mapping:
            msg = f"Path contains invalid character {ch!r} (expected N/E/S/W)"
            raise MazeValidationError(msg)
        out.append(mapping[ch])
    return out


class MazeValidator:
    """Validate maze invariants and output-file constraints."""

    def validate_maze(
        self,
        maze: Maze,
        *,
        perfect: bool,
        expected_closed: Optional[set[Point]] = None,
    ) -> ValidationResult:
        """Validate maze structure: borders, coherence, connectivity, and rules.""" # noqa
        errors: list[str] = []

        if maze.width <= 0 or maze.height <= 0:
            errors.append("Maze: width/height must be positive")
            return ValidationResult(False, tuple(errors))

        if not maze.in_bounds(maze.entry):
            errors.append(f"Maze: entry out of bounds: {maze.entry}")
        if not maze.in_bounds(maze.exit):
            errors.append(f"Maze: exit out of bounds: {maze.exit}")
        if maze.entry == maze.exit:
            errors.append("Maze: entry and exit must be different")

        for x in range(maze.width):
            top = Point(x, 0)
            bot = Point(x, maze.height - 1)
            if not _has_wall(maze.cell(top).walls, Direction.NORTH):
                errors.append(f"Borders: missing NORTH wall at {top}")
            if not _has_wall(maze.cell(bot).walls, Direction.SOUTH):
                errors.append(f"Borders: missing SOUTH wall at {bot}")

        for y in range(maze.height):
            left = Point(0, y)
            right = Point(maze.width - 1, y)
            if not _has_wall(maze.cell(left).walls, Direction.WEST):
                errors.append(f"Borders: missing WEST wall at {left}")
            if not _has_wall(maze.cell(right).walls, Direction.EAST):
                errors.append(f"Borders: missing EAST wall at {right}")

        for p in _iter_points(maze.width, maze.height):
            for d, np in _neighbors(maze, p):
                aw = maze.cell(p).walls
                bw = maze.cell(np).walls
                a_has = _has_wall(aw, d)
                b_has = _has_wall(bw, OPPOSITE[d])
                if a_has != b_has:
                    msg = (
                        f"Coherence: mismatch {p} {d.name} vs "
                        f"{np} {OPPOSITE[d].name}"
                    )
                    errors.append(msg)  # noqa

        blocked: set[Point] = set()
        if expected_closed is not None:
            blocked = set(expected_closed)
            for p in blocked:
                if not maze.in_bounds(p):
                    errors.append(f"42: expected_closed contains out-of-bounds {p}") # noqa
                    continue
                if not _is_fully_closed(maze.cell(p).walls):
                    msg = (
                        f"42: cell {p} expected fully closed (0b1111), got "
                        f"{maze.cell(p).walls:04b}"
                    )
                    errors.append(msg)  # noqa

        if expected_closed is not None:
            for p in _iter_points(maze.width, maze.height):
                if p in blocked:
                    continue
                if _is_fully_closed(maze.cell(p).walls):
                    msg = f"42: found fully-closed cell outside expected pattern at {p}" # noqa
                    errors.append(msg)  # noqa

        if maze.entry in blocked:
            errors.append("42: entry is inside the closed pattern cells")
        if maze.exit in blocked:
            errors.append("42: exit is inside the closed pattern cells")

        dist = _bfs_distances(maze, maze.entry, blocked)
        total_open_cells = sum(
            1 for p in _iter_points(maze.width, maze.height) if p not in blocked # noqa
        )

        if len(dist) != total_open_cells:
            msg = (
                f"Connectivity: reachable={len(dist)} but expected={total_open_cells} " # noqa
                "(some cells isolated)"
            )
            errors.append(msg)  # noqa

        for y0 in range(maze.height - 2):
            for x0 in range(maze.width - 2):
                pts = [
                    Point(x0 + dx, y0 + dy)
                    for dy in range(3)
                    for dx in range(3)
                ]
                if expected_closed is not None and any(p in blocked for p in pts): # noqa
                    continue

                all_open = True
                for dy in range(3):
                    for dx in range(2):
                        a = Point(x0 + dx, y0 + dy)
                        if not _open_between(maze, a, Direction.EAST):
                            all_open = False
                            break
                    if not all_open:
                        break

                if all_open:
                    for dy in range(2):
                        for dx in range(3):
                            a = Point(x0 + dx, y0 + dy)
                            if not _open_between(maze, a, Direction.SOUTH):
                                all_open = False
                                break
                        if not all_open:
                            break

                if all_open:
                    msg = (
                        "OpenArea: found forbidden 3x3 open area at top-left "
                        f"({x0},{y0})"
                    )
                    errors.append(msg)  # noqa

        if perfect:
            if len(dist) == 0:
                errors.append("Perfect: entry unreachable (dist empty)")
            else:
                edges = _count_edges_undirected(maze, blocked)
                nodes = total_open_cells
                if edges != nodes - 1:
                    msg = (
                        "Perfect: expected edges=nodes-1 => "
                        f"{nodes - 1}, got {edges} (cycle or disconnect)"
                    )
                    errors.append(msg)  # noqa

        return ValidationResult(ok=(len(errors) == 0), errors=tuple(errors))

    def validate_path_is_shortest(
        self,
        maze: Maze,
        path: str,
        *,
        expected_closed: Optional[set[Point]] = None,
    ) -> ValidationResult:
        """Validate that path is legal, ends at exit, and is shortest by BFS.""" # noqa
        errors: list[str] = []
        blocked = set(expected_closed) if expected_closed else set()

        cur = maze.entry
        steps = _path_to_dirs(path)
        for i, d in enumerate(steps):
            if cur in blocked:
                msg = f"Path: stepped into blocked cell at step {i}: {cur}"
                errors.append(msg)
                break
            if not _open_between(maze, cur, d):
                msg = (
                    f"Path: invalid move at step {i}: from {cur} "
                    f"to {d.name} (wall closed)"
                )
                errors.append(msg)  # noqa
                break
            dx, dy = DIR_TO_DELTA[d]
            cur = Point(cur.x + dx, cur.y + dy)

        if not errors and cur != maze.exit:
            msg = (
                f"Path: does not end at exit. Ended at {cur}, expected {maze.exit}" # noqa
            )
            errors.append(msg)  # noqa

        if not errors:
            dist = _bfs_distances(maze, maze.entry, blocked)
            if maze.exit not in dist:
                errors.append("Path: exit not reachable according to BFS")
            else:
                shortest_len = dist[maze.exit]
                if len(steps) != shortest_len:
                    msg = (
                        f"Path: not shortest. len(path)={len(steps)} "
                        f"shortest={shortest_len}"
                    )
                    errors.append(msg)  # noqa

        return ValidationResult(ok=(len(errors) == 0), errors=tuple(errors))

    def validate_output_file(
        self,
        output_path: Path,
        *,
        width: int,
        height: int,
    ) -> tuple[Maze, str]:
        """Validate output file and decode it into (Maze, path_string)."""
        content = output_path.read_text(encoding="utf-8")
        grid_lines, entry_line, exit_line, path_line = _parse_hex_grid_and_tail( # noqa
            content
        )

        if len(grid_lines) != height:
            msg = f"Output file: expected {height} grid rows, got {len(grid_lines)}" # noqa
            raise MazeValidationError(msg)

        for i, row in enumerate(grid_lines):
            row_stripped = row.strip()
            if len(row_stripped) != width:
                msg = (
                    f"Output file: row {i} expected length {width}, got "
                    f"{len(row_stripped)}"
                )
                raise MazeValidationError(msg)  # noqa
            for ch in row_stripped:
                if ch not in "0123456789abcdefABCDEF":
                    msg = f"Output file: invalid hex char {ch!r} in row {i}"
                    raise MazeValidationError(msg)

        entry = _parse_point_line(entry_line, "entry")
        exit_ = _parse_point_line(exit_line, "exit")

        from mazegen import Cell

        grid: list[list[Cell]] = []
        for y in range(height):
            row = grid_lines[y].strip()
            cells: list[Cell] = []
            for x in range(width):
                walls = int(row[x], 16) & 0b1111
                cells.append(Cell(walls=walls))
            grid.append(cells)

        maze = Maze(width=width, height=height, entry=entry, exit=exit_, grid=grid) # noqa
        return maze, path_line.strip()
