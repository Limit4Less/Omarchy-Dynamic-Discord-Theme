"""Minimal logging helper that writes to stderr and an optional log file."""

from __future__ import annotations

import os
from typing import Optional

_LEVELS = {"debug": 10, "info": 20, "warn": 30, "error": 40}
_level = 20
_log_file: Optional[str] = None


def configure(level: str = "info", log_file: str = "") -> None:
    global _level, _log_file
    _level = _LEVELS.get(level.lower(), 20)
    if log_file:
        os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)
        _log_file = log_file


def _write(msg: str) -> None:
    print(msg, flush=True)
    if _log_file:
        try:
            with open(_log_file, "a", encoding="utf-8") as fh:
                fh.write(msg + "\n")
        except OSError:
            pass


def log(level: str, msg: str) -> None:
    if _LEVELS.get(level.lower(), 20) < _level:
        return
    _write(f"[{level.upper()}] {msg}")


def debug(msg: str) -> None:
    log("debug", msg)


def info(msg: str) -> None:
    log("info", msg)


def warn(msg: str) -> None:
    log("warn", msg)


def error(msg: str) -> None:
    log("error", msg)
