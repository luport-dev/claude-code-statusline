#!/usr/bin/env python3
"""Interactive configuration TUI for the Claude Code status line.

Requires: curses (stdlib on Linux/macOS)
          windows-curses (pip install windows-curses) on Windows
"""
from __future__ import annotations

import curses
import json
import platform
import shutil
import time
from pathlib import Path

CONFIG_PATH   = Path.home() / ".claude" / "statusline_config.json"
STATE_PATH    = Path.home() / ".claude" / "statusline_state.json"
SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
INSTALL_DEST  = Path.home() / ".claude" / "statusline.py"
UPDATE_CACHE  = Path.home() / ".claude" / "statusline_update.json"

UPDATE_CHOICES = ("never", "daily", "weekly", "monthly")


def _find_install_src() -> Path:
    """Findet statusline.py: erst im Repo (../scripts/), dann neben settings.py (npm payload)."""
    here = Path(__file__).resolve().parent
    repo_src = here.parent / "scripts" / "statusline.py"
    if repo_src.exists():
        return repo_src
    return here / "statusline.py"


INSTALL_SRC = _find_install_src()

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
    "bar_style": "dot",
    "metrics": {
        "model":    {"display": "text"},
        "effort":   {"display": "bar"},
        "thinking": {"display": "text"},
        "ctx":      {"display": "bar"},
        "tkn":      {"display": "text"},
        "five":     {"display": "bar"},
        "week":     {"display": "bar"},
    },
    "line2": {
        "show_dir":      True,
        "show_branch":   True,
        "show_worktree": True,
    },
    "updates": {
        "check": "weekly",
    },
}


def _read_package_version() -> str:
    """Locate package.json shipped with the repo/payload and return its version."""
    here = Path(__file__).resolve().parent
    for candidate in (
        here.parent / "npm" / "package.json",
        here / "package.json",
        here.parent / "package.json",
    ):
        try:
            if candidate.exists():
                with candidate.open(encoding="utf-8") as f:
                    return str(json.load(f).get("version") or "0.1.1")
        except Exception:
            continue
    return "0.1.1"


def write_update_cache_version() -> None:
    """Seed/refresh the update cache's current_version on install."""
    try:
        data: dict = {}
        if UPDATE_CACHE.exists():
            try:
                with UPDATE_CACHE.open(encoding="utf-8") as f:
                    data = json.load(f) or {}
            except Exception:
                data = {}
        data["current_version"] = _read_package_version()
        UPDATE_CACHE.parent.mkdir(parents=True, exist_ok=True)
        with UPDATE_CACHE.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
    except OSError:
        pass


def load_update_cache() -> dict:
    try:
        if UPDATE_CACHE.exists():
            with UPDATE_CACHE.open(encoding="utf-8") as f:
                d = json.load(f)
            return d if isinstance(d, dict) else {}
    except Exception:
        pass
    return {}


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


def _status_line_command() -> str:
    if platform.system() == "Windows":
        return f"python {str(INSTALL_DEST).replace(chr(92), '/')}"
    return f"python3 {INSTALL_DEST}"


def is_installed() -> bool:
    try:
        if not SETTINGS_PATH.exists():
            return False
        with SETTINGS_PATH.open(encoding="utf-8") as f:
            data = json.load(f)
        return "statusLine" in data
    except Exception:
        return False


def do_install() -> str:
    try:
        shutil.copy2(INSTALL_SRC, INSTALL_DEST)
        data: dict = {}
        if SETTINGS_PATH.exists():
            try:
                with SETTINGS_PATH.open(encoding="utf-8") as f:
                    data = json.load(f) or {}
            except Exception:
                data = {}
        data["statusLine"] = {"type": "command", "command": _status_line_command()}
        if SETTINGS_PATH.exists():
            backup = SETTINGS_PATH.with_name(f"{SETTINGS_PATH.name}.bak.{int(time.time())}")
            shutil.copy2(SETTINGS_PATH, backup)
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with SETTINGS_PATH.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        write_update_cache_version()
        return "Installed. Restart Claude Code to activate."
    except Exception as e:
        return f"Error: {e}"


