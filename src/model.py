from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class RenderMode(str, Enum):
    ASCII = "ascii"
    NONE = "none"


@dataclass(frozen=True, slots=True)
class AppConfig:
    """
    App-level configuration (CLI/runtime).

    Note: MazeConfig parsing + validation lives in mazegen.MazeConfig.
    """
    config_path: Path = Path("config_default.txt")

    render_mode: RenderMode = RenderMode.ASCII
    show_path: bool = False

    print_to_stdout: bool = True
