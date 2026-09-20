"""Command-line entry point for omarchy-discord-theme.

Subcommands:
  apply [--config PATH]   Run one update cycle (detect theme, generate, apply).
  watch [--config PATH]   Watch for Omarchy theme changes and update live.
  dry-run [--config PATH] Detect and generate without writing to Discord.
  version                 Print version.
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from . import logging as log
from .applier import run_update
from .config import load_config


def _setup_logging(cfg) -> None:
    lc = cfg.get("logging", {})
    log.configure(level=lc.get("level", "info"), log_file=lc.get("file", ""))


def cmd_apply(cfg) -> int:
    paths = cfg["paths"]
    result = run_update(base_css_path=paths.get("midnight_css", ""))
    log.info(f"Detected Omarchy theme: {result['name']}")
    log.info(f"Theme mode: {result['mode'].upper()}")
    log.info(f"Primary color: {result['accent']}")
    log.info("Generated Discord theme")
    log.info(f"Discord theme updated ({result['injection']}: {result['applied']})")
    return 0


def cmd_dry_run(cfg) -> int:
    paths = cfg["paths"]
    result = run_update(base_css_path=paths.get("midnight_css", ""), dry_run=True)
    log.info(f"Detected Omarchy theme: {result['name']}")
    log.info(f"Theme mode: {result['mode'].upper()}")
    log.info(f"Primary color: {result['accent']}")
    log.info(f"Would apply to ({result['injection']}: {result['applied']})")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="omarchy-discord-theme",
                                     description="Dynamic Discord theme for Omarchy")
    parser.add_argument("--config", default="", help="path to config.toml")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("apply", help="detect theme and apply immediately")
    sub.add_parser("watch", help="watch for theme changes and update live")
    sub.add_parser("dry-run", help="detect and generate without writing to Discord")
    sub.add_parser("version", help="print version")

    args = parser.parse_args(argv)

    if args.command == "version":
        print(__version__)
        return 0

    cfg = load_config(args.config)
    _setup_logging(cfg)

    if args.command == "apply":
        return cmd_apply(cfg)
    if args.command == "dry-run":
        return cmd_dry_run(cfg)
    if args.command == "watch":
        from .watcher import watch_loop
        watch_loop(cfg)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
