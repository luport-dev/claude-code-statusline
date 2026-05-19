#!/usr/bin/env python3
"""Claude Code CLI status line — Windows / Python implementation.

Reads JSON session data from stdin, prints a two-line ANSI-coloured status line
to stdout. Behaviour mirrors scripts/linux/statusline.sh (jq) line-for-line.
"""
from __future__ import annotations

import json
import math
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


def to_float(value, default: float = 0.0) -> float:
    """Parse to float; tolerate strings, None, and garbage."""
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def fmt_pct(value: float) -> str:
    """Format percentage as whole number, rounded up to match /usage."""
    return f"{math.ceil(value)}%"


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


# 10-segment gradient (green -> yellow -> red), inspired by kcchien/claude-code-statusline
_GRAD_R = (46, 116, 186, 241, 239, 236, 233, 231, 211, 192)
_GRAD_G = (204, 195, 186, 196, 161, 126, 101,  76,  66,  57)
_GRAD_B = (113,  89,  64,  15,  24,  34,  44,  60,  50,  43)
_BAR_EMPTY_COLOR = f"{ESC}[38;2;80;80;80m"

_NARROW_EMOJIS = {"🪾"}

_BAR_GLYPHS = {
    "fill":   ("▰", "▱"),
    "block":  ("█", "░"),
    "dot":    ("●", "○"),
    "square": ("■", "□"),
}


def bar_last_color(pct: int, segments: int = 10) -> str:
    """Return the ANSI color of the last filled segment for a given percentage."""
    pct = max(0, min(100, pct))
    filled = pct * segments // 100
    if filled == 0:
        return f"{ESC}[32m"  # grün bei 0%
    idx = min(filled - 1, len(_GRAD_R) - 1)
    return f"{ESC}[38;2;{_GRAD_R[idx]};{_GRAD_G[idx]};{_GRAD_B[idx]}m"


def render_bar(pct: int, glyphs: tuple[str, str] = ("▰", "▱"), segments: int = 10) -> str:
    """Render a coloured progress bar for a 0-100 percentage."""
    on, off = glyphs
    pct = max(0, min(100, pct))
    filled = pct * segments // 100
    out = []
    for i in range(segments):
        if i < filled:
            idx = min(i, len(_GRAD_R) - 1)
            out.append(f"{ESC}[38;2;{_GRAD_R[idx]};{_GRAD_G[idx]};{_GRAD_B[idx]}m{on}")
        else:
            out.append(f"{_BAR_EMPTY_COLOR}{off}")
    out.append(RESET)
    return "".join(out)


def model_color(name: str) -> str:
    n = (name or "").lower()
    if "opus" in n:
        return f"{ESC}[38;2;255;215;0m"   # gold
    if "sonnet" in n:
        return f"{ESC}[38;2;100;180;255m" # light blue
    if "haiku" in n:
        return f"{ESC}[38;5;255m"         # white
    return f"{ESC}[37m"


_EFFORT_LEVELS = ("low", "medium", "high", "xhigh")


def effort_color(level: str) -> str:
    if level == "xhigh":
        return f"{ESC}[31m"
    if level == "high":
        return f"{ESC}[38;5;208m"  # orange
    if level == "medium":
        return f"{ESC}[33m"
    return f"{ESC}[32m"


_MODEL_ORDER = ("haiku", "sonnet", "opus")


def render_model_bar(name: str, glyphs: tuple[str, str] = ("▰", "▱")) -> str:
    """3-segment bar (haiku, sonnet, opus). Only the active model's segment is coloured."""
    on, off = glyphs
    n = (name or "").lower()
    active = next((m for m in _MODEL_ORDER if m in n), None)
    out = []
    for m in _MODEL_ORDER:
        if m == active:
            out.append(f"{model_color(m)}{on}")
        else:
            out.append(f"{_BAR_EMPTY_COLOR}{off}")
    out.append(RESET)
    return "".join(out)


