# omarchy-discord-theme

Dynamically theme **Discord** to match your **active Omarchy desktop theme** —
automatically, live, with no manual edits and no restarts.

Built on the excellent [**Midnight**](https://github.com/refact0r/midnight-discord)
Discord theme by [refact0r](https://www.refact0r.dev). All credit for the base
Discord theme (layout, UI, structure) goes to refact0r — this project only
makes Midnight's *colors* follow your Omarchy theme.

```text
Omarchy theme (colors.toml)
      │  detected
      ▼
Theme detector ───────────── reads ~/.local/state/omarchy/current
      │
      ▼
Color/theme parser ───────── normalizes colors + dark/light mode
      │
      ▼
CSS variable generator ───── maps theme → Midnight :root variables
      │
      ▼
Midnight overrides ────────── user's midnight.css with injected colors
      │
      ▼
Equicord Quick CSS ────────── hot-reloaded, applied live
```

Change your theme and Discord follows:

| Omarchy theme | Discord becomes | Uses colors from |
|---|---|---|
| `Catppuccin Latte` (light) | **Light** | Catppuccin Latte |
| `Catppuccin` (dark) | **Dark** | Catppuccin Mocha / dark |
| `Cincinnati`, `Tokyo Night`, … | **Dark** | the active theme |
| `White`, `Flexoki Light`, … | **Light** | the active theme |

It works with **any** Omarchy theme — not just Catppuccin — because it reads
each theme's `colors.toml` and derives a full Midnight palette from it.

---

## How it works

1. **Detect** — the active theme is always staged by Omarchy at
   `~/.local/state/omarchy/current/` (`theme.name` + `theme/colors.toml`).
2. **Parse** — the `colors.toml` is read (TOML) and normalized with fallbacks
   for any missing color.
3. **Dark/light** — each theme declares `mode = "dark" | "light"`; that decides
   whether Discord gets a light or dark palette.
4. **Generate** — the theme's colors are mapped onto Midnight's `:root` CSS
   variables (`--bg-*`, `--text-*`, `--accent-*`, `--blue-*`…). Color ramps
   are derived from a single base color so any theme yields a coherent palette.
5. **Apply** — the generated CSS is written to Equicord's Quick CSS file, which
   Equicord **hot-reloads live**. No Discord restart needed.

**Two triggers keep it instant and reliable:**

- **Omarchy hook** — `omarchy theme set` fires `theme-set.d` hooks, so the
  moment you switch themes the Discord theme updates immediately.
- **systemd user service** — a persistent watcher (Linux inotify) also watches
  the theme state files as a backstop, and re-applies on login/boot.

---

## Requirements

- **Omarchy** Linux (Arch-based, Hyprland)
- **Discord** with one of:
  - **Equicord** (a Vencord fork) — recommended, Quick CSS hot-reloads live
  - **Vencord** — Quick CSS hot-reloads live
  - **BetterDiscord** — themes load at startup (needs a theme toggle/reload)
- **Python 3.11+** (uses only the standard library — no pip packages)
- **Network** on first load (Midnight `@import`s its base build from GitHub)

> For Equicord/Vencord, Quick CSS must be on. In
> `~/.config/<Mod>/settings/settings.json` set `"useQuickCss": true`.

---

## Installation

Clone the repo and run the installer. It asks which Discord client mod you use
(Equicord / Vencord / BetterDiscord) and configures the injection for it
automatically:

```bash
git clone https://github.com/Limit4Less/Omarchy-Dynamic-Discord-Theme
cd omarchy-discord-theme
./install.sh /path/to/your/midnight.css
```

If you don't pass a file, place a Midnight flavor at
`~/.config/omarchy/discord-theme/midnight.css` yourself.

The installer:

- asks which Discord client mod you use (defaults to an installed one)
- installs the binary to `~/.local/bin/omarchy-discord-theme`
- copies the Python library to `~/.local/share/omarchy-discord-theme/`
- installs your base Midnight CSS to `~/.config/omarchy/discord-theme/`
- writes a default config to `~/.config/omarchy/discord-theme.toml` with the
  correct `client` and paths for your mod
- installs the `theme-set.d` hook (`~/.config/omarchy/hooks/theme-set.d/99-discord-theme`)
- enables a **systemd user service** (`omarchy-discord-theme.service`) that
  **starts at login** and keeps Discord in sync
- applies your current theme immediately

### First-run

On login the service starts, detects the active theme, generates the matching
Discord theme, applies it, and watches for changes. Every time you switch your
Omarchy theme, Discord updates automatically.

---

## Usage

```bash
omarchy-discord-theme apply       # detect current theme and apply now
omarchy-discord-theme watch       # run the watcher in the foreground
omarchy-discord-theme dry-run     # detect + generate, don't write to Discord
omarchy-discord-theme version
```

You normally don't need to run anything manually — switching your Omarchy theme
does it for you:

```bash
omarchy theme set "Catppuccin Latte"   # Discord -> light, latte colors
omarchy theme set "Catppuccin"         # Discord -> dark, mocha colors
```

---

## Configuration

Edit `~/.config/omarchy/discord-theme.toml`. All paths are configurable.

```toml
# Discord client mod: "equicord" | "vencord" | "betterdiscord"
client = "equicord"

[paths]
theme_state_dir    = "~/.local/state/omarchy/current"
midnight_css       = "~/.config/omarchy/discord-theme/midnight.css"
generated_css      = "~/.cache/omarchy-discord-theme/generated.css"
discord_quickcss   = "~/.config/Equicord/settings/quickCss.css"
discord_themes_dir = "~/.config/Equicord/themes"

injection = "quickcss"   # "quickcss" (Equicord/Vencord) or "themesdir" (BetterDiscord)

[watch]
enabled = true
debounce_seconds = 1.0

[logging]
level = "info"   # debug | info | warn | error
file  = "~/.cache/omarchy-discord-theme/discord-theme.log"
```

- **`client`** selects your mod. The installer sets it for you. When set, the
  matching `injection` and paths are used automatically (see the table below).
- **`injection = "quickcss"`** (Equicord/Vencord) writes to `discord_quickcss` —
  live, no restart. Recommended.
- **`injection = "themesdir"`** (BetterDiscord) writes `midnight-omarchy.theme.css`
  into `discord_themes_dir`. You must enable it in Discord and toggle it (or
  restart Discord) to apply changes.
- **`midnight_css`** can also be a **remote URL** (`https://…`) instead of a
  local file.

### Per-client defaults

| `client` | `injection` | `discord_quickcss` | `discord_themes_dir` |
|---|---|---|---|
| `equicord` | `quickcss` | `~/.config/Equicord/settings/quickCss.css` | `~/.config/Equicord/themes` |
| `vencord` | `quickcss` | `~/.config/Vencord/settings/quickCss.css` | `~/.config/Vencord/themes` |
| `betterdiscord` | `themesdir` | `~/.config/BetterDiscord/custom.css` | `~/.config/BetterDiscord/themes` |

You only need to set `client` (and override any path you want); the rest is
filled in automatically.

---

## Logging

You'll see useful lines in the journal / log file:

```text
Detected Omarchy theme: Catppuccin Latte
Theme mode: LIGHT
Primary color: #1e66f5
Generated Discord theme
Discord theme updated (quickcss: /home/limit/.config/Equicord/settings/quickCss.css)
```

View them with:

```bash
journalctl --user -u omarchy-discord-theme -f
tail -f ~/.cache/omarchy-discord-theme/discord-theme.log
```

---

## Color mapping (extensible)

Omarchy themes use a standard `colors.toml` with these keys. `themeparser.py`
reads them and fills in missing ones with sensible fallbacks, so even a sparse
theme produces a usable Discord theme.

| Omarchy key | Used for (Midnight) |
|---|---|
| `mode` | light / dark decision |
| `background`, `dark_background`, `darker_background`, `lighter_background` | `--bg-1..4`, borders |
| `foreground`, `dark_foreground`, `bright_foreground` | `--text-1..5`, hover states |
| `accent` | `--accent-1..5`, `--mention`, links |
| `selection`, `muted` | muted text, borders |
| `green` / `red` / `yellow` / `magenta` | `--green-*` / `--red-*` / `--yellow-*` / `--purple-*`, online/dnd/idle/streaming |

To tweak how any color maps to Midnight variables, edit
`palette.py` (`build_dark_palette` / `build_light_palette`).

---

## Troubleshooting

- **Discord shows default colors** —
  - Equicord/Vencord: ensure `useQuickCss: true` in
    `~/.config/<Mod>/settings/settings.json`, and disable other enabled themes
    in the mod's Settings → Themes so they don't fight the dynamic theme.
  - BetterDiscord: enable `midnight-omarchy.theme.css` in Discord →
    Settings → Themes.
- **No change after switching themes** — check the service is running:
  `systemctl --user status omarchy-discord-theme`, then
  `omarchy-discord-theme apply` manually. BetterDiscord needs a theme
  toggle/reload (it doesn't hot-reload).
- **Wrong mod selected** — set `client` in the config and reinstall, or run
  `omarchy-discord-theme apply` after editing it.
- **Empty / wrong colors** — confirm the active theme staged at
  `~/.local/state/omarchy/current/theme/colors.toml` has a `mode` field and
  `background`/`foreground`/`accent` keys.
- **No network** — the generated theme `@import`s Midnight's base build from
  GitHub. Without internet the base layout won't load (colors only). You can
  vendor the build locally if needed.
- **Broken after a Discord update** — because we only touch CSS variables on
  top of refact0r's maintained Midnight build, and the build tracks Discord
  changes, the theme keeps working. No core code is injected.

---

## Architecture

```
omarchy-discord-theme/
├── bin/omarchy-discord-theme      # CLI launcher
├── install.sh                     # installer
├── install/
│   ├── config.toml                # default config
│   ├── omarchy-discord-theme.service   # systemd user unit
│   └── theme-set-hook.sh          # theme-set.d hook
└── omarchy_discord_theme/
    ├── cli.py        # subcommands: apply / watch / dry-run / version
    ├── config.py     # config loading + defaults (client-aware: equicord/vencord/betterdiscord)
    ├── themeparser.py# Omarchy colors.toml -> normalized colors (+fallbacks)
    ├── palette.py    # colors -> Midnight CSS variables (dark/light)
    ├── generator.py  # Midnight template + injected palette -> final CSS
    ├── applier.py    # write CSS to Equicord Quick CSS / themes dir
    ├── watcher.py    # inotify watcher for theme changes
    ├── colorutils.py # hex/HSL helpers
    └── logging.py    # simple logging
```

Each stage is isolated so you can swap or extend any part (e.g. add a new
injection target, change color mappings, or support another Discord client).

---

## Acknowledgements

- **refact0r** — the Midnight Discord theme and its color system
  (<https://github.com/refact0r/midnight-discord>)
- **Omarchy** — the Arch-based Linux distribution this is built for
  (<https://omarchy.org>)
- **Equicord** — the Discord client mod used for hot-reloading Quick CSS

---

## License

MIT. The Midnight base theme remains © refact0r under its own license.