def do_uninstall() -> str:
    try:
        if not SETTINGS_PATH.exists():
            return "Not installed."
        with SETTINGS_PATH.open(encoding="utf-8") as f:
            data = json.load(f) or {}
        if "statusLine" not in data:
            return "Not installed."
        del data["statusLine"]
        backup = SETTINGS_PATH.with_name(f"{SETTINGS_PATH.name}.bak.{int(time.time())}")
        shutil.copy2(SETTINGS_PATH, backup)
        with SETTINGS_PATH.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        return "Uninstalled. Restart Claude Code to deactivate."
    except Exception as e:
        return f"Error: {e}"


MENU_ITEMS = [
    ("Metrics visibility",       "👀"),
    ("Metrics thresholds",       "🚦"),
    ("Git visibility",           "🌳"),
    ("Decoration (symbols/label)", "🎨"),
    ("Bar style",                "📊"),
    ("Update checks",            "♻️"),
]


# --- styled drawing helpers ------------------------------------------------

# Color pair slots — initialised in run() after curses.start_color().
CP_TITLE   = 1
CP_BORDER  = 2
CP_DIM     = 3
CP_ACCENT  = 4   # active menu pointer / selected option
CP_VALUE   = 5   # values, numbers
CP_OK      = 6
CP_WARN    = 7
CP_DANGER  = 8


def _attr(pair: int, bold: bool = False) -> int:
    a = curses.color_pair(pair)
    if bold:
        a |= curses.A_BOLD
    return a


def init_colors() -> None:
    try:
        curses.start_color()
        curses.use_default_colors()
    except curses.error:
        return
    if not curses.has_colors():
        return
    has256 = curses.COLORS >= 256

    def pair(idx: int, fg256: int, fg8: int) -> None:
        try:
            curses.init_pair(idx, fg256 if has256 else fg8, -1)
        except curses.error:
            pass

    pair(CP_TITLE,  81,  curses.COLOR_CYAN)
    pair(CP_BORDER, 245, curses.COLOR_WHITE)
    pair(CP_DIM,    245, curses.COLOR_WHITE)
    pair(CP_ACCENT, 213, curses.COLOR_MAGENTA)
    pair(CP_VALUE,  172, curses.COLOR_YELLOW)
    pair(CP_OK,     82,  curses.COLOR_GREEN)
    pair(CP_WARN,   220, curses.COLOR_YELLOW)
    pair(CP_DANGER, 203, curses.COLOR_RED)


def safe_addstr(win, y: int, x: int, text: str, attr: int = 0) -> None:
    """addstr that swallows out-of-bounds errors at the bottom-right corner."""
    try:
        win.addstr(y, x, text, attr)
    except curses.error:
        pass


def draw_rounded_box(win) -> None:
    h, w = win.getmaxyx()
    border = _attr(CP_BORDER)
    top    = "╭" + "─" * (w - 2) + "╮"
    bot    = "╰" + "─" * (w - 2) + "╯"
    safe_addstr(win, 0, 0, top, border)
    safe_addstr(win, h - 1, 0, bot, border)
    for y in range(1, h - 1):
        safe_addstr(win, y, 0,     "│", border)
        safe_addstr(win, y, w - 1, "│", border)


