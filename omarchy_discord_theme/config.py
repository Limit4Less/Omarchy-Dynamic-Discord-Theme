"""Configuration loading and defaults for the dynamic Discord theme.

All paths and behaviors are configurable via a TOML file. Defaults point at
the standard Omarchy and Equicord locations but can be overridden for other
setups (e.g. stock Discord + Vencord, BetterDiscord, etc.).
"""

from __future__ import annotations

import os
import tomllib
from typing import Any, Dict

# Per-client defaults: how the generated CSS reaches Discord for each mod.
#   quickcss  -> a settings/quickCss.css file that the mod hot-reloads live
#   themesdir -> a *.theme.css dropped into a themes folder (loads at startup)
CLIENT_DEFAULTS: Dict[str, Dict[str, str]] = {
    "equicord": {
        "client_dir": "~/.config/Equicord",
        "injection": "quickcss",
        "quickcss": "~/.config/Equicord/settings/quickCss.css",
        "themes_dir": "~/.config/Equicord/themes",
    },
    "vencord": {
        "client_dir": "~/.config/Vencord",
        "injection": "quickcss",
        "quickcss": "~/.config/Vencord/settings/quickCss.css",
        "themes_dir": "~/.config/Vencord/themes",
    },
    "betterdiscord": {
        "client_dir": "~/.config/BetterDiscord",
        "injection": "themesdir",
        "quickcss": "~/.config/BetterDiscord/custom.css",
        "themes_dir": "~/.config/BetterDiscord/themes",
    },
}

DEFAULT_CONFIG: Dict[str, Any] = {
    # Discord client mod: "equicord" | "vencord" | "betterdiscord"
    # When set and no explicit paths are provided, the matching per-client
    # defaults above are applied.
    "client": "equicord",
    "paths": {
        # Omarchy active theme state (colors.toml + theme.name)
        "theme_state_dir": "~/.local/state/omarchy/current",
        # Base Midnight CSS to derive the dynamic theme from. May be a local
        # file or a remote URL starting with http(s).
        "midnight_css": "~/.config/omarchy/discord-theme/midnight.css",
        # Where the generated theme file is written.
        "generated_css": "~/.cache/omarchy-discord-theme/generated.css",
        # Where Equicord/Vencord reads its Quick CSS from (hot-reloaded).
        "discord_quickcss": "~/.config/Equicord/settings/quickCss.css",
        # Alternative: a directory of *.theme.css files (not hot-reloaded).
        "discord_themes_dir": "~/.config/Equicord/themes",
    },
    "injection": "quickcss",  # "quickcss" or "themesdir"
    "theme": {
        # Optional explicit override of the active theme dir. Leave empty to
        # auto-detect from theme_state_dir.
        "override_colors": "",
    },
    "watch": {
        "enabled": True,
        "debounce_seconds": 1.0,
    },
    "logging": {
        "level": "info",  # debug | info | warn | error
        "file": "~/.cache/omarchy-discord-theme/discord-theme.log",
    },
}

CONFIG_PATHS = [
    "/etc/omarchy-discord-theme/config.toml",
    "~/.config/omarchy/discord-theme.toml",
    "~/.config/omarchy-discord-theme/config.toml",
]

def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def _expand(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _expand(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_expand(v) for v in obj]
    if isinstance(obj, str) and obj.startswith("~"):
        return os.path.expanduser(obj)
    return obj


def _apply_client_defaults(config: Dict[str, Any]) -> Dict[str, Any]:
    """If a client is configured and no explicit per-client paths are given,
    fill them in from CLIENT_DEFAULTS so the config stays minimal."""
    client = config.get("client", "").lower()
    if not client or client not in CLIENT_DEFAULTS:
        return config
    cd = CLIENT_DEFAULTS[client]
    paths = config["paths"]
    # Only override a path if the user has NOT set it explicitly. We track
    # explicit settings by checking whether the value still equals the generic
    # default (i.e. it was not overridden by a user config file).
    generic_quickcss = "~/.config/Equicord/settings/quickCss.css"
    generic_themes = "~/.config/Equicord/themes"
    if paths.get("discord_quickcss", generic_quickcss) == generic_quickcss:
        paths["discord_quickcss"] = cd["quickcss"]
    if paths.get("discord_themes_dir", generic_themes) == generic_themes:
        paths["discord_themes_dir"] = cd["themes_dir"]
    if config.get("injection", "quickcss") == "quickcss":
        config["injection"] = cd["injection"]
    return config


def load_config(path: str = "") -> Dict[str, Any]:
    """Load config, merging in any user file found at the known locations."""
    import copy
    config = copy.deepcopy(DEFAULT_CONFIG)
    paths = [path] if path else [p for p in CONFIG_PATHS if os.path.exists(os.path.expanduser(p))]
    for p in paths:
        expanded = os.path.expanduser(p)
        if os.path.isfile(expanded):
            try:
                with open(expanded, "rb") as fh:
                    user = tomllib.load(fh)
                config = _deep_merge(config, user)
            except (tomllib.TOMLDecodeError, OSError) as exc:
                print(f"[warn] failed to read config {expanded}: {exc}")
    config = _apply_client_defaults(config)
    return _expand(config)
