#!/usr/bin/env python3
"""Claude Code CLI status line — Windows / Python implementation.

Reads JSON session data from stdin, prints a two-line ANSI-coloured status line
to stdout. Behaviour mirrors scripts/linux/statusline.sh (jq) line-for-line.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Force UTF-8 stdout so box-drawing characters render correctly on Windows
# consoles (default cp1252 mangles the pipe glyph and any non-ASCII content).
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ESC = "\x1b"
RESET = f"{ESC}[0m"
DIM = f"{ESC}[2m"
DIM_GRAY = f"{ESC}[2;37m"
SEP = f" {ESC}[2;37m|{RESET} "

LABEL_COLOR = f"{ESC}[38;5;130m"   # rust brown for dir/branch/worktree labels
VALUE_COLOR = f"{ESC}[38;5;172m"   # warm bronze for the values

THINKING_ON_COLOR = f"{ESC}[38;2;80;220;200m"  # teal


def dig(obj, path: str, default=None):
    """Safe dotted-path access. Returns default for any missing/None segment."""
    cur = obj
    for key in path.split("."):
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return default if cur is None else cur


def to_int(value, default: int = 0) -> int:
    """Floor numeric values; tolerate strings, None, and garbage."""
    if value is None:
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def fmt_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}k"
    return str(n)


def color_threshold(value: float, warn: float, crit: float) -> str:
    if value >= crit:
        return f"{ESC}[31m"  # red
    if value >= warn:
        return f"{ESC}[33m"  # yellow
    return f"{ESC}[32m"      # green


def model_color(name: str) -> str:
    n = (name or "").lower()
    if "opus" in n:
        return f"{ESC}[38;2;255;215;0m"   # gold
    if "sonnet" in n:
        return f"{ESC}[38;2;100;180;255m" # light blue
    if "haiku" in n:
        return f"{ESC}[38;5;255m"         # white
    return f"{ESC}[37m"


def effort_color(level: str) -> str:
    if level == "xhigh":
        return f"{ESC}[31m"
    if level == "high":
        return f"{ESC}[38;5;208m"  # orange
    if level == "medium":
        return f"{ESC}[33m"
    return f"{ESC}[32m"


def label(text: str, color: str) -> str:
    return f"{color}{text}: {RESET}"


def git_branch(cwd: str) -> str:
    if not cwd:
        return ""
    try:
        if not Path(cwd).exists():
            return ""
    except OSError:
        return ""
    try:
        r = subprocess.run(
            ["git", "-C", cwd, "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return ""
    if r.returncode != 0:
        return ""
    return r.stdout.strip()


def read_thinking_setting() -> bool:
    """Read alwaysThinkingEnabled from ~/.claude/settings.json (not from stdin)."""
    try:
        settings_path = Path.home() / ".claude" / "settings.json"
        if not settings_path.exists():
            return False
        with settings_path.open(encoding="utf-8") as f:
            return bool(json.load(f).get("alwaysThinkingEnabled"))
    except Exception:
        return False


_CONFIG_PATH = Path.home() / ".claude" / "statusline_config.json"

_DEFAULTS: dict = {
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


def cfg_visibility(config: dict, section: str, key: str) -> bool:
    return bool(config.get(section, {}).get(key, _DEFAULTS[section][key]))


def main() -> None:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
        if not isinstance(data, dict):
            data = {}
    except Exception:
        print("?")
        return

    cwd      = dig(data, "cwd", "") or ""
    worktree = dig(data, "worktree.name", "") or ""
    model    = dig(data, "model.display_name", "") or ""
    effort   = dig(data, "effort.level", "low") or "low"
    ctx      = to_int(dig(data, "context_window.used_percentage"))
    tkn      = to_int(dig(data, "context_window.total_input_tokens"))
    tkn_pct  = to_int(dig(data, "context_window.used_percentage"))
    five     = to_int(dig(data, "rate_limits.five_hour.used_percentage"))
    week     = to_int(dig(data, "rate_limits.seven_day.used_percentage"))

    branch = git_branch(cwd)
    thinking_on = read_thinking_setting()
    is_haiku = "haiku" in model.lower()

    # --- line 1 ----------------------------------------------------------
    mc = model_color(model)
    ec = effort_color(effort)

    if is_haiku:
        effort_segment = f"{DIM_GRAY}effort:{RESET}{DIM_GRAY}n/a{RESET}"
    else:
        effort_segment = f"{ec}effort:{RESET}{ec}{effort}{RESET}"

    if thinking_on:
        thinking_segment = f"{THINKING_ON_COLOR}thinking:on{RESET}"
    else:
        thinking_segment = f"{DIM_GRAY}thinking:off{RESET}"

    config = load_config()

    ctx_warn,  ctx_crit  = cfg_threshold(config, "ctx")
    tkn_warn,  tkn_crit  = cfg_threshold(config, "tkn")
    five_warn, five_crit = cfg_threshold(config, "five")
    week_warn, week_crit = cfg_threshold(config, "week")

    ctx_c  = color_threshold(ctx,  ctx_warn,  ctx_crit)
    tkn_c  = color_threshold(tkn_pct, tkn_warn, tkn_crit)
    five_c = color_threshold(five, five_warn, five_crit)
    week_c = color_threshold(week, week_warn, week_crit)

    v1 = lambda k: cfg_visibility(config, "line1", k)
    line1_parts = []
    if v1("show_model"):
        line1_parts.append(f"{mc}{model}{RESET}")
    if v1("show_effort"):
        line1_parts.append(effort_segment)
    if v1("show_thinking"):
        line1_parts.append(thinking_segment)
    if v1("show_ctx"):
        line1_parts.append(f"{ctx_c}ctx:{RESET}{ctx_c}{ctx}%{RESET}")
    if v1("show_tkn"):
        line1_parts.append(f"{tkn_c}tkn:{RESET}{tkn_c}{fmt_tokens(tkn)}{RESET}")
    if v1("show_five"):
        line1_parts.append(f"{five_c}5h:{RESET}{five_c}{five}%{RESET}")
    if v1("show_week"):
        line1_parts.append(f"{week_c}7d:{RESET}{week_c}{week}%{RESET}")
    line1 = SEP.join(line1_parts)

    # --- line 2 ----------------------------------------------------------
    show_dir      = cfg_visibility(config, "line2", "show_dir")
    show_branch   = cfg_visibility(config, "line2", "show_branch")
    show_worktree = cfg_visibility(config, "line2", "show_worktree")
    active        = sum([show_dir, show_branch, show_worktree])

    term_cols = shutil.get_terminal_size(fallback=(120, 24)).columns
    n         = max(3, int(term_cols * 0.80) // max(1, active))

    def trunc(value: str) -> str:
        return f"…{value[-n:]}" if len(value) > n else value

    def field(name: str, value: str) -> str:
        return f"{LABEL_COLOR}{name}: {RESET}{VALUE_COLOR}{trunc(value) or '-'}{RESET}"

    line2_parts = []
    if show_dir:
        line2_parts.append(field("dir", cwd or "?"))
    if show_branch:
        line2_parts.append(field("branch", branch))
    if show_worktree:
        line2_parts.append(field("worktree", worktree))
    line2 = SEP.join(line2_parts) if line2_parts else ""

    print(line1)
    if line2:
        print(line2)


if __name__ == "__main__":
    main()
