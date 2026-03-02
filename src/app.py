from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import mazegen

from .model import AppConfig, RenderMode
from .render.ascii_renderer import RenderOptions, render_ascii


@dataclass(frozen=True, slots=True)
class RunResult:
    maze: mazegen.Maze
    path: str
    output_file: Path
    rendered: Optional[str]


def run(app_cfg: AppConfig) -> RunResult:
    cfg = mazegen.MazeConfig.from_file(app_cfg.config_path)

    gen = mazegen.MazeGenerator(cfg)
    maze = gen.generate()

    path = gen.solve_shortest_path()

    gen.write_output_file(maze, path)

    rendered: Optional[str] = None
    if app_cfg.render_mode == RenderMode.ASCII:
        rendered = render_ascii(
            maze,
            RenderOptions(show_path=app_cfg.show_path, path=path),
        )
        if app_cfg.print_to_stdout:
            print(rendered)

    return RunResult(
        maze=maze,
        path=path,
        output_file=cfg.output_file,
        rendered=rendered,
    )
