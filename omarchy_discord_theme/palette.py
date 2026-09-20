"""Map a parsed Omarchy theme onto Midnight's CSS variables.

Midnight (https://github.com/refact0r/midnight-discord) declares its entire
color scheme as CSS custom properties under `:root`. This module produces those
variables from an arbitrary Omarchy theme so any theme — not just Catppuccin —
gets a coherent Midnight-style palette.

Each base color ramp (--blue-*, --green-*, ...) is generated as 5 lightness
steps from the theme's single base color, mirroring how Midnight builds its
hsl(h, s%, l%) ramps. Dark and light themes map the semantic variables
differently so the result is always readable.
"""

from __future__ import annotations

from typing import Dict

from .colorutils import (
    hex_to_hsl,
    hsl_to_hex,
    relative_luminance,
    with_alpha,
)


def _ramp(base: str, n: int = 5, start: float = 0.85, end: float = 0.20) -> list:
    """Return n lightness steps from start..end for a base color.

    step 1 is the lightest (start) and step n the darkest (end), matching
    Midnight's ramp direction (--x-1 light, --x-5 dark).
    """
    hsl = hex_to_hsl(base)
    if not hsl:
        base = "#5865f2"
        hsl = hex_to_hsl(base)  # type: ignore[assignment]
    h, s, _ = hsl
    if n == 1:
        return [hsl_to_hex(h, s, (start + end) / 2)]
    steps = []
    for i in range(n):
        t = i / (n - 1)
        l = start + (end - start) * t
        steps.append(hsl_to_hex(h, s, l))
    return steps


def _build_ramps(theme: Dict[str, str]) -> Dict[str, list]:
    return {
        "red": _ramp(theme["red"]),
        "green": _ramp(theme["green"]),
        "blue": _ramp(theme["accent"]),
        "yellow": _ramp(theme["yellow"]),
        "purple": _ramp(theme["magenta"]),
    }


def build_dark_palette(theme: Dict[str, str]) -> Dict[str, str]:
    """Build Midnight variables for a dark Omarchy theme."""
    bg = theme["background"]
    bg2 = theme["dark_background"]
    bg3 = theme["darker_background"]
    fg = theme["foreground"]
    fg_dark = theme["dark_foreground"]
    accent = theme["accent"]
    muted = theme["muted"]
    ramps = _build_ramps(theme)

    p: Dict[str, str] = {}

    # --- text ---
    p["--text-0"] = bg2                                # text on colored elements
    p["--text-1"] = theme["bright_foreground"]         # primary white-ish text
    p["--text-2"] = fg                                 # headings / important
    p["--text-3"] = fg                                 # normal text
    p["--text-4"] = fg_dark                            # icons / channels
    p["--text-5"] = muted                              # muted text

    # --- backgrounds ---
    p["--bg-1"] = bg3                                  # dark buttons when clicked
    p["--bg-2"] = bg2                                  # dark buttons
    p["--bg-3"] = bg3                                  # spacing / secondary
    p["--bg-4"] = bg                                   # main background
    p["--hover"] = with_alpha(fg, 0.06)
    p["--active"] = with_alpha(fg, 0.12)
    p["--active-2"] = with_alpha(fg, 0.16)
    p["--message-hover"] = with_alpha(fg, 0.04)

    # --- accents ---
    p["--accent-1"] = ramps["blue"][0]
    p["--accent-2"] = ramps["blue"][1]
    p["--accent-3"] = ramps["blue"][2]
    p["--accent-4"] = ramps["blue"][3]
    p["--accent-5"] = ramps["blue"][4]
    p["--accent-new"] = ramps["blue"][1]
    p["--mention"] = f"linear-gradient(to right, {with_alpha(accent, 0.10)} 40%, transparent)"
    p["--mention-hover"] = f"linear-gradient(to right, {with_alpha(accent, 0.05)} 40%, transparent)"
    p["--reply"] = f"linear-gradient(to right, {with_alpha(fg, 0.10)} 40%, transparent)"
    p["--reply-hover"] = f"linear-gradient(to right, {with_alpha(fg, 0.05)} 40%, transparent)"

    # --- status ---
    p["--online"] = theme["green"]
    p["--dnd"] = theme["red"]
    p["--idle"] = theme["yellow"]
    p["--streaming"] = theme["magenta"]
    p["--offline"] = muted

    # --- borders ---
    p["--border-light"] = with_alpha(fg, 0.08)
    p["--border"] = with_alpha(fg, 0.14)
    p["--border-hover"] = with_alpha(fg, 0.14)
    p["--button-border"] = with_alpha(fg, 0.0)

    # --- base ramps ---
    for name, steps in ramps.items():
        for i, step in enumerate(steps, start=1):
            p[f"--{name}-{i}"] = step

    return p


