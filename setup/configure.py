#!/usr/bin/env python3
"""Interactive configuration TUI for the Claude Code status line.

Requires: curses (stdlib on Linux/macOS)
          windows-curses (pip install windows-curses) on Windows
"""
from __future__ import annotations

import curses
import json
import shutil
from pathlib import Path

CONFIG_PATH  = Path.home() / ".claude" / "statusline_config.json"
INSTALL_SRC  = Path(__file__).parent.parent / "scripts" / "statusline.py"
INSTALL_DEST = Path.home() / ".claude" / "statusline.py"

DEFAULTS: dict = {
    "thresholds": {
        "ctx":  {"warn": 60, "crit": 80},
        "tkn":  {"warn": 60, "crit": 80},
        "five": {"warn": 60, "crit": 80},
        "week": {"warn": 60, "crit": 80},
    },
    "line1": {
        "show_model":    True,
        "show_effort":   True,
        "show_thinking": True,
        "show_ctx":      True,
        "show_tkn":      True,
        "show_five":     True,
        "show_week":     True,
    },
    "line2": {
        "show_dir":      True,
        "show_branch":   True,
        "show_worktree": True,
    },
}


def load_config() -> dict:
    try:
        if CONFIG_PATH.exists():
            with CONFIG_PATH.open(encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def save_config(config: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
        f.write("\n")


def deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = v
    return result


MENU_ITEMS = ["Thresholds", "Line 1 visibility", "Line 2 visibility"]


def draw_box(win: "curses.window", title: str) -> None:
    win.box()
    h, w = win.getmaxyx()
    label = f" {title} "
    win.addstr(0, max(2, (w - len(label)) // 2), label, curses.A_BOLD)


def main_menu(stdscr: "curses.window", config: dict) -> tuple[dict, bool]:
    """Returns (config, save). save=False when user pressed Esc."""
    curses.curs_set(0)
    stdscr.keypad(True)
    selected = 0

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        draw_box(stdscr, "Claude Code Status Line — Configuration")

        for i, item in enumerate(MENU_ITEMS):
            prefix = "> " if i == selected else "  "
            attr = curses.A_REVERSE if i == selected else curses.A_NORMAL
            stdscr.addstr(2 + i, 2, f"{prefix}{i + 1}. {item}", attr)

        config_info = f"config: {CONFIG_PATH}"
        stdscr.addstr(h - 4, max(2, (w - len(config_info)) // 2), config_info, curses.A_DIM)
        hint = "[↑↓] navigate  [Enter] open  [q] save & quit  [Esc] quit without saving"
        stdscr.addstr(h - 2, max(2, (w - len(hint)) // 2), hint, curses.A_DIM)
        stdscr.refresh()

        key = stdscr.getch()
        if key in (ord("q"), ord("Q")):
            return config, True
        elif key == 27:  # Esc
            return config, False
        elif key == curses.KEY_UP:
            selected = (selected - 1) % len(MENU_ITEMS)
        elif key == curses.KEY_DOWN:
            selected = (selected + 1) % len(MENU_ITEMS)
        elif key in (curses.KEY_ENTER, ord("\n"), ord("\r")):
            if selected == 0:
                config = menu_thresholds(stdscr, config)
            elif selected == 1:
                config = menu_visibility(stdscr, config, "line1", "Line 1 Visibility", [
                    ("show_model",    "model"),
                    ("show_effort",   "effort"),
                    ("show_thinking", "thinking"),
                    ("show_ctx",      "ctx"),
                    ("show_tkn",      "tkn"),
                    ("show_five",     "5h"),
                    ("show_week",     "7d"),
                ])
            elif selected == 2:
                config = menu_visibility(stdscr, config)


def menu_thresholds(stdscr: "curses.window", config: dict) -> dict:
    curses.curs_set(1)
    stdscr.keypad(True)

    rows = [
        ("ctx",  "ctx "),
        ("tkn",  "tkn "),
        ("five", "5h  "),
        ("week", "7d  "),
    ]
    fields = ["warn", "crit"]

    t = config.get("thresholds", {})
    values: dict[str, dict[str, str]] = {}
    for key, _ in rows:
        d = DEFAULTS["thresholds"][key]
        values[key] = {
            "warn": str(t.get(key, {}).get("warn", d["warn"])),
            "crit": str(t.get(key, {}).get("crit", d["crit"])),
        }

    row, col = 0, 0

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        draw_box(stdscr, "Thresholds")

        for i, (key, lbl) in enumerate(rows):
            y = 2 + i
            stdscr.addstr(y, 2, lbl)
            for j, field in enumerate(fields):
                x = 10 + j * 18
                val = values[key][field]
                attr = curses.A_REVERSE if (i == row and j == col) else curses.A_NORMAL
                stdscr.addstr(y, x, f"{field}: [{val:>3}]%", attr)

        hint = "[↑↓] rows  [←→] fields  [0-9] edit  [Backspace] clear  [Esc] back"
        stdscr.addstr(h - 2, max(2, (w - len(hint)) // 2), hint, curses.A_DIM)

        key_r, key_c = rows[row][0], fields[col]
        val = values[key_r][key_c]
        stdscr.move(2 + row, 10 + col * 18 + len(f"{fields[col]}: [") + len(val))
        stdscr.refresh()

        key = stdscr.getch()

        if key == 27:  # Esc
            break
        elif key == curses.KEY_UP:
            row = (row - 1) % len(rows)
        elif key == curses.KEY_DOWN:
            row = (row + 1) % len(rows)
        elif key == curses.KEY_LEFT:
            col = (col - 1) % len(fields)
        elif key == curses.KEY_RIGHT:
            col = (col + 1) % len(fields)
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            values[key_r][key_c] = values[key_r][key_c][:-1]
        elif ord("0") <= key <= ord("9"):
            if len(val) < 3:
                values[key_r][key_c] = val + chr(key)

    new_thresholds = dict(config.get("thresholds", {}))
    for key, _ in rows:
        try:
            w_val = int(values[key]["warn"] or "0")
            c_val = int(values[key]["crit"] or "0")
        except ValueError:
            continue
        w_val = max(0, min(100, w_val))
        c_val = max(0, min(100, c_val))
        if w_val >= c_val:
            c_val = min(100, w_val + 1)
        new_thresholds[key] = {"warn": w_val, "crit": c_val}

    config = dict(config)
    config["thresholds"] = new_thresholds
    return config


def menu_visibility(
    stdscr: "curses.window",
    config: dict,
    section: str = "line2",
    title: str = "Line 2 Visibility",
    items: list | None = None,
) -> dict:
    if items is None:
        items = [
            ("show_dir",      "dir"),
            ("show_branch",   "branch"),
            ("show_worktree", "worktree"),
        ]
    curses.curs_set(0)
    stdscr.keypad(True)

    sec = config.get(section, {})
    state: dict[str, bool] = {
        k: bool(sec.get(k, DEFAULTS[section][k])) for k, _ in items
    }
    selected = 0

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        draw_box(stdscr, title)

        for i, (key, lbl) in enumerate(items):
            check = "x" if state[key] else " "
            attr = curses.A_REVERSE if i == selected else curses.A_NORMAL
            stdscr.addstr(2 + i, 2, f"  [{check}] {lbl}", attr)

        hint = "[↑↓] navigate  [Space/Enter] toggle  [Esc] back"
        stdscr.addstr(h - 2, max(2, (w - len(hint)) // 2), hint, curses.A_DIM)
        stdscr.refresh()

        key = stdscr.getch()
        if key == 27:  # Esc
            break
        elif key == curses.KEY_UP:
            selected = (selected - 1) % len(items)
        elif key == curses.KEY_DOWN:
            selected = (selected + 1) % len(items)
        elif key in (ord(" "), curses.KEY_ENTER, ord("\n"), ord("\r")):
            k = items[selected][0]
            state[k] = not state[k]

    config = dict(config)
    config[section] = {k: state[k] for k, _ in items}
    return config


_save_result: bool = False


def run(stdscr: "curses.window") -> None:
    global _save_result
    config = deep_merge(DEFAULTS, load_config())
    config, _save_result = main_menu(stdscr, config)
    if _save_result:
        save_config(config)


def refresh_install() -> bool:
    """Copy statusline.py from repo to ~/.claude/. Returns True on success."""
    if not INSTALL_SRC.exists():
        return False
    try:
        shutil.copy2(INSTALL_SRC, INSTALL_DEST)
        return True
    except OSError:
        return False


if __name__ == "__main__":
    try:
        import curses as _check  # noqa: F401
    except ImportError:
        print("ERROR: curses not available. On Windows: pip install windows-curses")
        raise SystemExit(1)
    curses.wrapper(run)
    if _save_result:
        refreshed = refresh_install()
        if refreshed:
            print("Configuration saved. statusline.py updated — restart Claude Code to apply.")
        else:
            print("Configuration saved. Restart Claude Code to apply.")
    else:
        print("Quit without saving.")
