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
STATE_PATH   = Path.home() / ".claude" / "statusline_state.json"
INSTALL_SRC  = Path(__file__).parent.parent / "scripts" / "statusline.py"
INSTALL_DEST = Path.home() / ".claude" / "statusline.py"

DISPLAY_CHOICES = ("bar", "text", "both", "off")

DEFAULTS: dict = {
    "thresholds": {
        "ctx":  {"warn": 60, "crit": 80},
        "tkn":  {"warn": 60, "crit": 80},
        "five": {"warn": 60, "crit": 80},
        "week": {"warn": 60, "crit": 80},
    },
    "line1": {},
    "decoration": "emoji",
    "bar_style": "fill",
    "metrics": {
        "model":    {"display": "text"},
        "effort":   {"display": "text"},
        "thinking": {"display": "text"},
        "ctx":      {"display": "both"},
        "tkn":      {"display": "text"},
        "five":     {"display": "both"},
        "week":     {"display": "both"},
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


MENU_ITEMS = ["Metrics visibility", "Metrics thresholds", "Git visibility", "Decoration (emoji/label)", "Bar style"]


def diff_config(original: dict, current: dict) -> list[str]:
    """Return human-readable list of changes between two configs."""
    lines: list[str] = []

    def walk(path: str, a, b) -> None:
        if isinstance(a, dict) or isinstance(b, dict):
            a = a if isinstance(a, dict) else {}
            b = b if isinstance(b, dict) else {}
            for key in sorted(set(a) | set(b)):
                walk(f"{path}.{key}" if path else key, a.get(key), b.get(key))
            return
        if a != b:
            if a is None:
                lines.append(f"+ {path} = {b!r}")
            elif b is None:
                lines.append(f"- {path}  (was {a!r})")
            else:
                lines.append(f"~ {path}: {a!r} -> {b!r}")

    walk("", original, current)
    return lines


def confirm_unsaved(stdscr: "curses.window", changes: list[str]) -> bool:
    """Show unsaved-changes dialog. Returns True = save, False = discard."""
    curses.curs_set(0)
    stdscr.keypad(True)
    selected = 0  # 0 = save, 1 = discard
    options = [("Save changes", True), ("Discard changes", False)]

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        draw_box(stdscr, "Unsaved changes")

        title = "You have unsaved changes:"
        stdscr.addstr(2, max(2, (w - len(title)) // 2), title, curses.A_BOLD)

        max_lines = max(1, h - 9)
        shown = changes[:max_lines]
        block_width = max((len(line) for line in shown), default=0)
        if len(changes) > max_lines:
            more = f"... and {len(changes) - max_lines} more"
            block_width = max(block_width, len(more))
        block_width = min(block_width, max(0, w - 4))
        x_block = max(2, (w - block_width) // 2)
        for i, line in enumerate(shown):
            stdscr.addstr(4 + i, x_block, line[: max(0, w - x_block - 2)])
        if len(changes) > max_lines:
            more = f"... and {len(changes) - max_lines} more"
            stdscr.addstr(4 + max_lines, x_block, more, curses.A_DIM)

        y_opts = h - 4
        opt_strs = [f" {label_} " for label_, _ in options]
        opts_total = sum(len(s) for s in opt_strs) + 4 * (len(opt_strs) - 1)
        x = max(2, (w - opts_total) // 2)
        for i, opt_str in enumerate(opt_strs):
            attr = curses.A_REVERSE if i == selected else curses.A_NORMAL
            stdscr.addstr(y_opts, x, opt_str, attr)
            x += len(opt_str) + 4

        hint = "[←→] choose  [Enter] confirm  [s] save  [d] discard"
        stdscr.addstr(h - 2, max(2, (w - len(hint)) // 2), hint, curses.A_DIM)
        stdscr.refresh()

        key = stdscr.getch()
        if key in (curses.KEY_LEFT, curses.KEY_UP):
            selected = (selected - 1) % len(options)
        elif key in (curses.KEY_RIGHT, curses.KEY_DOWN):
            selected = (selected + 1) % len(options)
        elif key in (ord("s"), ord("S")):
            return True
        elif key in (ord("d"), ord("D")):
            return False
        elif key in (curses.KEY_ENTER, ord("\n"), ord("\r")):
            return options[selected][1]


def draw_box(win: "curses.window", title: str) -> None:
    win.box()
    h, w = win.getmaxyx()
    label = f" {title} "
    win.addstr(0, max(2, (w - len(label)) // 2), label, curses.A_BOLD)


def main_menu(stdscr: "curses.window", config: dict, original: dict) -> tuple[dict, bool]:
    """Returns (config, save). save reflects user's choice on exit."""
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
        hint = "[↑↓] navigate  [Enter] open  [q] save & quit  [Esc] quit (asks if unsaved)"
        stdscr.addstr(h - 2, max(2, (w - len(hint)) // 2), hint, curses.A_DIM)
        stdscr.refresh()

        key = stdscr.getch()
        if key in (ord("q"), ord("Q")):
            stdscr.clear()
            draw_box(stdscr, "Claude Code Status Line — Configuration")
            msg = "Configuration saved. Restart Claude Code to apply changes."
            stdscr.addstr(h // 2, max(2, (w - len(msg)) // 2), msg)
            hint2 = "Press any key to exit"
            stdscr.addstr(h // 2 + 2, max(2, (w - len(hint2)) // 2), hint2, curses.A_DIM)
            stdscr.refresh()
            stdscr.getch()
            return config, True
        elif key == 27:  # Esc
            changes = diff_config(original, config)
            if not changes:
                return config, False
            if confirm_unsaved(stdscr, changes):
                return config, True
            return config, False
        elif key == curses.KEY_UP:
            selected = (selected - 1) % len(MENU_ITEMS)
        elif key == curses.KEY_DOWN:
            selected = (selected + 1) % len(MENU_ITEMS)
        elif key in (curses.KEY_ENTER, ord("\n"), ord("\r")):
            if selected == 0:
                config = menu_metrics(stdscr, config)
            elif selected == 1:
                config = menu_thresholds(stdscr, config)
            elif selected == 2:
                config = menu_visibility(stdscr, config, "line2", "Git visibility", [
                    ("show_dir",      "dir"),
                    ("show_branch",   "branch"),
                    ("show_worktree", "worktree"),
                ])
            elif selected == 3:
                config = menu_bar_decoration(stdscr, config)
            elif selected == 4:
                config = menu_bar_style(stdscr, config)


def menu_thresholds(stdscr: "curses.window", config: dict) -> dict:
    curses.curs_set(1)
    stdscr.keypad(True)

    rows = [
        ("ctx",  "context"),
        ("tkn",  "tokens "),
        ("five", "5h     "),
        ("week", "7d     "),
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


def menu_metrics(stdscr: "curses.window", config: dict) -> dict:
    curses.curs_set(0)
    stdscr.keypad(True)

    rows = [
        ("model",    "model   "),
        ("effort",   "effort  "),
        ("thinking", "thinking"),
        ("ctx",      "context "),
        ("tkn",      "tokens  "),
        ("five",     "5h      "),
        ("week",     "7d      "),
    ]
    metrics_cfg = config.get("metrics", {})
    state: dict[str, str] = {}
    for key, _ in rows:
        val = metrics_cfg.get(key, {}).get("display")
        if val not in DISPLAY_CHOICES:
            val = DEFAULTS["metrics"][key]["display"]
        state[key] = val

    row = 0

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        draw_box(stdscr, "Metric display")

        last = read_last_model()
        sub = f"selected model: {last}" if last else "selected model: (unknown — run Claude Code once)"
        stdscr.addstr(2, 2, sub, curses.A_DIM)

        header_y = 4
        stdscr.addstr(header_y, 2, "metric", curses.A_DIM)
        for j, choice in enumerate(DISPLAY_CHOICES):
            stdscr.addstr(header_y, 12 + j * 10, choice, curses.A_DIM)

        for i, (key, lbl) in enumerate(rows):
            y = header_y + 2 + i
            attr_row = curses.A_REVERSE if i == row else curses.A_NORMAL
            stdscr.addstr(y, 2, lbl, attr_row)
            for j, choice in enumerate(DISPLAY_CHOICES):
                mark = "(*)" if state[key] == choice else "( )"
                attr = curses.A_BOLD if state[key] == choice else curses.A_NORMAL
                if i == row and state[key] == choice:
                    attr |= curses.A_REVERSE
                stdscr.addstr(y, 12 + j * 10, mark, attr)

        hint = "[↑↓] metric  [←→] mode  [b/t/o/h] set  [Esc] back"
        stdscr.addstr(h - 2, max(2, (w - len(hint)) // 2), hint, curses.A_DIM)
        stdscr.refresh()

        key = stdscr.getch()
        if key == 27:  # Esc
            break
        elif key == curses.KEY_UP:
            row = (row - 1) % len(rows)
        elif key == curses.KEY_DOWN:
            row = (row + 1) % len(rows)
        elif key == curses.KEY_LEFT:
            cur = DISPLAY_CHOICES.index(state[rows[row][0]])
            state[rows[row][0]] = DISPLAY_CHOICES[(cur - 1) % len(DISPLAY_CHOICES)]
        elif key == curses.KEY_RIGHT:
            cur = DISPLAY_CHOICES.index(state[rows[row][0]])
            state[rows[row][0]] = DISPLAY_CHOICES[(cur + 1) % len(DISPLAY_CHOICES)]
        elif key in (ord("b"), ord("B")):
            state[rows[row][0]] = "bar"
        elif key in (ord("t"), ord("T")):
            state[rows[row][0]] = "text"
        elif key in (ord("h"), ord("H")):
            state[rows[row][0]] = "both"
        elif key in (ord("o"), ord("O")):
            state[rows[row][0]] = "off"

    config = dict(config)
    config["metrics"] = {k: {"display": state[k]} for k, _ in rows}
    return config


def read_last_model() -> str:
    try:
        if STATE_PATH.exists():
            with STATE_PATH.open(encoding="utf-8") as f:
                return str(json.load(f).get("last_model") or "")
    except Exception:
        pass
    return ""


def menu_visibility(
    stdscr: "curses.window",
    config: dict,
    section: str = "line2",
    title: str = "Line 2 Visibility",
    items: list | None = None,
    subtitle: str = "",
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

        row_offset = 2
        if subtitle:
            stdscr.addstr(2, 2, subtitle, curses.A_DIM)
            row_offset = 4

        for i, (key, lbl) in enumerate(items):
            check = "x" if state[key] else " "
            attr = curses.A_REVERSE if i == selected else curses.A_NORMAL
            stdscr.addstr(row_offset + i, 2, f"  [{check}] {lbl}", attr)

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


def menu_bar_decoration(stdscr: "curses.window", config: dict) -> dict:
    curses.curs_set(0)
    stdscr.keypad(True)

    choices = [
        ("emoji", "emoji   (🤖 💪 🧠 📦 🪙 🕔 📅)"),
        ("label", "label   (model effort thinking ctx tkn 5h 7d)"),
    ]
    current = config.get("decoration", config.get("bar_mode_decoration", DEFAULTS["decoration"]))
    if current not in ("emoji", "label"):
        current = "emoji"
    selected = 0 if current == "emoji" else 1

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        draw_box(stdscr, "Decoration")

        stdscr.addstr(2, 2, "Prefix shown in front of each segment (all display modes):", curses.A_DIM)

        for i, (_, lbl) in enumerate(choices):
            mark = "(*)" if i == selected else "( )"
            attr = curses.A_REVERSE if i == selected else curses.A_NORMAL
            stdscr.addstr(4 + i, 2, f"  {mark} {lbl}", attr)

        hint = "[↑↓] choose  [Enter/Space] select  [Esc] back"
        stdscr.addstr(h - 2, max(2, (w - len(hint)) // 2), hint, curses.A_DIM)
        stdscr.refresh()

        key = stdscr.getch()
        if key == 27:
            break
        elif key == curses.KEY_UP:
            selected = (selected - 1) % len(choices)
        elif key == curses.KEY_DOWN:
            selected = (selected + 1) % len(choices)
        elif key in (ord(" "), curses.KEY_ENTER, ord("\n"), ord("\r")):
            pass  # selection is implicit by position

    config = dict(config)
    config["decoration"] = choices[selected][0]
    config.pop("bar_mode_decoration", None)
    return config


def menu_bar_style(stdscr: "curses.window", config: dict) -> dict:
    curses.curs_set(0)
    stdscr.keypad(True)

    choices = [
        ("fill",   "fill     ▰▰▰▰▰▱▱▱▱▱   (default)"),
        ("block",  "block    █████░░░░░"),
        ("dot",    "dot      ●●●●●○○○○○"),
        ("square", "square   ■■■■■□□□□□"),
    ]
    current = config.get("bar_style", DEFAULTS["bar_style"])
    selected = next((i for i, (k, _) in enumerate(choices) if k == current), 0)

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        draw_box(stdscr, "Bar style")

        stdscr.addstr(2, 2, "Glyphs used for filled / empty bar segments:", curses.A_DIM)

        for i, (_, lbl) in enumerate(choices):
            mark = "(*)" if i == selected else "( )"
            attr = curses.A_REVERSE if i == selected else curses.A_NORMAL
            stdscr.addstr(4 + i, 2, f"  {mark} {lbl}", attr)

        hint = "[↑↓] choose  [Enter/Space] select  [Esc] back"
        stdscr.addstr(h - 2, max(2, (w - len(hint)) // 2), hint, curses.A_DIM)
        stdscr.refresh()

        key = stdscr.getch()
        if key == 27:
            break
        elif key == curses.KEY_UP:
            selected = (selected - 1) % len(choices)
        elif key == curses.KEY_DOWN:
            selected = (selected + 1) % len(choices)
        elif key in (ord(" "), curses.KEY_ENTER, ord("\n"), ord("\r")):
            pass

    config = dict(config)
    config["bar_style"] = choices[selected][0]
    return config


_save_result: bool = False


def run(stdscr: "curses.window") -> None:
    global _save_result
    raw = load_config()
    raw.pop("bar_mode_decoration", None)
    config = deep_merge(DEFAULTS, raw)
    original = json.loads(json.dumps(config))
    config, _save_result = main_menu(stdscr, config, original)
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
