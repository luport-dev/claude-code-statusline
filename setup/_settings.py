#!/usr/bin/env python3
"""Merge or remove the statusLine entry in %USERPROFILE%\\.claude\\settings.json.

Used by install.cmd and uninstall.cmd. A timestamped backup is always written
when an existing file is modified.

Usage:
    python _settings.py install
    python _settings.py uninstall
"""
from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path


CLAUDE_DIR = Path.home() / ".claude"
SETTINGS = CLAUDE_DIR / "settings.json"
SCRIPT = CLAUDE_DIR / "statusline.py"


def status_line_command() -> str:
    # Forward slashes: Git Bash (the shell Claude Code routes through on
    # Windows when present) treats backslashes as escapes and will eat them.
    # See https://code.claude.com/docs/en/statusline#windows-configuration
    script_posix = str(SCRIPT).replace("\\", "/")
    return f"python {script_posix}"


def load_settings() -> dict:
    if not SETTINGS.exists():
        return {}
    try:
        with SETTINGS.open(encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def write_settings(data: dict) -> None:
    if SETTINGS.exists():
        backup = SETTINGS.with_suffix(SETTINGS.suffix + f".bak.{int(time.time())}")
        shutil.copy2(SETTINGS, backup)
        print(f"   backup:  {backup}")
    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
    with SETTINGS.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"   updated: {SETTINGS}")


def cmd_install() -> None:
    data = load_settings()
    data["statusLine"] = {"type": "command", "command": status_line_command()}
    write_settings(data)


def cmd_uninstall() -> None:
    data = load_settings()
    if "statusLine" in data:
        del data["statusLine"]
        write_settings(data)
    else:
        print(f"   skipped: {SETTINGS} (no statusLine entry)")


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in ("install", "uninstall"):
        print("usage: python _settings.py {install|uninstall}", file=sys.stderr)
        return 2
    if sys.argv[1] == "install":
        cmd_install()
    else:
        cmd_uninstall()
    return 0


if __name__ == "__main__":
    sys.exit(main())
