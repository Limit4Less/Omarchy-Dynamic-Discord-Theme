"""Watch the Omarchy theme state for changes and regenerate the Discord theme.

Uses Linux inotify (via ctypes, no third-party deps) to react instantly when
the active theme's colors.toml or theme.name changes. Falls back to a small
polling loop if inotify is unavailable.

Note: Omarchy also fires a `theme-set.d` hook on every `omarchy theme set`
which triggers an immediate update; this watcher is a reliable backstop for any
change that bypasses the hook (e.g. a theme edited in place and re-staged).
"""

from __future__ import annotations

import ctypes
import ctypes.util
import errno
import os
import struct
import time
from typing import List, Optional

from . import logging as log
from .applier import run_update
from .config import load_config
from .themeparser import find_theme_colors_file, read_active_theme_name

IN_ACCESS = 0x00000001
IN_MODIFY = 0x00000002
IN_ATTRIB = 0x00000004
IN_CLOSE_WRITE = 0x00000008
IN_MOVED_TO = 0x00000080
IN_CREATE = 0x00000100
IN_DELETE = 0x00000200
IN_MASK = (
    IN_MODIFY
    | IN_ATTRIB
    | IN_CLOSE_WRITE
    | IN_MOVED_TO
    | IN_CREATE
    | IN_DELETE
)

_LIBC = None


def _libc():
    global _LIBC
    if _LIBC is None:
        _LIBC = ctypes.CDLL(None, use_errno=True)
        _LIBC.inotify_init.restype = ctypes.c_int
        _LIBC.inotify_add_watch.restype = ctypes.c_int
    return _LIBC


def inotify_available() -> bool:
    try:
        fd = _libc().inotify_init()
        if fd >= 0:
            os.close(fd)
            return True
    except Exception:
        pass
    return False


def _watch_dir(fd: int, path: str) -> Optional[int]:
    if not os.path.isdir(path):
        return None
    try:
        wd = _libc().inotify_add_watch(fd, path.encode(), IN_MASK)
        return wd if wd >= 0 else None
    except Exception:
        return None


class InotifyWatcher:
    """Blocking event source yielding on changes under the state dir."""

    def __init__(self, state_dir: str, watched_files: List[str]):
        self.state_dir = state_dir
        self.watched_files = set(os.path.abspath(p) for p in watched_files if p)
        self._buf = ctypes.create_string_buffer(4096)

    def next_event(self) -> bool:
        """Block until an event occurs. Returns True if it looks relevant."""
        fd = _libc().inotify_init()
        if fd < 0:
            return False
        try:
            _watch_dir(fd, self.state_dir)
            for path in self.watched_files:
                _watch_dir(fd, os.path.dirname(path))
            # Read events; treat any activity on the state dir as a change.
            _libc().read(fd, self._buf, 4096)
            return True
        finally:
            os.close(fd)


class PollWatcher:
    """Polling fallback when inotify is unavailable."""

    def __init__(self, watched_files: List[str], interval: float = 1.0):
        self.watched_files = [os.path.abspath(p) for p in watched_files if p]
        self.interval = interval
        self._mtime = self._snapshot()

    def _snapshot(self) -> dict:
        snap = {}
        for path in self.watched_files:
            try:
                snap[path] = os.stat(path).st_mtime_ns
            except OSError:
                snap[path] = None
        return snap

    def next_event(self) -> bool:
        time.sleep(self.interval)
        new = self._snapshot()
        changed = new != self._mtime
        self._mtime = new
        return changed


def build_watcher(cfg) -> object:
    paths = cfg["paths"]
    state_dir = paths.get("theme_state_dir", "~/.local/state/omarchy/current")
    state_dir = os.path.expanduser(state_dir)
    watched = [
        os.path.join(state_dir, "colors.toml"),
        os.path.join(state_dir, "theme.name"),
        find_theme_colors_file(),
    ]
    debounce = float(cfg.get("watch", {}).get("debounce_seconds", 1.0))

    if cfg.get("watch", {}).get("enabled", True) and inotify_available():
        return InotifyWatcher(state_dir, watched), debounce
    return PollWatcher(watched, interval=debounce), debounce


def watch_loop(cfg=None) -> None:
    """Run the watcher forever, regenerating the Discord theme on changes."""
    cfg = cfg or load_config()
    watcher, debounce = build_watcher(cfg)
    log.info("Watching Omarchy theme changes (inotify)" if isinstance(
        watcher, InotifyWatcher) else "Watching Omarchy theme changes (polling)")

    last_name = None
    while True:
        try:
            if watcher.next_event():
                time.sleep(debounce)
                name = read_active_theme_name()
                if name == last_name:
                    continue
                last_name = name
                update_and_log()
        except KeyboardInterrupt:
            log.info("Stopping watcher")
            break
        except Exception as exc:  # pragma: no cover - defensive
            log.error(f"Watcher error: {exc}")
            time.sleep(2.0)


def update_and_log() -> None:
    """Run one update and emit the requested log lines."""
    cfg = load_config()
    paths = cfg["paths"]
    try:
        result = run_update(
            base_css_path=paths.get("midnight_css", ""),
        )
        log.info(f"Detected Omarchy theme: {result['name']}")
        log.info(f"Theme mode: {result['mode'].upper()}")
        log.info(f"Primary color: {result['accent']}")
        log.info("Generated Discord theme")
        log.info(f"Discord theme updated ({result['injection']}: {result['applied']})")
    except Exception as exc:  # pragma: no cover - defensive
        log.error(f"Failed to update Discord theme: {exc}")


def main() -> None:
    cfg = load_config()
    logging_cfg = cfg.get("logging", {})
    log.configure(
        level=logging_cfg.get("level", "info"),
        log_file=logging_cfg.get("file", ""),
    )
    watch_loop(cfg)


if __name__ == "__main__":
    main()
