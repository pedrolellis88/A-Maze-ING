from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import Iterable
import random
from collections import deque


class MazeConfigError(ValueError):
    pass


class MazeGenerationError(RuntimeError):
    pass


class Direction(IntEnum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3


# Bits no output (subject):
# bit 0 North, bit 1 East, bit 2 South, bit 3 West :contentReference[oaicite:4]{index=4}
DIR_TO_BIT = {
    Direction.NORTH: 0,
    Direction.EAST: 1,
    Direction.SOUTH: 2,
    Direction.WEST: 3,
}

DIR_TO_DELTA = {
    Direction.NORTH: (0, -1),
    Direction.EAST: (1, 0),
    Direction.SOUTH: (0, 1),
    Direction.WEST: (-1, 0),
}

OPPOSITE = {
    Direction.NORTH: Direction.SOUTH,
    Direction.EAST: Direction.WEST,
    Direction.SOUTH: Direction.NORTH,
    Direction.WEST: Direction.EAST,
}

DIR_TO_LETTER = {
    Direction.NORTH: "N",
    Direction.EAST: "E",
    Direction.SOUTH: "S",
    Direction.WEST: "W",
}


@dataclass(frozen=True)
class Point:
    x: int
    y: int


@dataclass
class MazeConfig:
    width: int
    height: int
    entry: Point
    exit: Point
    output_file: Path
    perfect: bool
    seed: int | None = None

    @staticmethod
    def from_file(path: Path) -> "MazeConfig":
        text = path.read_text(encoding="utf-8")
        kv = _parse_kv_config(text)

        width = _parse_int_required(kv, "WIDTH")
        height = _parse_int_required(kv, "HEIGHT")
        entry = _parse_point_required(kv, "ENTRY")
        exit_ = _parse_point_required(kv, "EXIT")
        output_file = Path(_parse_str_required(kv, "OUTPUT_FILE"))
        perfect = _parse_bool_required(kv, "PERFECT")

        seed = None
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


@dataclass
class Cell:
    # walls bits: 1 means CLOSED, 0 means OPEN
    walls: int = 0b1111  # começa tudo fechado por padrão


@dataclass
class Maze:
    width: int
    height: int
    entry: Point
    exit: Point
    grid: list[list[Cell]]

    def in_bounds(self, p: Point) -> bool:
        return 0 <= p.x < self.width and 0 <= p.y < self.height

    def cell(self, p: Point) -> Cell:
        return self.grid[p.y][p.x]


class MazeGenerator:
    def __init__(self, config: MazeConfig) -> None:
        self.cfg = config
        self.rng = random.Random(config.seed)

    def generate(self) -> Maze:
        # Placeholder: estrutura inicial coerente (bordas fechadas).
        # Depois você troca por algoritmo (recursive backtracker / prim / kruskal etc.)
        maze = Maze(
            width=self.cfg.width,
            height=self.cfg.height,
            entry=self.cfg.entry,
            exit=self.cfg.exit,
            grid=[[Cell() for _ in range(self.cfg.width)] for __ in range(self.cfg.height)],
        )

        self._ensure_outer_borders_closed(maze)

        # Aqui entra:
        # - algoritmo de carving garantindo conectividade
        # - se perfect=True: gerar spanning tree (um único caminho entre entry e exit) :contentReference[oaicite:5]{index=5}
        # - aplicar padrão "42" com células totalmente fechadas quando couber :contentReference[oaicite:6]{index=6}
        #
        # Por enquanto, falha clara para não “passar falso positivo”.
        raise MazeGenerationError("generate() not implemented yet (algorithm missing)")

    def solve_shortest_path(self) -> str:
        # Depende de generate() ter sido feito e armazenado.
        raise MazeGenerationError("solve_shortest_path() requires a generated maze")

    # --------- IO do formato do subject ---------

    def write_output_file(self, maze: Maze, path: str) -> None:
        lines: list[str] = []
        for y in range(maze.height):
            row_hex = "".join(_cell_to_hex(maze.grid[y][x]) for x in range(maze.width))
            lines.append(row_hex)
        lines.append("")  # empty line
        lines.append(f"{maze.entry.x},{maze.entry.y}")
        lines.append(f"{maze.exit.x},{maze.exit.y}")
        lines.append(path)

        content = "\n".join(lines) + "\n"
        self.cfg.output_file.write_text(content, encoding="utf-8")

    # --------- Render (placeholder) ---------

    def render_ascii(self, maze: Maze, show_path: bool, path: str | None) -> str:
        # Placeholder minimalista: depois você faz o renderer de verdade
        return f"Maze {maze.width}x{maze.height} entry={maze.entry} exit={maze.exit}"

    # --------- Helpers internos ---------

    def _ensure_outer_borders_closed(self, maze: Maze) -> None:
        # Por padrão já iniciamos walls=1111, então bordas já fechadas.
        # Se você começar com paredes abertas, use isso aqui.
        pass

    def _open_wall(self, maze: Maze, p: Point, d: Direction) -> None:
        """
        Abre parede em (p) na direção d e abre a parede oposta no vizinho.
        Isso garante coerência entre células adjacentes. :contentReference[oaicite:7]{index=7}
        """
        nx, ny = p.x + DIR_TO_DELTA[d][0], p.y + DIR_TO_DELTA[d][1]
        np = Point(nx, ny)
        if not maze.in_bounds(np):
            return

        cell = maze.cell(p)
        neigh = maze.cell(np)

        cell.walls &= ~(1 << DIR_TO_BIT[d])
        neigh.walls &= ~(1 << DIR_TO_BIT[OPPOSITE[d]])


# ---------------- Parsing helpers ----------------

def _parse_kv_config(text: str) -> dict[str, str]:
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
    if key not in kv:
        raise MazeConfigError(f"Missing required key: {key}")
    if not kv[key]:
        raise MazeConfigError(f"Empty value for key: {key}")
    return kv[key]


def _parse_int_required(kv: dict[str, str], key: str) -> int:
    return _parse_int(_parse_str_required(kv, key), key)


def _parse_int(value: str, key: str) -> int:
    try:
        return int(value)
    except ValueError as e:
        raise MazeConfigError(f"{key} must be an integer, got {value!r}") from e


def _parse_bool_required(kv: dict[str, str], key: str) -> bool:
    raw = _parse_str_required(kv, key).lower()
    if raw in {"true", "1", "yes", "y"}:
        return True
    if raw in {"false", "0", "no", "n"}:
        return False
    raise MazeConfigError(f"{key} must be a boolean (True/False), got {raw!r}")


def _parse_point_required(kv: dict[str, str], key: str) -> Point:
    raw = _parse_str_required(kv, key)
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) != 2:
        raise MazeConfigError(f"{key} must be 'x,y', got {raw!r}")
    x = _parse_int(parts[0], key)
    y = _parse_int(parts[1], key)
    return Point(x=x, y=y)


def _validate_config(cfg: MazeConfig) -> None:
    if cfg.width <= 0 or cfg.height <= 0:
        raise MazeConfigError("WIDTH and HEIGHT must be positive")
    if cfg.entry == cfg.exit:
        raise MazeConfigError("ENTRY and EXIT must be different")

    if not (0 <= cfg.entry.x < cfg.width and 0 <= cfg.entry.y < cfg.height):
        raise MazeConfigError("ENTRY out of bounds")
    if not (0 <= cfg.exit.x < cfg.width and 0 <= cfg.exit.y < cfg.height):
        raise MazeConfigError("EXIT out of bounds")


# ---------------- Hex encoding ----------------

def _cell_to_hex(cell: Cell) -> str:
    # walls bits are in 0..3, convert to 0..15 and then to hex digit
    v = cell.walls & 0xF
    return format(v, "X")