def build_light_palette(theme: Dict[str, str]) -> Dict[str, str]:
    """Build Midnight variables for a light Omarchy theme."""
    bg = theme["background"]
    bg2 = theme["lighter_background"]
    bg3 = theme["dark_background"]
    fg = theme["foreground"]
    fg_muted = theme["muted"]
    accent = theme["accent"]
    muted = theme["muted"]
    ramps = _build_ramps(theme)

    p: Dict[str, str] = {}

    # --- text (dark on light background) ---
    p["--text-0"] = bg2
    p["--text-1"] = theme["bright_foreground"]
    p["--text-2"] = fg
    p["--text-3"] = fg
    p["--text-4"] = fg_muted
    p["--text-5"] = muted

    # --- backgrounds (light) ---
    p["--bg-1"] = bg3
    p["--bg-2"] = bg2
    p["--bg-3"] = bg3
    p["--bg-4"] = bg
    p["--hover"] = with_alpha(fg, 0.05)
    p["--active"] = with_alpha(fg, 0.10)
    p["--active-2"] = with_alpha(fg, 0.14)
    p["--message-hover"] = with_alpha(fg, 0.04)

    # --- accents ---
    p["--accent-1"] = ramps["blue"][0]
    p["--accent-2"] = ramps["blue"][1]
    p["--accent-3"] = ramps["blue"][2]
    p["--accent-4"] = ramps["blue"][3]
    p["--accent-5"] = ramps["blue"][4]
    p["--accent-new"] = ramps["blue"][1]
    p["--mention"] = f"linear-gradient(to right, {with_alpha(accent, 0.12)} 40%, transparent)"
    p["--mention-hover"] = f"linear-gradient(to right, {with_alpha(accent, 0.06)} 40%, transparent)"
    p["--reply"] = f"linear-gradient(to right, {with_alpha(fg, 0.08)} 40%, transparent)"
    p["--reply-hover"] = f"linear-gradient(to right, {with_alpha(fg, 0.04)} 40%, transparent)"

    # --- status ---
    p["--online"] = theme["green"]
    p["--dnd"] = theme["red"]
    p["--idle"] = theme["yellow"]
    p["--streaming"] = theme["magenta"]
    p["--offline"] = muted

    # --- borders ---
    p["--border-light"] = with_alpha(fg, 0.10)
    p["--border"] = with_alpha(fg, 0.16)
    p["--border-hover"] = with_alpha(fg, 0.16)
    p["--button-border"] = with_alpha(fg, 0.0)

    # --- base ramps ---
    for name, steps in ramps.items():
        for i, step in enumerate(steps, start=1):
            p[f"--{name}-{i}"] = step

    return p


def build_palette(theme: Dict[str, str]) -> Dict[str, str]:
    """Choose and build the palette matching the theme's mode."""
    mode = theme.get("mode", "dark")
    if mode == "light":
        return build_light_palette(theme)
    return build_dark_palette(theme)


def heuristic_mode(theme: Dict[str, str]) -> str:
    """Fallback: infer light/dark from the background luminance if needed."""
    lum = relative_luminance(theme["background"])
    if lum is None:
        return "dark"
    return "light" if lum > 0.5 else "dark"
