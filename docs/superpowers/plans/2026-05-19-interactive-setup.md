# Interactive Setup TUI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A cross-platform curses TUI at `setup/configure.py` that lets users configure color thresholds and line 2 field visibility, persisted to `~/.claude/statusline_config.json` and read by `scripts/statusline.py`.

**Architecture:** `setup/configure.py` is a self-contained curses app that reads/writes `~/.claude/statusline_config.json`. `scripts/statusline.py` gains a `load_config()` function that reads this file on every invocation and applies thresholds and visibility. On Windows, `windows-curses` must be installed via pip (added to `setup/win/install.cmd`).

**Tech Stack:** Python 3, curses (stdlib on Linux/macOS, `windows-curses` on Windows), JSON

---

## File Map

```
setup/
  configure.py           ← NEW: cross-platform curses TUI
  win/
    install.cmd          ← MODIFIED: pip install windows-curses

scripts/
  statusline.py          ← MODIFIED: load_config(), apply thresholds + visibility
```

Config file: `~/.claude/statusline_config.json`

---

### Task 1: Add `load_config()` to `scripts/statusline.py`

**Files:**
- Modify: `scripts/statusline.py`

- [ ] **Step 1: Add `load_config()` after `read_thinking_setting()`**

Insert this function at line 129 (after `read_thinking_setting`):

```python
_CONFIG_PATH = Path.home() / ".claude" / "statusline_config.json"

_DEFAULTS: dict = {
    "thresholds": {
        "ctx":  {"warn": 70, "crit": 90},
        "tkn":  {"warn": 70, "crit": 90},
        "five": {"warn": 70, "crit": 90},
        "week": {"warn": 50, "crit": 80},
    },
    "line2": {
        "show_dir":      True,
        "show_branch":   True,
        "show_worktree": True,
    },
}


def load_config() -> dict:
    try:
        if _CONFIG_PATH.exists():
            with _CONFIG_PATH.open(encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def cfg_threshold(config: dict, key: str) -> tuple[int, int]:
    t = config.get("thresholds", {}).get(key, {})
    d = _DEFAULTS["thresholds"][key]
    warn = int(t.get("warn", d["warn"]))
    crit = int(t.get("crit", d["crit"]))
    return warn, crit


def cfg_line2(config: dict, key: str) -> bool:
    return bool(config.get("line2", {}).get(key, _DEFAULTS["line2"][key]))
```

- [ ] **Step 2: Apply config in `main()`**

Replace the threshold calls and line2 assembly in `main()`. The current hardcoded calls:

```python
    ctx_c  = color_threshold(ctx,  70, 90)
    five_c = color_threshold(five, 70, 90)
    week_c = color_threshold(week, 50, 80)
```

And the line2 block:

```python
    line2 = SEP.join([
        field("dir",      cwd or "?"),
        field("branch",   branch),
        field("worktree", worktree),
    ])
```

Replace with:

```python
    config = load_config()

    ctx_warn,  ctx_crit  = cfg_threshold(config, "ctx")
    tkn_warn,  tkn_crit  = cfg_threshold(config, "tkn")
    five_warn, five_crit = cfg_threshold(config, "five")
    week_warn, week_crit = cfg_threshold(config, "week")

    ctx_c  = color_threshold(ctx,  ctx_warn,  ctx_crit)
    tkn_c  = color_threshold(tkn,  tkn_warn,  tkn_crit)
    five_c = color_threshold(five, five_warn, five_crit)
    week_c = color_threshold(week, week_warn, week_crit)
```

And update `line1` to use `tkn_c` (currently it reuses `ctx_c` for tkn):

```python
    line1 = SEP.join([
        f"{mc}{model}{RESET}",
        effort_segment,
        thinking_segment,
        f"{ctx_c}ctx:{RESET}{ctx_c}{ctx}%{RESET}",
        f"{tkn_c}tkn:{RESET}{tkn_c}{fmt_tokens(tkn)}{RESET}",
        f"{five_c}5h:{RESET}{five_c}{five}%{RESET}",
        f"{week_c}7d:{RESET}{week_c}{week}%{RESET}",
    ])
```

And the line2 block:

```python
    line2_parts = []
    if cfg_line2(config, "show_dir"):
        line2_parts.append(field("dir", cwd or "?"))
    if cfg_line2(config, "show_branch"):
        line2_parts.append(field("branch", branch))
    if cfg_line2(config, "show_worktree"):
        line2_parts.append(field("worktree", worktree))
    line2 = SEP.join(line2_parts) if line2_parts else ""
```

