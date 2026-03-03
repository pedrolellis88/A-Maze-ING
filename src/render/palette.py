"""
palette.py

ANSI color management for terminal rendering.
Provides theme-based color application for maze visualization.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Color(str, Enum):
    """ANSI color codes."""

    RESET = "\033[0m"

    WHITE = "\033[37m"

    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_WHITE = "\033[97m"


@dataclass(slots=True)
class Palette:
    """
    Represents a color theme for rendering the maze.
    """

    wall: Color = Color.BRIGHT_WHITE
    entry: Color = Color.BRIGHT_GREEN
    exit: Color = Color.BRIGHT_RED
    path: Color = Color.BRIGHT_BLUE
    pattern_42: Color = Color.WHITE
    enabled: bool = True

    def apply(self, text: str, color: Color) -> str:
        """
        Apply ANSI color to a text if enabled.

        Args:
            text: The text to colorize.
            color: The ANSI color to apply.

        Returns:
            Colored text if enabled, otherwise original text.
        """
        if not self.enabled:
            return text
        return f"{color.value}{text}{Color.RESET.value}"