def render_thinking_bar(on_state: bool, glyphs: tuple[str, str] = ("▰", "▱")) -> str:
    """2-segment bar: left=off (red), right=on (green). Only one is coloured."""
    on, off = glyphs
    red   = f"{ESC}[31m"
    green = f"{ESC}[32m"
    if on_state:
        return f"{_BAR_EMPTY_COLOR}{off}{green}{on}{RESET}"
    return f"{red}{on}{_BAR_EMPTY_COLOR}{off}{RESET}"


def render_effort_bar(level: str, glyphs: tuple[str, str] = ("▰", "▱")) -> str:
    """4-segment bar (low → xhigh), filled up to the current level."""
    on, off = glyphs
    try:
        filled = _EFFORT_LEVELS.index(level) + 1
    except ValueError:
        filled = 0
    out = []
    for i, lvl in enumerate(_EFFORT_LEVELS):
        if i < filled:
            out.append(f"{effort_color(lvl)}{on}")
        else:
            out.append(f"{_BAR_EMPTY_COLOR}{off}")
    out.append(RESET)
    return "".join(out)


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
_STATE_PATH  = Path.home() / ".claude" / "statusline_state.json"
_UPDATE_PATH = Path.home() / ".claude" / "statusline_update.json"

_GITHUB_REPO = "luport-dev/claude-code-statusline"
_UPDATE_INTERVALS_SEC = {
    "daily":   24 * 3600,
    "weekly":  7 * 24 * 3600,
    "monthly": 30 * 24 * 3600,
}

_DISPLAY_CHOICES = ("bar", "text", "both", "off")

_BAR_EMOJI = {
    "model":    "🤖",
    "effort":   "💪",
    "thinking": "🧠",
    "ctx":      "📦",
    "tkn":      "🎫",
    "five":     "🕔",
    "week":     "📆",
    "dir":      "📁",
    "branch":   "🌿",
    "worktree": "🌳",
}

_BAR_LABEL = {
    "model":    "model",
    "effort":   "effort",
    "thinking": "thinking",
    "ctx":      "ctx",
    "tkn":      "tkn",
    "five":     "5h",
    "week":     "7d",
    "dir":      "dir",
    "branch":   "branch",
    "worktree": "worktree",
}

_DEFAULTS: dict = {
    "thresholds": {
        "ctx":  {"warn": 60, "crit": 80},
        "tkn":  {"warn": 60, "crit": 80},
        "five": {"warn": 60, "crit": 80},
        "week": {"warn": 60, "crit": 80},
    },
    "line1": {},
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


def cfg_bar_glyphs(config: dict) -> tuple[str, str]:
    style = config.get("bar_style", "dot")
    return _BAR_GLYPHS.get(style, _BAR_GLYPHS["dot"])


def cfg_decoration(config: dict) -> str:
    """Global label/emoji choice. Falls back to legacy bar_mode_decoration key."""
    val = config.get("decoration", config.get("bar_mode_decoration"))
    return "label" if val == "label" else "emoji"


def prefix(config: dict, metric: str, color: str, sep: str = " ") -> str:
    """Leading decoration for any segment: emoji (no colour) or coloured word label."""
    if cfg_decoration(config) == "label":
        if metric == "model":
            return ""
        return f"{color}{_BAR_LABEL[metric]}{RESET}{sep}"
    emo = _BAR_EMOJI[metric]
    pad = " " if emo in _NARROW_EMOJIS else ""
    return f"{emo}{pad}{sep}"


def cfg_display(config: dict, metric: str) -> str:
    """Return the display mode for a metric: bar | text | both | off."""
    val = config.get("metrics", {}).get(metric, {}).get("display")
    if val in _DISPLAY_CHOICES:
        return val
    legacy = config.get("line1", {})
    if f"show_{metric}" in legacy and not legacy.get(f"show_{metric}", True):
        return "off"
    if legacy.get(f"show_{metric}_bar"):
        return "both"
    return _DEFAULTS["metrics"][metric]["display"]


def load_state() -> dict:
    try:
        if _STATE_PATH.exists():
            with _STATE_PATH.open(encoding="utf-8") as f:
                d = json.load(f)
            return d if isinstance(d, dict) else {}
    except Exception:
        pass
    return {}


def save_state(data: dict) -> None:
    try:
        _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _STATE_PATH.open("w", encoding="utf-8") as f:
            json.dump(data, f)
    except OSError:
        pass


def _parse_version(v: str) -> tuple[int, ...]:
    """Parse 'v1.2.3' or '1.2.3' → (1,2,3). Non-numeric parts become 0."""
    s = (v or "").lstrip("vV").strip()
    parts: list[int] = []
    for chunk in s.split("."):
        num = ""
        for ch in chunk:
            if ch.isdigit():
                num += ch
            else:
                break
        parts.append(int(num) if num else 0)
    return tuple(parts) or (0,)


def load_update_cache() -> dict:
    try:
        if _UPDATE_PATH.exists():
            with _UPDATE_PATH.open(encoding="utf-8") as f:
                d = json.load(f)
            return d if isinstance(d, dict) else {}
    except Exception:
        pass
    return {}


def save_update_cache(data: dict) -> None:
    try:
        _UPDATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = _UPDATE_PATH.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        tmp.replace(_UPDATE_PATH)
    except OSError:
        pass


def _gh_get(url: str):
    import urllib.request
    import urllib.error
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "claude-code-statusline",
    })
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            return json.load(resp)
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError, TimeoutError):
        return None