And update the print at the end:

```python
    print(line1)
    if line2:
        print(line2)
```

- [ ] **Step 3: Verify with test input**

```bash
echo '{"cwd":"/tmp","model":{"display_name":"Claude Sonnet 4.6"},"effort":{"level":"medium"},"context_window":{"used_percentage":42,"total_input_tokens":12000},"rate_limits":{"five_hour":{"used_percentage":10},"seven_day":{"used_percentage":5}}}' | python3 scripts/statusline.py
```

Expected: two lines, no errors.

- [ ] **Step 4: Verify config file is respected**

```bash
cat > /tmp/test_config.json << 'EOF'
{"thresholds":{"ctx":{"warn":30,"crit":40}},"line2":{"show_dir":true,"show_branch":false,"show_worktree":false}}
EOF
# Temporarily point to test config by symlinking
cp /tmp/test_config.json ~/.claude/statusline_config.json
echo '{"cwd":"/tmp","model":{"display_name":"Claude Sonnet 4.6"},"effort":{"level":"medium"},"context_window":{"used_percentage":42,"total_input_tokens":12000},"rate_limits":{"five_hour":{"used_percentage":10},"seven_day":{"used_percentage":5}}}' | python3 scripts/statusline.py
```

Expected: ctx shown in yellow (42 > 30), line2 shows only `dir:`.

```bash
rm ~/.claude/statusline_config.json
```

---

### Task 2: Create `setup/configure.py` — main menu skeleton

**Files:**
- Create: `setup/configure.py`

- [ ] **Step 1: Write the file**

```python
#!/usr/bin/env python3
"""Interactive configuration TUI for the Claude Code status line.

Requires: curses (stdlib on Linux/macOS)
          windows-curses (pip install windows-curses) on Windows
"""
from __future__ import annotations

import curses
import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".claude" / "statusline_config.json"

DEFAULTS: dict = {
    "thresholds": {
        "ctx":  {"warn": 70, "crit": 90},
        "tkn":  {"warn": 70, "crit": 90},
        "five": {"warn": 70, "crit": 90},
        "week": {"warn": 50, "crit": 80},
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


MENU_ITEMS = ["Thresholds", "Line 2 visibility"]


def draw_box(win: "curses.window", title: str) -> None:
    win.box()
    h, w = win.getmaxyx()
    label = f" {title} "
    win.addstr(0, max(2, (w - len(label)) // 2), label, curses.A_BOLD)


def main_menu(stdscr: "curses.window", config: dict) -> dict:
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

        hint = "[↑↓] navigate  [Enter] open  [q] save & quit"
        stdscr.addstr(h - 2, max(2, (w - len(hint)) // 2), hint, curses.A_DIM)
        stdscr.refresh()

        key = stdscr.getch()
        if key in (ord("q"), ord("Q")):
            return config
        elif key == curses.KEY_UP:
            selected = (selected - 1) % len(MENU_ITEMS)
        elif key == curses.KEY_DOWN:
            selected = (selected + 1) % len(MENU_ITEMS)
        elif key in (curses.KEY_ENTER, ord("\n"), ord("\r")):
            if selected == 0:
                config = menu_thresholds(stdscr, config)
            elif selected == 1:
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
    error = ""

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        draw_box(stdscr, "Thresholds")

        for i, (key, label) in enumerate(rows):
            y = 2 + i
            stdscr.addstr(y, 2, label)
            for j, field in enumerate(fields):
                x = 10 + j * 18
                val = values[key][field]
                attr = curses.A_REVERSE if (i == row and j == col) else curses.A_NORMAL
                stdscr.addstr(y, x, f"{field}: [{val:>3}]", attr)

        hint = "[↑↓] rows  [←→] fields  [0-9] edit  [Backspace] clear  [Esc] back"
        stdscr.addstr(h - 2, max(2, (w - len(hint)) // 2), hint, curses.A_DIM)
        if error:
            stdscr.addstr(h - 3, 2, error, curses.A_BOLD)

        key_r, key_c = rows[row][0], fields[col]
        val = values[key_r][key_c]
        # Position cursor inside the bracket
        stdscr.move(2 + row, 10 + col * 18 + len(f"{fields[col]}: [") + len(val))
        stdscr.refresh()

        key = stdscr.getch()
        error = ""

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

    # Validate and write back
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


def menu_visibility(stdscr: "curses.window", config: dict) -> dict:
    curses.curs_set(0)
    stdscr.keypad(True)

    items = [
        ("show_dir",      "dir"),
        ("show_branch",   "branch"),
        ("show_worktree", "worktree"),
    ]

    line2 = config.get("line2", {})
    state: dict[str, bool] = {
        k: bool(line2.get(k, DEFAULTS["line2"][k])) for k, _ in items
    }
    selected = 0

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        draw_box(stdscr, "Line 2 Visibility")

        for i, (key, label) in enumerate(items):
            check = "x" if state[key] else " "
            attr = curses.A_REVERSE if i == selected else curses.A_NORMAL
            stdscr.addstr(2 + i, 2, f"  [{check}] {label}", attr)

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
    config["line2"] = {k: state[k] for k, _ in items}
    return config


def run(stdscr: "curses.window") -> None:
    config = deep_merge(DEFAULTS, load_config())
    config = main_menu(stdscr, config)
    save_config(config)


if __name__ == "__main__":
    try:
        import curses as _curses_check
    except ImportError:
        print("ERROR: curses not available. On Windows: pip install windows-curses")
        raise SystemExit(1)
    curses.wrapper(run)
    print("Configuration saved.")
```

