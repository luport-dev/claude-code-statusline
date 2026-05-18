# Design: Interactive Setup TUI

**Date:** 2026-05-19  
**Status:** Approved

## Goal

A curses-based interactive configuration tool for the Claude Code status line. Users can adjust color thresholds and toggle the visibility of line 2 fields, without editing JSON by hand.

## Platform Support

Works on Linux, macOS, and Windows. Uses Python's built-in `curses` on Linux/macOS. On Windows, requires `windows-curses` (`pip install windows-curses`), which provides the same API. `install.cmd` installs `windows-curses` automatically during setup.

## Files

| File | Change |
|------|--------|
| `setup/configure.py` | New — cross-platform curses TUI (shared) |
| `setup/win/install.cmd` | Modified — `pip install windows-curses` after Python install |
| `scripts/statusline.py` | Modified — load config, apply thresholds and visibility |

## Config File

Location: `~/.claude/statusline_config.json`

```json
{
  "thresholds": {
    "ctx":  {"warn": 70, "crit": 90},
    "tkn":  {"warn": 70, "crit": 90},
    "five": {"warn": 70, "crit": 90},
    "week": {"warn": 50, "crit": 80}
  },
  "line2": {
    "show_dir":      true,
    "show_branch":   true,
    "show_worktree": true
  }
}
```

If the file does not exist, `statusline.py` uses the hardcoded defaults above.

## TUI Structure

### Main Menu

```
┌─ Claude Code Status Line — Configuration ───────────────┐
│                                                          │
│  > 1. Thresholds                                         │
│    2. Line 2 visibility                                  │
│                                                          │
│  [↑↓] navigate  [Enter] open  [q] save & quit           │
└──────────────────────────────────────────────────────────┘
```

### Menu 1 — Thresholds

Four rows, one per metric. Each row has two editable fields: `warn` and `crit`.

```
  ctx   warn: [ 70]   crit: [ 90]
  tkn   warn: [ 70]   crit: [ 90]
  5h    warn: [ 70]   crit: [ 90]
  7d    warn: [ 50]   crit: [ 80]
```

- `↑↓` move between rows
- `←→` move between warn/crit fields on the same row
- Type digits to edit the value
- `Backspace` to clear
- `Esc` to go back (changes are kept in memory until saved)

Validation: warn < crit, both 0–100.

### Menu 2 — Line 2 Visibility

Three toggle rows.

```
  [x] dir
  [x] branch
  [x] worktree
```

- `↑↓` move between rows
- `Space` or `Enter` to toggle
- `Esc` to go back

## Data Flow

1. `configure.py` starts → reads `~/.claude/statusline_config.json` (or uses defaults)
2. User edits values in TUI
3. On `q` (quit): writes config back to `~/.claude/statusline_config.json`
4. `statusline.py` reads config on every invocation → applies thresholds and visibility

## Out of Scope

- Configuring line 1 field visibility
- Configuring truncation length