def draw_box(win, title: str) -> None:
    """Rounded box with centered, accented title strip."""
    draw_rounded_box(win)
    h, w = win.getmaxyx()
    label = f" * {title} "
    x = max(2, (w - len(label)) // 2)
    safe_addstr(win, 0, x, label, _attr(CP_TITLE, bold=True))


def draw_divider(win, y: int) -> None:
    h, w = win.getmaxyx()
    safe_addstr(win, y, 2, "─" * max(0, w - 4), _attr(CP_BORDER))


def draw_hint_pills(win, y: int, pills: list[tuple[str, str]]) -> None:
    """Render a centred ' key  action │ key  action │ … ' footer."""
    h, w = win.getmaxyx()
    sep = "  │  "
    parts = [f"{k} {v}" for k, v in pills]
    total = sum(len(p) for p in parts) + len(sep) * (len(parts) - 1)
    if total > w - 4:
        # Compact fallback
        text = "  ".join(f"[{k}] {v}" for k, v in pills)
        safe_addstr(win, y, max(2, (w - len(text)) // 2), text[: w - 4], _attr(CP_DIM))
        return
    x = max(2, (w - total) // 2)
    for i, (k, v) in enumerate(parts and pills):
        safe_addstr(win, y, x, k, _attr(CP_ACCENT, bold=True))
        x += len(k) + 1
        safe_addstr(win, y, x, v, _attr(CP_DIM))
        x += len(v)
        if i < len(pills) - 1:
            safe_addstr(win, y, x, sep, _attr(CP_BORDER))
            x += len(sep)


def emoji_safe(emoji: str) -> str:
    """Ensure narrow emojis have a trailing space so columns don't collide."""
    narrow = set()
    return emoji if emoji.endswith(" ") or emoji in narrow else emoji + " "


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

        title = "!  You have unsaved changes"
        safe_addstr(stdscr, 2, max(2, (w - len(title)) // 2), title, _attr(CP_WARN, bold=True))

        max_lines = max(1, h - 9)
        shown = changes[:max_lines]
        block_width = max((len(line) for line in shown), default=0)
        if len(changes) > max_lines:
            more = f"… and {len(changes) - max_lines} more"
            block_width = max(block_width, len(more))
        block_width = min(block_width, max(0, w - 4))
        x_block = max(2, (w - block_width) // 2)

        def diff_attr(line: str) -> int:
            if line.startswith("+"): return _attr(CP_OK)
            if line.startswith("-"): return _attr(CP_DANGER)
            if line.startswith("~"): return _attr(CP_VALUE)
            return 0

        for i, line in enumerate(shown):
            safe_addstr(stdscr, 4 + i, x_block, line[: max(0, w - x_block - 2)], diff_attr(line))
        if len(changes) > max_lines:
            more = f"… and {len(changes) - max_lines} more"
            safe_addstr(stdscr, 4 + max_lines, x_block, more, _attr(CP_DIM))

        y_opts = h - 4
        opt_strs = []
        for i, (label_, _) in enumerate(options):
            marker = "> " if i == selected else "  "
            opt_strs.append(f"{marker}{label_}{'  '}")
        opts_total = sum(len(s) for s in opt_strs) + 4 * (len(opt_strs) - 1)
        x = max(2, (w - opts_total) // 2)
        for i, opt_str in enumerate(opt_strs):
            if i == selected:
                attr = _attr(CP_OK if options[i][1] else CP_DANGER, bold=True)
            else:
                attr = _attr(CP_DIM)
            safe_addstr(stdscr, y_opts, x, opt_str, attr)
            x += len(opt_str) + 4

        draw_hint_pills(stdscr, h - 2, [
            ("←→",  "choose"),
            ("Ent", "confirm"),
            ("s",   "save"),
            ("d",   "discard"),
        ])
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


def show_flash(stdscr: "curses.window", msg: str, attr: int) -> None:
    """Zeigt eine kurze Statusmeldung und wartet auf Tastendruck."""
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    draw_box(stdscr, "Claude Code Status Line — Settings")
    safe_addstr(stdscr, h // 2,     max(2, (w - len(msg)) // 2), msg, attr)
    hint = "Press any key to continue"
    safe_addstr(stdscr, h // 2 + 2, max(2, (w - len(hint)) // 2), hint, _attr(CP_DIM))
    stdscr.refresh()
    stdscr.getch()


def main_menu(stdscr: "curses.window", config: dict, original: dict) -> tuple[dict, bool]:
    """Returns (config, save). save reflects user's choice on exit."""
    curses.curs_set(0)
    stdscr.keypad(True)
    selected = 0
    # Gesamtanzahl Einträge = MENU_ITEMS + 1 Toggle-Eintrag
    total = len(MENU_ITEMS) + 1
    TOGGLE_IDX = len(MENU_ITEMS)

    while True:
        installed = is_installed()
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        draw_box(stdscr, "Claude Code Status Line — Settings")

        for i, (item, emo) in enumerate(MENU_ITEMS):
            y = 3 + i * 2
            pointer = ">" if i == selected else " "
            safe_addstr(stdscr, y, 3, pointer, _attr(CP_ACCENT, bold=True))
            safe_addstr(stdscr, y, 6, emo)
            label_attr = _attr(CP_ACCENT, bold=True) if i == selected else 0
            safe_addstr(stdscr, y, 11, item, label_attr)

        # Toggle-Eintrag
        toggle_y = 3 + TOGGLE_IDX * 2
        toggle_label = "Uninstall" if installed else "Install"
        toggle_emo   = "📤" if installed else "📥"
        toggle_attr  = _attr(CP_DANGER if installed else CP_OK, bold=(selected == TOGGLE_IDX))
        pointer = ">" if selected == TOGGLE_IDX else " "
        safe_addstr(stdscr, toggle_y, 3, pointer, _attr(CP_ACCENT, bold=True))
        safe_addstr(stdscr, toggle_y, 6, toggle_emo, toggle_attr)
        safe_addstr(stdscr, toggle_y, 11, toggle_label, toggle_attr)

        cache = load_update_cache()
        hint_text = ""
        if cache.get("update_available") and cache.get("latest_version"):
            tag = str(cache["latest_version"])
            if not tag.startswith(("v", "V")):
                tag = f"v{tag}"
            hint_text = f"🔔  Update available: {tag}"

        draw_divider(stdscr, h - 5)
        if hint_text:
            safe_addstr(stdscr, h - 4, max(2, (w - len(hint_text)) // 2), hint_text, _attr(CP_WARN, bold=True))
            path_text = f"{CONFIG_PATH}"
            safe_addstr(stdscr, h - 3, max(2, (w - len(path_text)) // 2), path_text, _attr(CP_DIM))
        else:
            path_text = f"{CONFIG_PATH}"
            safe_addstr(stdscr, h - 4, max(2, (w - len(path_text)) // 2), path_text, _attr(CP_DIM))

        draw_hint_pills(stdscr, h - 2, [
            ("↑↓",  "navigate"),
            ("Ent", "open"),
            ("q",   "save & quit"),
            ("esc", "quit"),
        ])
        stdscr.refresh()

        key = stdscr.getch()
        if key in (ord("q"), ord("Q")):
            stdscr.clear()
            draw_box(stdscr, "Claude Code Status Line — Settings")
            msg = "+ Configuration saved."
            sub = "Restart Claude Code to apply changes."
            safe_addstr(stdscr, h // 2,     max(2, (w - len(msg)) // 2), msg, _attr(CP_OK, bold=True))
            safe_addstr(stdscr, h // 2 + 1, max(2, (w - len(sub)) // 2), sub, _attr(CP_DIM))
            hint2 = "Press any key to exit"
            safe_addstr(stdscr, h // 2 + 3, max(2, (w - len(hint2)) // 2), hint2, _attr(CP_DIM))
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
            selected = (selected - 1) % total
        elif key == curses.KEY_DOWN:
            selected = (selected + 1) % total
        elif key in (curses.KEY_ENTER, ord("\n"), ord("\r")):
            if selected == 0:
                config = menu_metrics(stdscr, config)
            elif selected == 1:
                config = menu_thresholds(stdscr, config)
            elif selected == 2:
                config = menu_visibility(stdscr, config, "line2", "Git visibility", [
                    ("show_dir",      "dir",      "📁"),
                    ("show_branch",   "branch",   "🌿"),
                    ("show_worktree", "worktree", "🌳"),
                ])
            elif selected == 3:
                config = menu_bar_decoration(stdscr, config)
            elif selected == 4:
                config = menu_bar_style(stdscr, config)
            elif selected == 5:
                config = menu_updates(stdscr, config)
            elif selected == TOGGLE_IDX:
                if installed:
                    result = do_uninstall()
                    show_flash(stdscr, result, _attr(CP_WARN, bold=True))
                else:
                    result = do_install()
                    show_flash(stdscr, result, _attr(CP_OK, bold=True))


def menu_thresholds(stdscr: "curses.window", config: dict) -> dict:
    curses.curs_set(0)
    stdscr.keypad(True)

    rows = [
        ("ctx",  "context", "📦"),
        ("tkn",  "tokens",  "🎫"),
        ("five", "5h",      "🕔"),
        ("week", "7d",      "📆"),
    ]
    fields = ["warn", "crit"]
    field_labels = {"warn": "warn", "crit": "critical"}

    t = config.get("thresholds", {})
    values: dict[str, dict[str, int]] = {}
    for key, _, _ in rows:
        d = DEFAULTS["thresholds"][key]
        try:
            wv = int(t.get(key, {}).get("warn", d["warn"]))
        except (TypeError, ValueError):
            wv = d["warn"]
        try:
            cv = int(t.get(key, {}).get("crit", d["crit"]))
        except (TypeError, ValueError):
            cv = d["crit"]
        values[key] = {"warn": wv, "crit": cv}

    digit_buffer = ""  # for multi-digit numeric entry

    def clamp(key: str) -> None:
        """Clamp warn/crit to 0..100 and enforce warn < crit."""
        v = values[key]
        v["warn"] = max(0, min(100, v["warn"]))
        v["crit"] = max(0, min(100, v["crit"]))
        if v["warn"] >= v["crit"]:
            # The field the user just edited wins; the other is pushed.
            v["crit"] = min(100, v["warn"] + 1)
            if v["crit"] == v["warn"]:
                v["warn"] = max(0, v["crit"] - 1)

    def set_value(key: str, field: str, new_val: int) -> None:
        v = values[key]
        v[field] = max(0, min(100, new_val))
        # Enforce warn < crit by pushing the *other* field, not the edited one.
        if v["warn"] >= v["crit"]:
            if field == "warn":
                v["crit"] = min(100, v["warn"] + 1)
                if v["crit"] <= v["warn"]:
                    v["warn"] = max(0, v["crit"] - 1)
            else:
                v["warn"] = max(0, v["crit"] - 1)

    row, col = 0, 0

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        draw_box(stdscr, "Metrics thresholds")

        subtitle = "Color thresholds — warn (yellow) and crit (red), 0..100, warn < crit"
        safe_addstr(stdscr, 2, max(2, (w - len(subtitle)) // 2), subtitle, _attr(CP_DIM))

        y_base = 4
        for i, (key, lbl, emo) in enumerate(rows):
            y = y_base + i
            row_active = (i == row)
            safe_addstr(stdscr, y, 4, emo + " ")
            safe_addstr(stdscr, y, 9, lbl, _attr(CP_ACCENT, bold=True) if row_active else 0)
            warn_x = 18
            crit_x = 36
            for j, field in enumerate(fields):
                x = warn_x if field == "warn" else crit_x
                val = values[key][field]
                cell_active = row_active and (j == col)
                field_color = CP_WARN if field == "warn" else CP_DANGER
                field_emo = "🟡" if field == "warn" else "🔴"
                flabel = field_labels[field]
                safe_addstr(stdscr, y, x, field_emo + " ")
                safe_addstr(stdscr, y, x + 3, f"{flabel}:", _attr(field_color, bold=True))
                bracket = ">" if cell_active else " "
                safe_addstr(stdscr, y, x + 3 + len(flabel) + 2, bracket, _attr(CP_ACCENT, bold=True))
                box_attr = _attr(CP_VALUE, bold=True) if cell_active else _attr(CP_VALUE)
                shown = f"{val:>3}%"
                if cell_active and digit_buffer:
                    shown = f"{int(digit_buffer):>3}%"
                safe_addstr(stdscr, y, x + 3 + len(flabel) + 3, shown, box_attr)

        draw_hint_pills(stdscr, h - 2, [
            ("↑↓",    "row"),
            ("←→",    "field"),
            ("+/-",   "±1"),
            ("PgUp/Dn", "±5"),
            ("0-9",   "type"),
            ("esc",   "back"),
        ])

        key_r, key_c = rows[row][0], fields[col]
        stdscr.refresh()

        key = stdscr.getch()

        # Any non-digit action commits the in-flight digit buffer.
        def commit_buffer() -> None:
            nonlocal digit_buffer
            if digit_buffer:
                try:
                    set_value(key_r, key_c, int(digit_buffer))
                except ValueError:
                    pass
                digit_buffer = ""

        if key == 27:  # Esc
            commit_buffer()
            break
        elif key == curses.KEY_UP:
            commit_buffer()
            row = (row - 1) % len(rows)
        elif key == curses.KEY_DOWN:
            commit_buffer()
            row = (row + 1) % len(rows)
        elif key == curses.KEY_LEFT:
            commit_buffer()
            col = (col - 1) % len(fields)
        elif key == curses.KEY_RIGHT:
            commit_buffer()
            col = (col + 1) % len(fields)
        elif key in (ord("+"), ord("=")):
            commit_buffer()
            set_value(key_r, key_c, values[key_r][key_c] + 1)
        elif key in (ord("-"), ord("_")):
            commit_buffer()
            set_value(key_r, key_c, values[key_r][key_c] - 1)
        elif key == curses.KEY_PPAGE:  # PageUp
            commit_buffer()
            set_value(key_r, key_c, values[key_r][key_c] + 5)
        elif key == curses.KEY_NPAGE:  # PageDown
            commit_buffer()
            set_value(key_r, key_c, values[key_r][key_c] - 5)
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            if digit_buffer:
                digit_buffer = digit_buffer[:-1]
            else:
                set_value(key_r, key_c, 0)
        elif key in (curses.KEY_ENTER, ord("\n"), ord("\r")):
            commit_buffer()
        elif ord("0") <= key <= ord("9"):
            if len(digit_buffer) < 3:
                digit_buffer += chr(key)
                # Live-preview the typed number, but don't commit yet.
                try:
                    candidate = int(digit_buffer)
                    if candidate <= 100:
                        set_value(key_r, key_c, candidate)
                    else:
                        # Overflow — reset buffer to last typed digit.
                        digit_buffer = chr(key)
                        set_value(key_r, key_c, int(digit_buffer))
                except ValueError:
                    digit_buffer = ""

    new_thresholds = dict(config.get("thresholds", {}))
    for key, _, _ in rows:
        clamp(key)
        new_thresholds[key] = {"warn": values[key]["warn"], "crit": values[key]["crit"]}

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

    # Matches the emojis used in the rendered status line itself.
    metric_glyph = {
        "model":    "🤖",
        "effort":   "💪",
        "thinking": "🧠",
        "ctx":      "📦",
        "tkn":      "🎫",
        "five":     "🕔",
        "week":     "📆",
    }

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        draw_box(stdscr, "Metrics visibility")

        last = read_last_model()
        sub = f"selected model: {last}" if last else "selected model: (unknown — run Claude Code once)"
        safe_addstr(stdscr, 2, max(2, (w - len(sub)) // 2), sub, _attr(CP_DIM))

        header_y = 4
        safe_addstr(stdscr, header_y, 4, "metric", _attr(CP_DIM, bold=True))
        for j, choice in enumerate(DISPLAY_CHOICES):
            safe_addstr(stdscr, header_y, 18 + j * 10, choice, _attr(CP_DIM, bold=True))

        for i, (key, lbl) in enumerate(rows):
            y = header_y + 2 + i
            row_active = (i == row)
            pointer = ">" if row_active else " "
            safe_addstr(stdscr, y, 2, pointer, _attr(CP_ACCENT, bold=True))
            safe_addstr(stdscr, y, 4, metric_glyph.get(key, "?") + " ")
            lbl_attr = _attr(CP_ACCENT, bold=True) if row_active else 0
            safe_addstr(stdscr, y, 9, lbl.strip(), lbl_attr)
            for j, choice in enumerate(DISPLAY_CHOICES):
                selected_mark = state[key] == choice
                if selected_mark:
                    mark = "(*)"
                    attr = _attr(CP_OK, bold=True)
                else:
                    mark = "( )"
                    attr = _attr(CP_DIM)
                safe_addstr(stdscr, y, 18 + j * 10, mark, attr)

        draw_hint_pills(stdscr, h - 2, [
            ("↑↓",      "metric"),
            ("←→",      "mode"),
            ("b/t/h/o", "set"),
            ("esc",     "back"),
        ])
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
                d = json.load(f)
            # Neues Format: last_data.model.display_name
            model = (d.get("last_data") or {}).get("model", {}).get("display_name")
            if model:
                return str(model)
            # Altes Format: last_model (Fallback)
            return str(d.get("last_model") or "")
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
            ("show_dir",      "dir",      "📁"),
            ("show_branch",   "branch",   "🌿"),
            ("show_worktree", "worktree", "🌳"),
        ]
    # Normalize: items may be (key, lbl) or (key, lbl, emoji)
    norm_items = [(it + ("",)) if len(it) == 2 else it for it in items]

    curses.curs_set(0)
    stdscr.keypad(True)

    sec = config.get(section, {})
    state: dict[str, bool] = {
        k: bool(sec.get(k, DEFAULTS[section][k])) for k, _, _ in norm_items
    }
    selected = 0

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        draw_box(stdscr, title)

        row_offset = 2
        if subtitle:
            safe_addstr(stdscr, 2, max(2, (w - len(subtitle)) // 2), subtitle, _attr(CP_DIM))
            row_offset = 4

        for i, (key, lbl, emo) in enumerate(norm_items):
            y = row_offset + i
            row_active = (i == selected)
            pointer = ">" if row_active else " "
            safe_addstr(stdscr, y, 4, pointer, _attr(CP_ACCENT, bold=True))
            check = "[x]" if state[key] else "[ ]"
            check_attr = _attr(CP_OK, bold=True) if state[key] else _attr(CP_DIM)
            safe_addstr(stdscr, y, 6, check, check_attr)
            if emo:
                safe_addstr(stdscr, y, 10, emo + " ")
                safe_addstr(stdscr, y, 13, lbl, _attr(CP_ACCENT, bold=True) if row_active else 0)
            else:
                lbl_attr = _attr(CP_ACCENT, bold=True) if row_active else 0
                safe_addstr(stdscr, y, 10, lbl, lbl_attr)

        draw_hint_pills(stdscr, h - 2, [
            ("↑↓",      "navigate"),
            ("Spc/Ent", "toggle"),
            ("esc",     "back"),
        ])
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
    config[section] = {k: state[k] for k, *_ in items}
    return config


def menu_bar_decoration(stdscr: "curses.window", config: dict) -> dict:
    curses.curs_set(0)
    stdscr.keypad(True)

    choices = [
        ("emoji", "symbols   🤖 | 💪 | 🧠 | 📦 | 🎫 | 🕔 | 📆"),
        ("label", "label     model | effort | thinking | ctx | tkn | 5h | 7d"),
    ]
    current = config.get("decoration", config.get("bar_mode_decoration", DEFAULTS["decoration"]))
    if current not in ("emoji", "label"):
        current = "emoji"
    selected = 0 if current == "emoji" else 1

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        draw_box(stdscr, "Decoration")

        sub = "Prefix shown in front of each segment (all display modes)"
        safe_addstr(stdscr, 2, max(2, (w - len(sub)) // 2), sub, _attr(CP_DIM))

        for i, (_, lbl) in enumerate(choices):
            y = 4 + i * 2
            row_active = (i == selected)
            pointer = ">" if row_active else " "
            safe_addstr(stdscr, y, 4, pointer, _attr(CP_ACCENT, bold=True))
            radio = "(*)" if row_active else "( )"
            radio_attr = _attr(CP_OK, bold=True) if row_active else _attr(CP_DIM)
            safe_addstr(stdscr, y, 6, radio, radio_attr)
            lbl_attr = _attr(CP_ACCENT, bold=True) if row_active else 0
            safe_addstr(stdscr, y, 10, lbl, lbl_attr)

        draw_hint_pills(stdscr, h - 2, [
            ("↑↓",      "choose"),
            ("Ent/Spc", "select"),
            ("esc",     "back"),
        ])
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
        ("fill",   "fill     ▰▰▰▰▰▱▱▱▱▱"),
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

        sub = "Glyphs used for filled / empty bar segments"
        safe_addstr(stdscr, 2, max(2, (w - len(sub)) // 2), sub, _attr(CP_DIM))

        for i, (_, lbl) in enumerate(choices):
            y = 4 + i * 2
            row_active = (i == selected)
            pointer = ">" if row_active else " "
            safe_addstr(stdscr, y, 4, pointer, _attr(CP_ACCENT, bold=True))
            radio = "(*)" if row_active else "( )"
            radio_attr = _attr(CP_OK, bold=True) if row_active else _attr(CP_DIM)
            safe_addstr(stdscr, y, 6, radio, radio_attr)
            lbl_attr = _attr(CP_ACCENT, bold=True) if row_active else 0
            safe_addstr(stdscr, y, 10, lbl, lbl_attr)

        draw_hint_pills(stdscr, h - 2, [
            ("↑↓",      "choose"),
            ("Ent/Spc", "select"),
            ("esc",     "back"),
        ])
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


def menu_updates(stdscr: "curses.window", config: dict) -> dict:
    curses.curs_set(0)
    stdscr.keypad(True)

    choices = [
        ("never",   "never     no update checks"),
        ("daily",   "daily     check once per day"),
        ("weekly",  "weekly    check once per week"),
        ("monthly", "monthly   check once per month"),
    ]
    current = str(config.get("updates", {}).get("check", DEFAULTS["updates"]["check"])).lower()
    if current not in UPDATE_CHOICES:
        current = "weekly"
    selected = next((i for i, (k, _) in enumerate(choices) if k == current), 2)

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        draw_box(stdscr, "Update checks")

        sub = "How often to check GitHub for a new release"
        safe_addstr(stdscr, 2, max(2, (w - len(sub)) // 2), sub, _attr(CP_DIM))

        cache = load_update_cache()
        cur_v  = cache.get("current_version") or "?"
        last_v = cache.get("latest_version")  or "?"
        info = f"installed: {cur_v}    latest: {last_v}"
        safe_addstr(stdscr, 3, max(2, (w - len(info)) // 2), info, _attr(CP_DIM))

        for i, (_, lbl) in enumerate(choices):
            y = 5 + i * 2
            row_active = (i == selected)
            pointer = ">" if row_active else " "
            safe_addstr(stdscr, y, 4, pointer, _attr(CP_ACCENT, bold=True))
            radio = "(*)" if row_active else "( )"
            radio_attr = _attr(CP_OK, bold=True) if row_active else _attr(CP_DIM)
            safe_addstr(stdscr, y, 6, radio, radio_attr)
            lbl_attr = _attr(CP_ACCENT, bold=True) if row_active else 0
            safe_addstr(stdscr, y, 10, lbl, lbl_attr)

        draw_hint_pills(stdscr, h - 2, [
            ("↑↓",      "choose"),
            ("Ent/Spc", "select"),
            ("esc",     "back"),
        ])
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
    config["updates"] = {"check": choices[selected][0]}
    return config


_save_result: bool = False


MAX_TUI_H = 24
MAX_TUI_W = 90


def run(stdscr: "curses.window") -> None:
    global _save_result
    init_colors()
    try:
        stdscr.bkgd(" ", curses.color_pair(0))
    except curses.error:
        pass
    stdscr.clear()
    stdscr.refresh()

    th, tw = stdscr.getmaxyx()
    h = min(MAX_TUI_H, th)
    w = min(MAX_TUI_W, tw)
    y = max(0, (th - h) // 2)
    x = max(0, (tw - w) // 2)
    win = curses.newwin(h, w, y, x)
    try:
        win.bkgd(" ", curses.color_pair(0))
    except curses.error:
        pass
    win.keypad(True)

    raw = load_config()
    raw.pop("bar_mode_decoration", None)
    config = deep_merge(DEFAULTS, raw)
    original = json.loads(json.dumps(config))
    config, _save_result = main_menu(win, config, original)
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