def _fetch_latest_release() -> str | None:
    """Return the latest release tag from GitHub. Falls back to newest tag."""
    payload = _gh_get(f"https://api.github.com/repos/{_GITHUB_REPO}/releases/latest")
    if isinstance(payload, dict):
        tag = payload.get("tag_name") or payload.get("name")
        if tag:
            return str(tag)
    tags = _gh_get(f"https://api.github.com/repos/{_GITHUB_REPO}/tags?per_page=1")
    if isinstance(tags, list) and tags:
        name = tags[0].get("name") if isinstance(tags[0], dict) else None
        if name:
            return str(name)
    return None


def _update_check_worker() -> None:
    """Background thread: fetch latest release, update cache file."""
    cache = load_update_cache()
    current = str(cache.get("current_version") or "0.1.1")
    latest = _fetch_latest_release()
    from datetime import datetime, timezone
    now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    if latest is None:
        cache["last_checked"] = now_iso
        save_update_cache(cache)
        return
    available = _parse_version(latest) > _parse_version(current)
    cache.update({
        "last_checked":     now_iso,
        "latest_version":   latest,
        "current_version":  current,
        "update_available": available,
    })
    save_update_cache(cache)


def maybe_trigger_update_check(config: dict) -> None:
    """Spawn a daemon thread to refresh the update cache if interval elapsed."""
    mode = str(config.get("updates", {}).get("check", "weekly")).lower()
    if mode == "never":
        return
    interval = _UPDATE_INTERVALS_SEC.get(mode)
    if interval is None:
        return
    cache = load_update_cache()
    last = cache.get("last_checked")
    if last:
        try:
            from datetime import datetime
            last_dt = datetime.fromisoformat(str(last).replace("Z", "+00:00"))
            from datetime import datetime as _dt, timezone as _tz
            now = _dt.now(_tz.utc)
            if last_dt.tzinfo is None:
                from datetime import timezone as _tz2
                last_dt = last_dt.replace(tzinfo=_tz2.utc)
            if (now - last_dt).total_seconds() < interval:
                return
        except (ValueError, TypeError):
            pass
    import threading
    t = threading.Thread(target=_update_check_worker, daemon=True)
    t.start()


def update_hint_segment(config: dict) -> str | None:
    """Return rendered '⬆ vX.Y.Z' segment for line 2, or None."""
    mode = str(config.get("updates", {}).get("check", "weekly")).lower()
    if mode == "never":
        return None
    cache = load_update_cache()
    if not cache.get("update_available"):
        return None
    latest = cache.get("latest_version") or ""
    if not latest:
        return None
    tag = str(latest)
    if not tag.startswith(("v", "V")):
        tag = f"v{tag}"
    return f"{DIM_GRAY}🔔 {tag} available{RESET}"


