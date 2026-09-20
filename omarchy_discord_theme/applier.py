"""Apply the generated CSS to Discord via Equicord/Vencord.

Equicord (a Vencord fork) reads settings/quickCss.css and *hot-reloads* it via
a native file change listener, so writing the generated theme there updates
Discord live with no restart. This is the preferred injection point.

An alternative "themesdir" mode writes a *.theme.css into the themes folder,
which Equicord loads on startup but does not hot-reload.
"""

from __future__ import annotations

import os
import shutil
from typing import Dict, Optional

from .config import load_config
from .generator import generate

THEME_FILE_NAME = "midnight-omarchy.theme.css"


def _fmt_name(name: str, mode: str) -> str:
    return f"{name} [{mode.upper()}]"


def apply(generated_css: str,
          output_path: str,
          injection: str = "quickcss",
          themes_dir: str = "") -> Optional[str]:
    """Write generated_css to the configured Discord injection point.

    Returns a human-readable description of where it was applied, or None on
    failure.
    """
    if injection == "quickcss":
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        # Write IN PLACE (truncate + rewrite the same inode) rather than an
        # atomic rename. Equicord/Vencord watch the quickCss file with an
        # inotify listener on the file's inode; replacing the inode via
        # os.replace() would be missed, so the live hot-reload never fires.
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(generated_css)
            fh.flush()
            os.fsync(fh.fileno())
        return output_path

    if injection == "themesdir":
        if not themes_dir:
            return None
        os.makedirs(themes_dir, exist_ok=True)
        target = os.path.join(themes_dir, THEME_FILE_NAME)
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(generated_css)
        return target

    return None


def run_update(theme: Optional[Dict[str, str]] = None,
               base_css_path: str = "",
               dry_run: bool = False) -> Dict[str, str]:
    """One full update cycle: parse theme, generate CSS, write to Discord.

    Returns a dict with keys describing the result for logging.
    """
    cfg = load_config()
    paths = cfg["paths"]
    if theme is None:
        theme = parse_theme_import()
    name = theme.get("_name", "unknown")
    mode = theme.get("mode", "dark")

    generated = generate(
        theme=theme,
        base_css_path=base_css_path or paths.get("midnight_css", ""),
    )

    # Always write the generated file to cache so the theme-set hook / watcher
    # can reuse it and users can inspect it.
    cache_path = paths.get("generated_css", "")
    if cache_path and not dry_run:
        os.makedirs(os.path.dirname(os.path.abspath(cache_path)), exist_ok=True)
        tmp = cache_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(generated)
        os.replace(tmp, cache_path)

    injection = cfg.get("injection", "quickcss")
    if dry_run:
        applied = f"dry-run ({injection})"
    else:
        applied = apply(
            generated,
            output_path=paths.get("discord_quickcss", ""),
            injection=injection,
            themes_dir=paths.get("discord_themes_dir", ""),
        ) or "FAILED"

    return {
        "name": name,
        "mode": mode,
        "accent": theme.get("accent", ""),
        "applied": applied,
        "injection": injection,
    }


def parse_theme_import():
    from .themeparser import parse_theme
    return parse_theme()