- [ ] **Step 2: Verify syntax**

```bash
python3 -m py_compile setup/configure.py && echo "OK"
```

Expected: `OK`

- [ ] **Step 3: Smoke test — launch the TUI**

```bash
python3 setup/configure.py
```

Expected: TUI opens, main menu shows two items, `q` saves and exits cleanly, `Configuration saved.` printed.

---

### Task 3: Add `windows-curses` install to `setup/win/install.cmd`

**Files:**
- Modify: `setup/win/install.cmd`

- [ ] **Step 1: Add pip install after Python is confirmed**

In `setup/win/install.cmd`, after the final `if not defined PY` guard block (line ~38) and before the `rem --- Locate git` section, insert:

```bat
rem --- Install windows-curses for the configure.py TUI ----------------
%PY% -m pip install --quiet windows-curses
if errorlevel 1 (
    echo WARN: Could not install windows-curses. configure.py TUI may not work.
)
```

- [ ] **Step 2: Verify the file looks correct**

```bash
grep -n "windows-curses" setup/win/install.cmd
```

Expected: one matching line.

---

### Task 4: Full integration smoke test

**Files:** none

- [ ] **Step 1: Run configure.py, set ctx warn to 10, crit to 20, hide worktree**

```bash
python3 setup/configure.py
```

Navigate to Thresholds → set ctx warn=10, crit=20 → Esc.
Navigate to Line 2 visibility → toggle worktree off → Esc.
Press `q` to save.

- [ ] **Step 2: Verify config was written correctly**

```bash
python3 -c "import json; print(json.dumps(json.load(open('$HOME/.claude/statusline_config.json')), indent=2))"
```

Expected output contains:
```json
"ctx": {"warn": 10, "crit": 20}
```
and:
```json
"show_worktree": false
```

- [ ] **Step 3: Verify statusline.py respects the config**

```bash
echo '{"cwd":"/tmp","model":{"display_name":"Claude Sonnet 4.6"},"effort":{"level":"medium"},"context_window":{"used_percentage":15,"total_input_tokens":5000},"rate_limits":{"five_hour":{"used_percentage":5},"seven_day":{"used_percentage":2}}}' | python3 scripts/statusline.py
```

Expected:
- `ctx:15%` shown in **yellow** (15 > warn:10)
- Line 2 has no `worktree:` field

- [ ] **Step 4: Clean up test config**

```bash
rm ~/.claude/statusline_config.json
```

- [ ] **Step 5: Verify statusline.py falls back to defaults**

```bash
echo '{"cwd":"/tmp","model":{"display_name":"Claude Sonnet 4.6"},"effort":{"level":"medium"},"context_window":{"used_percentage":15,"total_input_tokens":5000},"rate_limits":{"five_hour":{"used_percentage":5},"seven_day":{"used_percentage":2}}}' | python3 scripts/statusline.py
```

Expected:
- `ctx:15%` shown in **green** (15 < default warn:70)
- Line 2 shows all three fields: `dir:`, `branch:`, `worktree:`
