from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Color(str, Enum):
    """ANSI color codes."""

    RESET = "\033[0m"

    # standard colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # bright colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
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


def palette_from_spec(spec: str | None) -> Palette:
    """
    Build a Palette from config specification.

    Examples:
        COLORS=TRUE
        COLORS=FALSE
        COLORS=WALL:WHITE,PATH:BLUE,ENTRY:GREEN,EXIT:RED
        COLORS=WALL:BRIGHT_WHITE,PATH:BRIGHT_BLUE

    Allowed keys:
        WALL
        PATH
        ENTRY
        EXIT
        PATTERN_42
    """

    palette = Palette()

    if spec is None:
        return palette

    raw = spec.strip()

    if not raw:
        return palette

    upper = raw.upper()

    # simple enable/disable
    if upper == "TRUE":
        palette.enabled = True
        return palette

    if upper == "FALSE":
        palette.enabled = False
        return palette

    key_map = {
        "WALL": "wall",
        "PATH": "path",
        "ENTRY": "entry",
        "EXIT": "exit",
        "PATTERN_42": "pattern_42",
    }

    chunks = [c.strip() for c in raw.split(",") if c.strip()]

    for chunk in chunks:
        if ":" not in chunk:
            raise ValueError(
                f"Invalid COLORS entry '{chunk}'. Expected KEY:COLOR."
            )

        key, value = chunk.split(":", 1)
        key = key.strip().upper()
        value = value.strip().upper()

        if key not in key_map:
            allowed = ", ".join(sorted(key_map))
            raise ValueError(
                f"Invalid COLORS key '{key}'. Allowed keys: {allowed}"
            )

        try:
            color = Color[value]
        except KeyError as exc:
            allowed_colors = ", ".join(c.name for c in Color)
            raise ValueError(
                f"Invalid color '{value}'. Allowed colors: {allowed_colors}"
            ) from exc

        setattr(palette, key_map[key], color)

    return palette
