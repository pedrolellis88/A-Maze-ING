from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import mazegen


@dataclass(frozen=True, slots=True)
class RenderOptions:
    show_path: bool = False
    path: Optional[str] = None
    mark_entry: str = "S"
    mark_exit: str = "E"
    mark_path: str = "."


def _has_wall(cell: mazegen.Cell, d: mazegen.Direction) -> bool:
    """Return True if the cell has a wall in direction d."""
    return bool(cell.walls & (1 << mazegen.DIR_TO_BIT[d]))


def _walk_path(entry: mazegen.Point, path: str) -> set[mazegen.Point]:
    """Return the set of points visited by the path string (includes entry)."""
    visited: set[mazegen.Point] = {entry}
    p = entry

    for ch in path:
        if ch == "N":
            d = mazegen.Direction.NORTH
        elif ch == "E":
            d = mazegen.Direction.EAST
        elif ch == "S":
            d = mazegen.Direction.SOUTH
        elif ch == "W":
            d = mazegen.Direction.WEST
        else:
            continue

        dx, dy = mazegen.DIR_TO_DELTA[d]
        p = mazegen.Point(p.x + dx, p.y + dy)
        visited.add(p)

    return visited


def render_ascii(maze: mazegen.Maze, opts: RenderOptions | None = None) -> str:
    """
    Render maze using +---+ / |   | grid.

    - Uses maze.grid[y][x].walls bitmask (WSEN mapped by DIR_TO_BIT).
    - Optionally overlays S/E and path markers inside cells.
    """
    if opts is None:
        opts = RenderOptions()

    path_points: set[mazegen.Point] = set()
    if opts.show_path and opts.path:
        path_points = _walk_path(maze.entry, opts.path)

    lines: list[str] = []

    for y in range(maze.height):
        # Top border of row y (NORTH walls)
        top = ["+"]
        for x in range(maze.width):
            cell = maze.grid[y][x]
            top.append("---+" if _has_wall(cell, mazegen.Direction.NORTH) else "   +") # noqa
        lines.append("".join(top))

        # Middle/content line (WEST/EAST walls + markers)
        mid: list[str] = []
        for x in range(maze.width):
            cell = maze.grid[y][x]

            if x == 0:
                mid.append("|" if _has_wall(cell, mazegen.Direction.WEST) else " ") # noqa

            p = mazegen.Point(x, y)
            if p == maze.entry:
                content = f" {opts.mark_entry} "
            elif p == maze.exit:
                content = f" {opts.mark_exit} "
            elif p in path_points:
                content = f" {opts.mark_path} "
            else:
                content = "   "
            mid.append(content)

            mid.append("|" if _has_wall(cell, mazegen.Direction.EAST) else " ")

        lines.append("".join(mid))

    # Bottom border (SOUTH walls of last row)
    bottom = ["+"]
    last_y = maze.height - 1
    for x in range(maze.width):
        cell = maze.grid[last_y][x]
        bottom.append("---+" if _has_wall(cell, mazegen.Direction.SOUTH) else "   +") # noqa
    lines.append("".join(bottom))

    return "\n".join(lines) + "\n"
