#!/bin/bash
# Installer for omarchy-discord-theme.
#
# Usage: ./install.sh [path/to/midnight.css]
#
# Asks which Discord client mod you use (Equicord / Vencord / BetterDiscord),
# configures the theme injection for it, installs the theme-set hook and a
# systemd user service (so it starts at login and keeps Discord's theme in
# sync), then applies your current theme immediately.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_DIR="$REPO_DIR/omarchy_discord_theme"

BIN_DEST="$HOME/.local/bin/omarchy-discord-theme"
LIB_DEST="$HOME/.local/share/omarchy-discord-theme"
CONFIG_DEST="$HOME/.config/omarchy/discord-theme.toml"
BASE_DEST="$HOME/.config/omarchy/discord-theme/midnight.css"
HOOK_DIR="$HOME/.config/omarchy/hooks/theme-set.d"
SERVICE_NAME="omarchy-discord-theme.service"
SERVICE_SRC="$REPO_DIR/install/omarchy-discord-theme.service"
CONFIG_SRC="$REPO_DIR/install/config.toml"
HOOK_SRC="$REPO_DIR/install/theme-set-hook.sh"

detect_client() {
    # Return the first installed mod, best-effort, for a default.
    [[ -d "$HOME/.config/Equicord" ]]   && { echo "equicord"; return; }
    [[ -d "$HOME/.config/Vencord" ]]    && { echo "vencord"; return; }
    [[ -d "$HOME/.config/BetterDiscord" ]] && { echo "betterdiscord"; return; }
    echo "equicord"
}

echo "==> omarchy-discord-theme installer"
echo

# 1. Ask which Discord client mod.
DEFAULT_CLIENT="$(detect_client)"
echo "Which Discord client mod do you use?"
echo "  1) Equicord       (recommended: live hot-reload)"
echo "  2) Vencord        (live hot-reload)"
echo "  3) BetterDiscord  (loads themes at startup; needs theme reload)"
printf "Choice [%s]: " "$DEFAULT_CLIENT"
read -r CLIENT_CHOICE
CLIENT="${DEFAULT_CLIENT}"
case "${CLIENT_CHOICE:-}" in
    1|e|equicord)       CLIENT="equicord" ;;
    2|v|vencord)        CLIENT="vencord" ;;
    3|b|betterdiscord)  CLIENT="betterdiscord" ;;
    "")                 CLIENT="${DEFAULT_CLIENT}" ;;
    *)                  CLIENT="equicord" ;;
esac
echo "    Using client: $CLIENT"

# 2. Base Midnight CSS.
BASE_CSS="${1:-}"
if [[ -z "$BASE_CSS" && -f "$BASE_DEST" ]]; then
    BASE_CSS="$BASE_DEST"   # reuse existing installed base
fi

echo "==> Installing omarchy-discord-theme"

# 3. Library + launcher
mkdir -p "$LIB_DEST" "$(dirname "$BIN_DEST")"
cp -r "$PKG_DIR" "$LIB_DEST/"
cat > "$BIN_DEST" <<EOF
#!/usr/bin/env python3
import os, sys
sys.path.insert(0, os.path.expanduser("$LIB_DEST"))
from omarchy_discord_theme.cli import main
if __name__ == "__main__":
    sys.exit(main())
EOF
chmod +x "$BIN_DEST"
echo "    binary: $BIN_DEST"

# 4. Base Midnight CSS
mkdir -p "$(dirname "$BASE_DEST")"
if [[ -n "$BASE_CSS" && -f "$BASE_CSS" ]]; then
    cp "$BASE_CSS" "$BASE_DEST"
    echo "    base css: $BASE_CSS -> $BASE_DEST"
else
    if [[ ! -f "$BASE_DEST" ]]; then
        echo "    WARNING: no midnight.css provided; create $BASE_DEST with your flavor."
    fi
fi

# 5. Config (do not clobber an existing one)
mkdir -p "$(dirname "$CONFIG_DEST")"
if [[ -f "$CONFIG_DEST" ]]; then
    # Update the client in an existing config. Remove any stray "client =" line
    # (which may sit under a [table] and be invalid at top level), then prepend
    # the top-level client key at the very top of the file.
    grep -v '^[[:space:]]*client[[:space:]]*=' "$CONFIG_DEST" > "$CONFIG_DEST.tmp" || true
    { printf 'client = "%s"\n\n' "$CLIENT"; cat "$CONFIG_DEST.tmp"; } > "$CONFIG_DEST"
    rm -f "$CONFIG_DEST.tmp"
else
    cp "$CONFIG_SRC" "$CONFIG_DEST"
    sed -i "s/^client *=.*/client = \"$CLIENT\"/" "$CONFIG_DEST"
fi
echo "    config: $CONFIG_DEST (client=$CLIENT)"

# 6. Theme-set hook (instant trigger on 'omarchy theme set')
mkdir -p "$HOOK_DIR"
HOOK_FILE="$HOOK_DIR/99-discord-theme"
cp "$HOOK_SRC" "$HOOK_FILE"
chmod +x "$HOOK_FILE"
echo "    hook: $HOOK_FILE"

# 7. systemd user service (persistent watcher, starts at login)
cp "$SERVICE_SRC" "$HOME/.config/systemd/user/$SERVICE_NAME"
systemctl --user daemon-reload >/dev/null 2>&1 || true
systemctl --user enable --now "$SERVICE_NAME" >/dev/null 2>&1 || \
    echo "    WARNING: could not enable systemd service; run: systemctl --user enable --now $SERVICE_NAME"
echo "    service: $SERVICE_NAME (enabled at login)"

# 8. Initial apply
echo "==> Applying current theme"
"$BIN_DEST" apply || echo "    WARNING: initial apply failed"

echo "==> Done."
echo
echo "Notes for $CLIENT:"
case "$CLIENT" in
    equicord|vencord)
        echo "  - Ensure Quick CSS is enabled (useQuickCss: true) in"
        echo "    $HOME/.config/$( [ "$CLIENT" = equicord ] && echo Equicord || echo Vencord )/settings/settings.json"
        echo "  - Disable any other enabled themes so the dynamic theme is the one you see."
        echo "  - The theme hot-reloads live when you switch Omarchy themes."
        ;;
    betterdiscord)
        echo "  - Enable the generated theme in Discord: Settings -> Themes ->"
        echo "    'midnight-omarchy.theme.css' (in the themes folder)."
        echo "  - BetterDiscord loads themes at startup; after switching an Omarchy"
        echo "    theme, toggle the theme off/on (or restart Discord) to apply it."
        ;;
esac
echo
echo "Try it: omarchy theme set 'Catppuccin Latte' then 'Catppuccin'"
