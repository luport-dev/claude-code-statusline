#!/usr/bin/env python3
"""Render every relevant status line variation in one go.

Runs scripts/statusline.py against fixed JSON snapshots with different config
overrides and prints each result with a heading. Intended for screenshotting.

Usage:
    python scripts/preview.py            # full preview (all sections)
    python scripts/preview.py --small    # 5 representative variations only
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parent.parent
STATUSLINE = REPO / "scripts" / "statusline.py"
CONFIG_PATH   = Path.home() / ".claude" / "statusline_config.json"
SETTINGS_PATH = Path.home() / ".claude" / "settings.json"

ESC = "\x1b"
RESET = f"{ESC}[0m"
BOLD = f"{ESC}[1m"
DIM = f"{ESC}[2m"
HEADER = f"{ESC}[1;38;5;39m"

SCENARIOS = {
    "low":    {"ctx": 12, "tkn": 12, "five": 18, "week": 8,  "tokens": 5_400},
    "medium": {"ctx": 65, "tkn": 65, "five": 62, "week": 45, "tokens": 84_000},
    "high":   {"ctx": 88, "tkn": 88, "five": 85, "week": 78, "tokens": 178_500},
}

MODELS = [
    ("Opus 4.7",   "opus"),
    ("Sonnet 4.6", "sonnet"),
    ("Haiku 4.5",  "haiku"),
]

BAR_STYLES = ["fill", "block", "dot", "square"]
DECORATIONS = ["emoji", "label"]
DISPLAY_MODES = ["text", "bar", "both"]


def make_input(model_name: str, effort: str, scenario: dict) -> str:
    return json.dumps({
        "cwd": str(REPO),
        "worktree": {"name": "feat-statusline"},
        "model": {"display_name": model_name},
        "effort": {"level": effort},
        "context_window": {
            "used_percentage":     scenario["ctx"],
            "total_input_tokens":  scenario["tokens"],
        },
        "rate_limits": {
            "five_hour":  {"used_percentage": scenario["five"]},
            "seven_day":  {"used_percentage": scenario["week"]},
        },
    })


def render(config: dict, payload: str, thinking: bool = False) -> str:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config), encoding="utf-8")
    # statusline.py reads alwaysThinkingEnabled from ~/.claude/settings.json
    existing: dict = {}
    if SETTINGS_PATH.exists():
        try:
            existing = json.loads(SETTINGS_PATH.read_text(encoding="utf-8")) or {}
        except Exception:
            existing = {}
    existing["alwaysThinkingEnabled"] = bool(thinking)
    SETTINGS_PATH.write_text(json.dumps(existing), encoding="utf-8")
    r = subprocess.run(
        [sys.executable, str(STATUSLINE)],
        input=payload,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return r.stdout.rstrip("\n")


def section(title: str) -> None:
    print()
    print(f"{HEADER}── {title} {'─' * max(0, 72 - len(title))}{RESET}")
    print()


def label(text: str) -> None:
    print(f"{DIM}{text}{RESET}")


def all_metrics(mode: str) -> dict:
    return {k: {"display": mode} for k in
            ("model", "effort", "thinking", "ctx", "tkn", "five", "week")}


def run_full() -> None:
    # 1. Threshold colour progression (low / medium / high) — default config
    section("1. Threshold stages (low / medium / high usage)")
    for stage, scen in SCENARIOS.items():
        cfg = {
            "decoration": "emoji",
            "bar_style":  "fill",
            "metrics":    all_metrics("both"),
        }
        payload = make_input("Sonnet 4.6", "high", scen)
        label(f"  {stage}")
        print(render(cfg, payload))
        print()

    # 2. Models (Opus / Sonnet / Haiku)
    section("2. Models — colour coding")
    for name, _ in MODELS:
        cfg = {
            "decoration": "emoji",
            "bar_style":  "fill",
            "metrics":    all_metrics("both"),
        }
        effort = "low" if "haiku" in name.lower() else "high"
        payload = make_input(name, effort, SCENARIOS["medium"])
        label(f"  {name}")
        print(render(cfg, payload))
        print()

    # 3. Display modes (text / bar / both)
    section("3. Display modes")
    for mode in DISPLAY_MODES:
        cfg = {
            "decoration": "emoji",
            "bar_style":  "fill",
            "metrics":    all_metrics(mode),
        }
        payload = make_input("Sonnet 4.6", "high", SCENARIOS["medium"])
        label(f"  display={mode}")
        print(render(cfg, payload))
        print()

    # 4. Decoration: emoji vs label
    section("4. Decoration — emoji vs label")
    for deco in DECORATIONS:
        cfg = {
            "decoration": deco,
            "bar_style":  "fill",
            "metrics":    all_metrics("both"),
        }
        payload = make_input("Sonnet 4.6", "high", SCENARIOS["medium"])
        label(f"  decoration={deco}")
        print(render(cfg, payload))
        print()

    # 5. Bar styles (fill / block / dot / square)
    section("5. Bar styles")
    for style in BAR_STYLES:
        cfg = {
            "decoration": "emoji",
            "bar_style":  style,
            "metrics":    all_metrics("bar"),
        }
        payload = make_input("Sonnet 4.6", "high", SCENARIOS["medium"])
        label(f"  bar_style={style}")
        print(render(cfg, payload))
        print()


def run_small() -> None:
    """Five representative variations — each with a different bar style."""
    section("1. fill — Sonnet, both mode, medium load, thinking on")
    cfg = {"decoration": "emoji", "bar_style": "fill", "metrics": all_metrics("both")}
    print(render(cfg, make_input("Sonnet 4.6", "high", SCENARIOS["medium"]), thinking=True))
    print()

    section("2. block — Opus, high load, red thresholds")
    cfg = {"decoration": "emoji", "bar_style": "block", "metrics": all_metrics("both")}
    print(render(cfg, make_input("Opus 4.7", "high", SCENARIOS["high"]), thinking=False))
    print()

    section("3. dot — bar-only, compact, thinking on")
    cfg = {"decoration": "emoji", "bar_style": "dot", "metrics": all_metrics("bar")}
    print(render(cfg, make_input("Sonnet 4.6", "medium", SCENARIOS["medium"]), thinking=True))
    print()

    section("4. square — label decoration, words instead of emojis")
    cfg = {"decoration": "label", "bar_style": "square", "metrics": all_metrics("both")}
    print(render(cfg, make_input("Opus 4.7", "high", SCENARIOS["medium"]), thinking=False))
    print()

    section("5. fill — Haiku, low load, text mode")
    cfg = {"decoration": "emoji", "bar_style": "fill", "metrics": all_metrics("text")}
    print(render(cfg, make_input("Haiku 4.5", "low", SCENARIOS["low"]), thinking=False))
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Render status line preview variations.")
    parser.add_argument("--small", action="store_true",
                        help="show only 5 representative variations")
    args = parser.parse_args()

    backup_cfg = CONFIG_PATH.read_text(encoding="utf-8") if CONFIG_PATH.exists() else None
    backup_set = SETTINGS_PATH.read_text(encoding="utf-8") if SETTINGS_PATH.exists() else None
    try:
        print(f"{BOLD}Claude Code Status Line — Preview{RESET}")
        if args.small:
            print(f"{DIM}5 representative variations.{RESET}")
            run_small()
        else:
            print(f"{DIM}Renders every relevant variation. Screenshot freely.{RESET}")
            run_full()
    finally:
        for path, backup in ((CONFIG_PATH, backup_cfg), (SETTINGS_PATH, backup_set)):
            if backup is not None:
                path.write_text(backup, encoding="utf-8")
            else:
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass


if __name__ == "__main__":
    main()
