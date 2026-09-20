"""Generate the final Midnight Discord theme CSS for a given palette.

The base is the user's provided Midnight CSS (credit: refact0r, midnight-discord
https://github.com/refact0r/midnight-discord). Its layout, size, animation and
UI options are preserved verbatim; only the `:root` color block is replaced
with variables derived from the active Omarchy theme.

The generated file still `@import`s the shared Midnight build so layout/UI
updates track the original theme, while colors always follow Omarchy.
"""

from __future__ import annotations

import os
import re
import urllib.request
from typing import Dict, Optional

from .palette import build_palette
from .themeparser import parse_theme

# Matches a :root { ... } block. Assumes no nested braces inside.
ROOT_BLOCK_RE = re.compile(r":root\s*\{[^}]*\}", re.DOTALL)
# Matches the import statement line.
IMPORT_RE = re.compile(r"^\s*@import\s+url\(([^)]*)\)[^;]*;", re.MULTILINE)


def _fetch_source(path_or_url: str) -> str:
    """Load the base Midnight CSS from a local file or remote URL."""
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        with urllib.request.urlopen(path_or_url, timeout=30) as resp:
            return resp.read().decode("utf-8")
    with open(path_or_url, "r", encoding="utf-8") as fh:
        return fh.read()


def _format_vars(palette: Dict[str, str]) -> str:
    lines = []
    for key, value in palette.items():
        lines.append(f"    {key}: {value};")
    return "\n".join(lines)


def generate(theme: Optional[Dict[str, str]] = None,
             base_css_path: str = "",
             palette_override: Optional[Dict[str, str]] = None) -> str:
    """Return the full generated CSS as a string.

    theme: parsed Omarchy theme dict (mode + colors). If None, it is parsed
           from the active Omarchy theme automatically.
    base_css_path: path/URL of the Midnight CSS template. If empty, a minimal
           self-contained template is used (no external import).
    palette_override: if provided, used verbatim instead of deriving from theme.
    """
    if theme is None:
        theme = parse_theme()
    if palette_override is None:
        palette_override = build_palette(theme)

    mode = theme.get("mode", "dark")
    theme_name = theme.get("_name", "unknown")
    colors_block = _format_vars(palette_override)

    if base_css_path:
        base = _fetch_source(base_css_path)
        # Replace the :root color block with our generated palette.
        if ROOT_BLOCK_RE.search(base):
            base = ROOT_BLOCK_RE.sub(
                f":root {{\n{colors_block}\n}}", base, count=1
            )
        else:
            base = base.rstrip() + f"\n\n:root {{\n{colors_block}\n}}\n"
    else:
        base = (
            "/* Minimal Midnight base (no external import). Layout/UI options "
            "are not applied; colors only. */\n"
        )

    header = (
        "/**\n"
        " * @name midnight (omarchy dynamic)\n"
        " * @description Dynamically themed Midnight Discord theme that follows\n"
        " *   the active Omarchy desktop theme. Based on midnight-discord by\n"
        " *   refact0r (https://github.com/refact0r/midnight-discord).\n"
        " * @author omarchy-discord-theme\n"
        " * @authorId 0\n"
        " * @version 1.0.0\n"
        f" * @omarchy-theme {theme_name}\n"
        f" * @omarchy-mode {mode}\n"
        " * @invite nz87hXyvcy\n"
        " * @website https://github.com/refact0r/midnight-discord\n"
        " * @source https://github.com/refact0r/midnight-discord/blob/master/themes/flavors/midnight-tokyo-night.theme.css\n"
        "*/\n\n"
    )

    return header + base


def generate_to_file(output_path: str,
                     theme: Optional[Dict[str, str]] = None,
                     base_css_path: str = "",
                     palette_override: Optional[Dict[str, str]] = None) -> str:
    """Generate CSS and write it to output_path. Returns the generated text."""
    text = generate(theme, base_css_path, palette_override)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    tmp = output_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, output_path)
    return text
