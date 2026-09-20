#!/bin/bash
# Omarchy theme-set hook: regenerate the dynamic Discord theme immediately.
# Installed to ~/.config/omarchy/hooks/theme-set.d/ by the installer.
# $1 = snake-cased theme slug (e.g. "catppuccin-latte").

BIN="${OMARCHY_DISCORD_THEME_BIN:-$HOME/.local/bin/omarchy-discord-theme}"
CONFIG="${OMARCHY_DISCORD_THEME_CONFIG:-}"

[[ -x "$BIN" ]] || { echo "[discord-theme] binary not found: $BIN" >&2; exit 0; }

# Fire and forget so a slow network fetch never blocks theme switching.
if [[ -n "$CONFIG" ]]; then
    "$BIN" --config "$CONFIG" apply &
else
    "$BIN" apply &
fi

exit 0