def main() -> None:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
        if not isinstance(data, dict):
            data = {}
    except Exception:
        print("?")
        return

    state = load_state()
    # Fehlende Werte aus dem letzten bekannten State ergänzen
    if not data:
        data = state.get("last_data", {})

    cwd      = dig(data, "cwd", "") or ""
    worktree = dig(data, "worktree.name", "") or ""
    model    = dig(data, "model.display_name", "") or ""
    effort   = dig(data, "effort.level", "low") or "low"
    ctx_f    = to_float(dig(data, "context_window.used_percentage"))
    ctx      = int(ctx_f)
    tkn      = to_int(dig(data, "context_window.total_input_tokens"))
    tkn_pct_f = ctx_f
    tkn_pct  = ctx
    five_f   = to_float(dig(data, "rate_limits.five_hour.used_percentage"))
    five     = int(five_f)
    week_f   = to_float(dig(data, "rate_limits.seven_day.used_percentage"))
    week     = int(week_f)

    branch = git_branch(cwd)
    thinking_on = read_thinking_setting()

    if model:
        save_state({"last_data": data})

    is_haiku = "haiku" in model.lower()

    # --- line 1 ----------------------------------------------------------
    mc = model_color(model)
    ec = effort_color(effort)

    config = load_config()
    glyphs = cfg_bar_glyphs(config)
    maybe_trigger_update_check(config)

    def text_prefix(metric: str, color: str) -> str:
        if cfg_decoration(config) == "label":
            if metric == "model":
                return ""
            return f"{color}{_BAR_LABEL[metric]}:{RESET} "
        emo = _BAR_EMOJI[metric]
        pad = "  " if emo in _NARROW_EMOJIS else " "
        return f"{emo}{pad}"

    if is_haiku:
        effort_segment = f"{text_prefix('effort', DIM_GRAY)}{DIM_GRAY}n/a{RESET}"
    else:
        effort_segment = f"{text_prefix('effort', ec)}{ec}{effort}{RESET}"

    if thinking_on:
        thinking_segment = f"{text_prefix('thinking', THINKING_ON_COLOR)}{THINKING_ON_COLOR}on{RESET}"
    else:
        thinking_segment = f"{text_prefix('thinking', DIM_GRAY)}{DIM_GRAY}off{RESET}"

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

    model_mode = cfg_display(config, "model")
    if model_mode != "off":
        m_text = f"{mc}{model}{RESET}"
        m_bar = render_model_bar(model, glyphs)
        if model_mode == "bar":
            line1_parts.append(f"{prefix(config, 'model', mc)}{m_bar}")
        elif model_mode == "text":
            line1_parts.append(f"{text_prefix('model', mc)}{m_text}")
        else:
            line1_parts.append(f"{text_prefix('model', mc)}{m_text} {m_bar}")

    effort_mode = cfg_display(config, "effort")
    if effort_mode != "off" and not is_haiku:
        bar = render_effort_bar(effort, glyphs)
        text = f"{ec}{effort}{RESET}"
        if effort_mode == "bar":
            line1_parts.append(f"{prefix(config, 'effort', ec)}{bar}")
        elif effort_mode == "text":
            line1_parts.append(f"{text_prefix('effort', ec)}{text}")
        else:
            line1_parts.append(f"{text_prefix('effort', ec)}{bar} {text}")
    elif is_haiku and effort_mode != "off":
        if effort_mode == "bar":
            line1_parts.append(f"{prefix(config, 'effort', DIM_GRAY)}{DIM_GRAY}n/a{RESET}")
        else:
            line1_parts.append(effort_segment)

    thinking_mode = cfg_display(config, "thinking")
    if thinking_mode != "off":
        th_color = THINKING_ON_COLOR if thinking_on else DIM_GRAY
        th_bar = render_thinking_bar(thinking_on, glyphs)
        if thinking_mode == "bar":
            line1_parts.append(f"{prefix(config, 'thinking', th_color)}{th_bar}")
        elif thinking_mode == "text":
            line1_parts.append(thinking_segment)
        else:
            line1_parts.append(f"{text_prefix('thinking', th_color)}{th_bar} {th_color}{'on' if thinking_on else 'off'}{RESET}")

    def metric_segment(metric: str, pct: int, color: str, text_value: str) -> str | None:
        mode = cfg_display(config, metric)
        if mode == "off":
            return None
        bar = render_bar(pct, glyphs)
        last_color = bar_last_color(pct)
        if mode == "bar":
            return f"{prefix(config, metric, last_color)}{bar}"
        if mode == "text":
            return f"{text_prefix(metric, color)}{color}{text_value}{RESET}"
        return f"{text_prefix(metric, last_color)}{bar} {last_color}{text_value}{RESET}"

    for seg in (
        metric_segment("ctx",  ctx,     ctx_c,  fmt_pct(ctx_f)),
        metric_segment("tkn",  tkn_pct, tkn_c,  fmt_tokens(tkn)),
        metric_segment("five", five,    five_c, fmt_pct(five_f)),
        metric_segment("week", week,    week_c, fmt_pct(week_f)),
    ):
        if seg is not None:
            line1_parts.append(seg)
    line1 = SEP.join(line1_parts)

    # --- line 2 ----------------------------------------------------------
    show_dir      = cfg_visibility(config, "line2", "show_dir")
    show_branch   = cfg_visibility(config, "line2", "show_branch")
    show_worktree = cfg_visibility(config, "line2", "show_worktree")
    active        = sum([show_dir, show_branch, show_worktree])

    term_cols = shutil.get_terminal_size(fallback=(120, 24)).columns
    total_budget = max(3 * max(1, active), int(term_cols * 0.80))

    raw_items: list[tuple[str, str]] = []
    if show_dir:
        raw_items.append(("dir", cwd or "?"))
    if show_branch:
        raw_items.append(("branch", branch))
    if show_worktree:
        raw_items.append(("worktree", worktree))

    # Two-pass allocation: equal share, donors release surplus, deficit items
    # split the freed pool proportionally to how much extra they need.
    if raw_items:
        share = max(3, total_budget // len(raw_items))
        needs = [len(v) for _, v in raw_items]
        budgets = [min(share, need) for need in needs]
        surplus = sum(share - b for b in budgets)
        deficits = [max(0, need - share) for need in needs]
        deficit_total = sum(deficits)
        if surplus and deficit_total:
            for i, d in enumerate(deficits):
                if d:
                    budgets[i] += surplus * d // deficit_total
            leftover = surplus - sum(surplus * d // deficit_total for d in deficits)
            for i, d in enumerate(deficits):
                if leftover <= 0:
                    break
                if d:
                    budgets[i] += 1
                    leftover -= 1
        widths = {name: budgets[i] for i, (name, _) in enumerate(raw_items)}
    else:
        widths = {}

    def trunc(value: str, n: int) -> str:
        return f"…{value[-(n - 1):]}" if len(value) > n and n > 1 else (value if len(value) <= n else value[-n:])

    def field(name: str, value: str) -> str:
        if cfg_decoration(config) == "label":
            head = f"{LABEL_COLOR}{_BAR_LABEL[name]}: {RESET}"
        else:
            emo = _BAR_EMOJI[name]
            pad = "  " if emo in _NARROW_EMOJIS else " "
            head = f"{emo}{pad}"
        n = widths.get(name, 3)
        return f"{head}{VALUE_COLOR}{trunc(value, n) or '-'}{RESET}"

    line2_parts = [field(name, value) for name, value in raw_items]
    hint = update_hint_segment(config)
    if hint:
        line2_parts.append(hint)
    line2 = SEP.join(line2_parts) if line2_parts else ""

    print(line1)
    if line2:
        print(line2)


if __name__ == "__main__":
    main()
