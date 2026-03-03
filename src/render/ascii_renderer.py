from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import mazegen

from .palette import Palette

WALL_MARK = "W"
PATTERN42_MARK = "F"
PATH_MARK = "P"
ENTRY_MARK = "A"
EXIT_MARK = "Z"

OUT_CHAR = "▒"


@dataclass(frozen=True, slots=True)
class RenderOptions:
    """Options that control ASCII rendering (path + palette)."""

    show_path: bool = False
    path: Optional[str] = None
    palette: Palette = field(default_factory=Palette)


def _has_wall(cell: mazegen.Cell, d: mazegen.Direction) -> bool:
    """Return True if `cell` has a wall in direction `d`."""
    return bool(cell.walls & (1 << mazegen.DIR_TO_BIT[d]))


def _cell_center_coords(
    x: int,
    y: int,
    cell_size: int,
    wall_thickness: int,
) -> tuple[int, int]:
    """Return (cx, cy) canvas coords for the center of cell (x, y)."""
    base_x = x * (cell_size + wall_thickness) + wall_thickness
    base_y = y * (cell_size + wall_thickness) + wall_thickness
    cx = base_x + cell_size // 2
    cy = base_y + cell_size // 2
    return cx, cy


def _draw_axis_aligned_segment(
    canvas: list[list[str]],
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    mark: str,
) -> None:
    """Draw an orthogonal segment on `canvas` from (x0,y0) to (x1,y1)."""
    if x0 == x1:
        step = 1 if y1 >= y0 else -1
        for y in range(y0, y1 + step, step):
            canvas[y][x0] = mark
        return

    if y0 == y1:
        step = 1 if x1 >= x0 else -1
        for x in range(x0, x1 + step, step):
            canvas[y0][x] = mark
        return

    # Fallback: mark endpoints only (shouldn't happen).
    canvas[y0][x0] = mark
    canvas[y1][x1] = mark


def _overlay_path_as_single_line(
    canvas: list[list[str]],
    maze: mazegen.Maze,
    path: str,
    cell_size: int,
    wall_thickness: int,
    mark: str = PATH_MARK,
) -> None:
    """Overlay a continuous line following `path` from entry to exit."""
    p = maze.entry
    cx0, cy0 = _cell_center_coords(p.x, p.y, cell_size, wall_thickness)
    canvas[cy0][cx0] = mark

    for step_ch in path:
        if step_ch == "N":
            d = mazegen.Direction.NORTH
        elif step_ch == "S":
            d = mazegen.Direction.SOUTH
        elif step_ch == "E":
            d = mazegen.Direction.EAST
        elif step_ch == "W":
            d = mazegen.Direction.WEST
        else:
            continue

        dx, dy = mazegen.DIR_TO_DELTA[d]
        nxt = mazegen.Point(p.x + dx, p.y + dy)
        if not maze.in_bounds(nxt):
            continue

        cx1, cy1 = _cell_center_coords(nxt.x, nxt.y, cell_size, wall_thickness)
        _draw_axis_aligned_segment(canvas, cx0, cy0, cx1, cy1, mark)

        p = nxt
        cx0, cy0 = cx1, cy1


def render_ascii(maze: mazegen.Maze, opts: RenderOptions | None = None) -> str:
    """Render `maze` to colored ASCII using `opts` (optionally with path)."""
    if opts is None:
        opts = RenderOptions()

    palette = opts.palette

    cell_size = 3
    wall_thickness = 1

    width = maze.width
    height = maze.height

    canvas_w = width * cell_size + (width + 1) * wall_thickness
    canvas_h = height * cell_size + (height + 1) * wall_thickness

    # Start filled with "walls" (internal mark).
    canvas = [[WALL_MARK for _ in range(canvas_w)] for _ in range(canvas_h)]

    # 1) Draw maze interior + open passages.
    for y in range(height):
        for x in range(width):
            cell = maze.grid[y][x]

            base_x = x * (cell_size + wall_thickness) + wall_thickness
            base_y = y * (cell_size + wall_thickness) + wall_thickness

            is_42 = cell.walls == 0b1111

            # Fill cell interior with either pattern marker or space.
            fill_mark = PATTERN42_MARK if is_42 else " "
            for dy in range(cell_size):
                for dx in range(cell_size):
                    canvas[base_y + dy][base_x + dx] = fill_mark

            # Open walls where passages exist.
            if not _has_wall(cell, mazegen.Direction.NORTH):
                for dx in range(cell_size):
                    canvas[base_y - 1][base_x + dx] = " "

            if not _has_wall(cell, mazegen.Direction.SOUTH):
                for dx in range(cell_size):
                    canvas[base_y + cell_size][base_x + dx] = " "

            if not _has_wall(cell, mazegen.Direction.WEST):
                for dy in range(cell_size):
                    canvas[base_y + dy][base_x - 1] = " "

            if not _has_wall(cell, mazegen.Direction.EAST):
                for dy in range(cell_size):
                    canvas[base_y + dy][base_x + cell_size] = " "

    # 2) Overlay continuous path (internal mark).
    if opts.show_path and opts.path:
        _overlay_path_as_single_line(
            canvas=canvas,
            maze=maze,
            path=opts.path,
            cell_size=cell_size,
            wall_thickness=wall_thickness,
            mark=PATH_MARK,
        )

    # 3) Overlay entry/exit marks.
    entry_cx, entry_cy = _cell_center_coords(
        maze.entry.x, maze.entry.y, cell_size, wall_thickness
    )
    exit_cx, exit_cy = _cell_center_coords(
        maze.exit.x, maze.exit.y, cell_size, wall_thickness
    )
    canvas[entry_cy][entry_cx] = ENTRY_MARK
    canvas[exit_cy][exit_cx] = EXIT_MARK

    # 4) Colorize: print OUT_CHAR for marks, preserving spaces.
    lines: list[str] = []
    for row in canvas:
        line = ""
        for mark in row:
            if mark == WALL_MARK:
                line += palette.apply(OUT_CHAR, palette.wall)
            elif mark == PATTERN42_MARK:
                line += palette.apply(OUT_CHAR, palette.pattern_42)
            elif mark == PATH_MARK:
                line += palette.apply(OUT_CHAR, palette.path)
            elif mark == ENTRY_MARK:
                line += palette.apply(OUT_CHAR, palette.entry)
            elif mark == EXIT_MARK:
                line += palette.apply(OUT_CHAR, palette.exit)
            else:
                line += mark
        lines.append(line)

    return "\n".join(lines) + "\n"
