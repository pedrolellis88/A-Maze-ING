from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .render.palette import palette_from_spec

import mazegen

from .model import AppConfig, RenderMode
from .render.ascii_renderer import RenderOptions, render_ascii


@dataclass(frozen=True, slots=True)
class RunResult:
    """
    Represents the result of a full maze execution run.
    """

    maze: mazegen.Maze
    path: str
    output_file: Path
    rendered: Optional[str]


def run(app_cfg: AppConfig) -> RunResult:
    """
    Executes the full maze pipeline:
    configuration loading, generation, solving, file output,
    and optional ASCII rendering.
    """

    # Load maze configuration
    cfg = mazegen.MazeConfig.from_file(app_cfg.config_path)

    # Generate maze
    generator = mazegen.MazeGenerator(cfg)
    maze = generator.generate()

    # Solve shortest path
    path = generator.solve_shortest_path()

    # Write output file
    generator.write_output_file(maze, path)

    rendered: Optional[str] = None

    # Optional ASCII rendering
    if app_cfg.render_mode == RenderMode.ASCII:
        palette = palette_from_spec(cfg.colors)

        rendered = render_ascii(
            maze,
            RenderOptions(
                show_path=app_cfg.show_path,
                path=path,
                palette=palette,
            ),
        )

        if app_cfg.print_to_stdout:
            print(rendered)

    return RunResult(
        maze=maze,
        path=path,
        output_file=cfg.output_file,
        rendered=rendered,
    )
