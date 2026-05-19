#!/usr/bin/env python3
"""Merge or remove the statusLine entry in ~/.claude/settings.json.

Used by install.cmd / install.sh and uninstall.cmd / uninstall.sh.
A timestamped backup is always written when an existing file is modified.

Usage:
    python  _install_helper.py install
    python  _install_helper.py uninstall
    python3 _install_helper.py install
    python3 _install_helper.py uninstall
"""
from __future__ import annotations

import json
import platform
import shutil
import sys
import time
from pathlib import Path


CLAUDE_DIR = Path.home() / ".claude"
SETTINGS = CLAUDE_DIR / "settings.json"
SCRIPT = CLAUDE_DIR / "statusline.py"


def status_line_command() -> str:
    if platform.system() == "Windows":
        # Forward slashes: Git Bash treats backslashes as escapes.
        script_posix = str(SCRIPT).replace("\\", "/")
        return f"python {script_posix}"
    return f"python3 {SCRIPT}"


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
        print("usage: python _install_helper.py {install|uninstall}", file=sys.stderr)
        return 2
    if sys.argv[1] == "install":
        cmd_install()
    else:
        cmd_uninstall()
    return 0


if __name__ == "__main__":
    sys.exit(main())
