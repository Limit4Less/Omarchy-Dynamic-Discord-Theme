"""Parse an Omarchy theme's colors.toml into a normalized color dictionary.

Omarchy themes live in ~/.config/omarchy/themes/<slug>/colors.toml (user) or
/usr/share/omarchy/themes/<slug>/colors.toml (stock). The currently active
theme is *staged* at ~/.local/state/omarchy/current/theme/colors.toml with a
theme.name file alongside it holding the slug.

This module reads that staged location so it always reflects the active theme
regardless of which directory the theme originally came from, then normalizes
the raw colors into a dict with guaranteed keys, applying sensible fallbacks
when a theme is missing any of them.
"""

from __future__ import annotations

import os
import tomllib
from typing import Dict, Optional

from .colorutils import normalize_hex

# Canonical ordering + fallbacks for every color we care about.
# Fallbacks reference other theme keys so a sparse theme still yields a usable
# palette. bright_* falls back to the base color when absent.
#
# NOTE: the fallback graph must stay ACYCLIC (no two keys pointing at each
# other), otherwise a sparse theme triggers infinite recursion.
COLOR_FIELDS: Dict[str, Optional[str]] = {
    # semantic
    "accent": "blue",
    "selection": "lighter_background",
    "muted": "dark_foreground",
    # backgrounds
    "background": None,
    "dark_background": "background",
    "darker_background": "dark_background",
    "lighter_background": "background",
    # foregrounds
    "foreground": None,
    "dark_foreground": "foreground",
    "light_foreground": "foreground",
    "bright_foreground": "foreground",
    # base colors
    "red": None,
    "yellow": None,
    "orange": "yellow",
    "green": None,
    "cyan": "blue",
    "blue": None,
    "magenta": "blue",
    "brown": "orange",
    # bright variants (fall back to base)
    "bright_red": "red",
    "bright_yellow": "yellow",
    "bright_orange": "orange",
    "bright_green": "green",
    "bright_cyan": "cyan",
    "bright_blue": "blue",
    "bright_magenta": "magenta",
}

# Colors that must exist with a real value or the whole theme fails.
REQUIRED = {"background", "foreground", "accent", "blue"}

# Fallback values used only if even the chained fallbacks come up empty.
ABSOLUTE_FALLBACKS: Dict[str, str] = {
    "background": "#1e1e2e",
    "dark_background": "#161622",
    "darker_background": "#101019",
    "lighter_background": "#313244",
    "foreground": "#cdd6f4",
    "dark_foreground": "#6c7086",
    "light_foreground": "#bac2de",
    "bright_foreground": "#cdd6f4",
    "accent": "#89b4fa",
    "selection": "#45475a",
    "muted": "#585b70",
    "red": "#f38ba8",
    "yellow": "#f9e2af",
    "orange": "#f6b6ab",
    "green": "#a6e3a1",
    "cyan": "#94e2d5",
    "blue": "#89b4fa",
    "magenta": "#f5c2e7",
    "brown": "#7b5b55",
    "bright_red": "#f38ba8",
    "bright_yellow": "#f9e2af",
    "bright_orange": "#f6b6ab",
    "bright_green": "#a6e3a1",
    "bright_cyan": "#94e2d5",
    "bright_blue": "#89b4fa",
    "bright_magenta": "#f5c2e7",
}


def find_theme_colors_file() -> Optional[str]:
    """Return the path to the active theme's staged colors.toml if it exists."""
    candidates = [
        os.path.expanduser("~/.local/state/omarchy/current/theme/colors.toml"),
        os.path.expanduser("~/.config/omarchy/themes/current/colors.toml"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def read_active_theme_name() -> Optional[str]:
    """Return the slug of the active theme (e.g. 'catppuccin'), or None."""
    name_file = os.path.expanduser("~/.local/state/omarchy/current/theme.name")
    if os.path.isfile(name_file):
        with open(name_file, "r", encoding="utf-8") as fh:
            name = fh.read().strip()
            if name:
                return name
    return None


def read_colors_toml(path: str) -> Dict[str, str]:
    """Read a colors.toml and return only its color entries as strings."""
    with open(path, "rb") as fh:
        data = tomllib.load(fh)
    colors: Dict[str, str] = {}
    for key, value in data.items():
        if isinstance(value, str) and value.strip().startswith("#"):
            colors[key] = normalize_hex(value) or ""
        elif isinstance(value, str):
            colors[key] = value.strip()
    return colors


def resolve_colors(raw: Dict[str, str]) -> Dict[str, str]:
    """Normalize raw theme colors into a complete dict with fallbacks."""
    resolved: Dict[str, str] = {}

    # First pass: materialize each color, following its fallback chain.
    memo: Dict[str, str] = {}

    def resolve(key: str) -> str:
        if key in memo:
            return memo[key]
        value = raw.get(key)
        if value and value.startswith("#"):
            memo[key] = value
            return value
        fallback = COLOR_FIELDS.get(key)
        if fallback:
            memo[key] = resolve(fallback)
            return memo[key]
        memo[key] = ABSOLUTE_FALLBACKS.get(key, "#000000")
        return memo[key]

    for key in COLOR_FIELDS:
        resolved[key] = resolve(key)

    return resolved


def parse_theme(colors_path: Optional[str] = None) -> Dict[str, str]:
    """Parse the active Omarchy theme into a normalized color dict.

    Returns the resolved colors plus a 'mode' key ('dark' or 'light') and a
    '_name' key holding the theme slug.
    """
    path = colors_path or find_theme_colors_file()
    raw: Dict[str, str] = {}
    mode = "dark"

    if path and os.path.isfile(path):
        raw = read_colors_toml(path)
        mode = raw.get("mode", "dark").lower()
        if mode not in ("dark", "light"):
            mode = "dark"

    resolved = resolve_colors(raw)
    resolved["mode"] = mode
    resolved["_name"] = read_active_theme_name() or "unknown"
    return resolved
