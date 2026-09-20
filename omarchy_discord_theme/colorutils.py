"""Color conversion utilities shared across the dynamic theme generator.

Handles parsing hex colors, converting between hex and HSL, and computing
lightness variants (used to build Midnight's 1..5 step color ramps).
"""

from __future__ import annotations

import re
import colorsys
from typing import Optional, Tuple

HEX_RE = re.compile(r"^#?([0-9a-fA-F]{6}|[0-9a-fA-F]{3})$")


def normalize_hex(value: str) -> Optional[str]:
    """Normalize a color value to '#rrggbb' lowercase, or None if invalid."""
    if not value:
        return None
    value = value.strip()
    if not HEX_RE.match(value):
        return None
    value = value.lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    return f"#{value.lower()}"


def hex_to_rgb(hex_color: str) -> Optional[Tuple[int, int, int]]:
    """Convert '#rrggbb' to an (r, g, b) tuple, or None if invalid."""
    normalized = normalize_hex(hex_color)
    if not normalized:
        return None
    h = normalized.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert (r, g, b) to a '#rrggbb' string."""
    return "#{:02x}{:02x}{:02x}".format(
        max(0, min(255, round(r))),
        max(0, min(255, round(g))),
        max(0, min(255, round(b))),
    )


def hex_to_hsl(hex_color: str) -> Optional[Tuple[float, float, float]]:
    """Convert '#rrggbb' to (h, s, l) with h in [0,360), s and l in [0,1]."""
    rgb = hex_to_rgb(hex_color)
    if not rgb:
        return None
    r, g, b = (c / 255.0 for c in rgb)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return (h * 360.0, s, l)


def hsl_to_hex(h: float, s: float, l: float) -> str:
    """Convert (h, s, l) with h in degrees, s/l in [0,1] to '#rrggbb'."""
    h = h % 360.0
    s = max(0.0, min(1.0, s))
    l = max(0.0, min(1.0, l))
    r, g, b = colorsys.hls_to_rgb(h / 360.0, l, s)
    return rgb_to_hex(r * 255.0, g * 255.0, b * 255.0)


def adjust_lightness(hex_color: str, delta: float) -> str:
    """Return hex_color with its lightness shifted by +delta (clamped 0..1)."""
    hsl = hex_to_hsl(hex_color)
    if not hsl:
        return normalize_hex(hex_color) or "#000000"
    h, s, l = hsl
    return hsl_to_hex(h, s, max(0.0, min(1.0, l + delta)))


def set_lightness(hex_color: str, target_l: float) -> str:
    """Return hex_color with its lightness set to target_l, keeping hue/sat."""
    hsl = hex_to_hsl(hex_color)
    if not hsl:
        return normalize_hex(hex_color) or "#000000"
    h, s, _ = hsl
    return hsl_to_hex(h, s, max(0.0, min(1.0, target_l)))


def with_alpha(hex_color: str, alpha: float) -> str:
    """Return an 'hsla(...)' string for hex_color at the given alpha."""
    hsl = hex_to_hsl(hex_color)
    if not hsl:
        return f"hsla(0, 0%, 0%, {alpha})"
    h, s, l = hsl
    return f"hsla({h:.1f}, {s * 100:.1f}%, {l * 100:.1f}%, {alpha})"


def relative_luminance(hex_color: str) -> Optional[float]:
    """Compute WCAG relative luminance in [0,1]; used for dark/light heuristics."""
    rgb = hex_to_rgb(hex_color)
    if not rgb:
        return None

    def channel(c: float) -> float:
        c /= 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b
