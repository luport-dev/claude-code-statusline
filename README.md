
# Claude Code CLI Status Line

> ⚠️ **Beta**  
  This project is currently in beta. There is **no guarantee** that the scripts work correctly on every system or configuration.  
  *Use at your own risk and feel free to report issues!*

## What is it?

A two-line, colored status line for the **[Claude Code CLI](https://claude.ai/code)** that shows all relevant session data at a glance:
- the current model (color-coded by type)
- the effort level
- thinking mode status
- context usage and token count
- rate limits for both the 5-hour and 7-day windows
- the working directory
- the active git branch
- the active worktree (if applicable)

Each metric can be shown as text, a coloured bar, both, or hidden. Colors automatically shift from green → yellow → red as configured thresholds are crossed, making critical states immediately visible without interrupting Claude's output.

Every segment can be prefixed with either a compact emoji (🤖 💪 🧠 📦 🪙 🕔 📅 / 📁 ⎇ 🌳) or a word label, and bar glyphs are switchable between four styles — all configurable via an interactive TUI.

## How it Works

Claude Code passes a JSON object to the status line via stdin. The script reads it, determines the git branch via `git branch --show-current` in the current working directory, and returns the formatted, colored output — implemented in Python 3 (standard library only) and works on Linux, macOS, and Windows.


## Examples

![Status line preview Haiku](screenshots/preview_haiku.png)

![Status line preview Sonnet](screenshots/preview_sonnet.png)

![Status line preview Opus](screenshots/preview_opus.png)

> *Example values for illustrating the color stages.*

**Line 1** — Model (colored by type), effort, thinking status, context usage (`ctx`), token count (`tkn`), rate limits (5h / 7d)<br>
**Line 2** — Working directory, git branch, active worktree (in bronze tones, truncated to fit terminal width)

Colors automatically shift green → yellow → red depending on usage.


## Color Scheme

| Element | Color |
|---------|-------|
| Opus | 🟡 Gold |
| Sonnet | 🔵 Light blue |
| Haiku | ⚪ White |
| thinking:on | 🟢 Teal |
| thinking:off | ⚫ Dimmed gray |
| effort / ctx / tkn / 5h / 7d (low) | 🟢 Green |
| effort / ctx / tkn / 5h / 7d (medium) | 🟡 Yellow |
| effort / ctx / tkn / 5h / 7d (high) | 🔴 Red |
| dir / branch / worktree labels | 🟤 Rust brown |
| dir / branch / worktree values | 🟠 Warm bronze |


## Display modes

Each line 1 metric can be rendered in one of four modes (`text` / `bar` / `both` / `off`):

| Mode | Example (ctx at 42%) |
|------|----------------------|
| `text` | `ctx: 42%` |
| `bar` | `ctx ▰▰▰▰▱▱▱▱▱▱` |
| `both` | `ctx ▰▰▰▰▱▱▱▱▱▱ 42%` |
| `off` | *(hidden)* |

Defaults: `ctx`, `5h`, `7d` use `both`; everything else uses `text`.


## Decoration: emoji or label

A single global switch controls whether every segment (on both lines) is prefixed with an **emoji** or a **word label**:

| Segment | Emoji | Label |
|---------|-------|-------|
| model | 🤖 | `model` |
| effort | 💪 | `effort` |
| thinking | 🧠 | `thinking` |
| ctx | 📦 | `ctx` |
| tkn | 🪙 | `tkn` |
| 5h | 🕔 | `5h` |
| 7d | 📅 | `7d` |
| dir | 📁 | `dir` |
| branch | ⎇ | `branch` |
| worktree | 🌳 | `worktree` |

Default: `emoji`.


## Bar style

When a metric is shown as a bar (`bar` or `both` mode), the glyphs are configurable:

| Style | Filled | Empty | Look |
|-------|--------|-------|------|
| `fill` *(default)* | ▰ | ▱ | Subtle, slightly rounded |
| `block` | █ | ░ | Strong contrast, classic |
| `dot` | ● | ○ | Battery-indicator style |
| `square` | ■ | □ | Clean, geometric |


## Thresholds

Default thresholds (configurable via `settings`):

| Metric | Yellow at | Red at |
|--------|-----------|--------|
| ctx | 60% | 80% |
| tkn | 60% | 80% |
| 5h rate limit | 60% | 80% |
| 7d rate limit | 60% | 80% |


## Settings

Run the interactive settings TUI to customize thresholds, display modes, decoration, bar style, and element visibility:

```bash
# Linux
./setup/linux/settings.sh

# macOS
./setup/macos/settings.sh
```

```cmd
# Windows (CMD)
setup\win\settings.cmd
```

All settings are saved to `~/.claude/statusline_config.json`.

> On Windows, `windows-curses` is installed automatically by `install.cmd`.

**Main menu**
```
┌──────────────── Claude Code Status Line — Configuration ──────────────────┐
│                                                                           │
│  > 1. Metrics visibility                                                  │
│    2. Metrics thresholds                                                  │
│    3. Git visibility                                                      │
│    4. Decoration (emoji/label)                                            │
│    5. Bar style                                                           │
│                                                                           │
│             config: ~/.claude/statusline_config.json                      │
│                                                                           │
│  [↑↓] navigate  [Enter] open  [q] save & quit  [Esc] quit without saving  │
└───────────────────────────────────────────────────────────────────────────┘
```

**Metrics visibility** — per-metric display mode
```
┌────────────────────────── Metric display ──────────────────────────┐
│                                                                    │
│   selected model: Sonnet 4.6                                       │
│                                                                    │
│   metric    bar       text      both      off                      │
│                                                                    │
│   model     ( )       (*)       ( )       ( )                      │
│   effort    ( )       (*)       ( )       ( )                      │
│   thinking  ( )       (*)       ( )       ( )                      │
│   ctx       ( )       ( )       (*)       ( )                      │
│   tkn       ( )       (*)       ( )       ( )                      │
│   5h        ( )       ( )       (*)       ( )                      │
│   7d        ( )       ( )       (*)       ( )                      │
│                                                                    │
│   [↑↓] metric  [←→] mode  [b/t/o/h] set  [Esc] back                │
└────────────────────────────────────────────────────────────────────┘
```

**Thresholds**
```
┌──────────────────────────────────────────────────────────────────────┐
│                              Thresholds                              │
│                                                                      │
│  ctx   warn: [ 60]%          crit: [ 80]%                            │
│  tkn   warn: [ 60]%          crit: [ 80]%                            │
│  5h    warn: [ 60]%          crit: [ 80]%                            │
│  7d    warn: [ 60]%          crit: [ 80]%                            │
│                                                                      │
│  [↑↓] rows  [←→] fields  [0-9] edit  [Backspace] clear  [Esc] back   │
└──────────────────────────────────────────────────────────────────────┘
```

**Git visibility** (line 2)
```
┌───────────────────────────────────────────────────┐
│                   Git visibility                  │
│                                                   │
│  [x] dir                                          │
│  [x] branch                                       │
│  [x] worktree                                     │
│                                                   │
│  [↑↓] navigate  [Space/Enter] toggle  [Esc] back  │
└───────────────────────────────────────────────────┘
```

**Decoration**
```
┌──────────────────────── Decoration ─────────────────────────┐
│                                                             │
│   Prefix shown in front of each segment (all display modes):│
│                                                             │
│     (*) emoji   (🤖 💪 🧠 📦 🪙 🕔 📅)                       │
│     ( ) label   (model effort thinking ctx tkn 5h 7d)       │
│                                                             │
│   [↑↓] choose  [Enter/Space] select  [Esc] back             │
└─────────────────────────────────────────────────────────────┘
```

**Bar style**
```
┌──────────────────────── Bar style ──────────────────────────┐
│                                                             │
│   Glyphs used for filled / empty bar segments:              │
│                                                             │
│     (*) fill     ▰▰▰▰▰▱▱▱▱▱   (default)                     │
│     ( ) block    █████░░░░░                                 │
│     ( ) dot      ●●●●●○○○○○                                 │
│     ( ) square   ■■■■■□□□□□                                 │
│                                                             │
│   [↑↓] choose  [Enter/Space] select  [Esc] back             │
└─────────────────────────────────────────────────────────────┘
```


## Files

| File | Description |
|------|-------------|
| [`scripts/statusline.py`](scripts/statusline.py) | Status line script (all platforms) |
| [`setup/_settings.py`](setup/_settings.py) | Shared settings helper |
| [`setup/settings.py`](setup/settings.py) | Interactive configuration TUI |
| [`setup/default_config.json`](setup/default_config.json) | Default configuration (copied on first install) |
| [`setup/linux/install.sh`](setup/linux/install.sh) | Linux install |
| [`setup/linux/settings.sh`](setup/linux/settings.sh) | Linux settings |
| [`setup/macos/install.sh`](setup/macos/install.sh) | macOS install |
| [`setup/macos/settings.sh`](setup/macos/settings.sh) | macOS settings |
| [`setup/win/install.cmd`](setup/win/install.cmd) | Windows install |
| [`setup/win/settings.cmd`](setup/win/settings.cmd) | Windows settings |


# Requirements

| Platform | Requirements |
|----------|--------------|
| Linux | `git`, Python 3.8+ |
| macOS | `git`, Python 3.8+ |
| Windows | `git`, Python 3.8+ (installed automatically by `install.cmd` if missing) |

<details>
<summary><strong>Linux</strong> — Installing Git and Python</summary>

Depending on the distribution:

```bash
sudo apt install git python3        # Debian / Ubuntu / Mint
sudo dnf install git python3        # Fedora / RHEL / CentOS
sudo pacman -S git python            # Arch / Manjaro
sudo zypper install git python3     # openSUSE
```

Verify: `git --version` and `python3 --version` should both output a version number.

</details>

<details>
<summary><strong>macOS</strong> — Installing Git and Python</summary>

Via [Homebrew](https://brew.sh):

```bash
brew install git python
```

Alternatively, running `git --version` will prompt to install Git via the Xcode Command Line Tools. Python can also be installed from [python.org](https://www.python.org/downloads/mac-osx/).

Verify: `git --version` and `python3 --version` should both output a version number.

</details>

<details>
<summary><strong>Windows</strong> — Installing Git and Python</summary>

Install Git from [git-scm.com](https://git-scm.com/download/win). Python 3 is installed automatically by `install.cmd` via winget if not already present. Alternatively, install manually:

```powershell
winget install --id Git.Git -e
winget install --id Python.Python.3.12 -e
```

> When installing Python, make sure **"Add python.exe to PATH"** is checked.

Verify: `git --version` and `python --version` (or `py --version`) should both output a version number.

</details>
<br>


# Installing the Status Line

The fastest way: **clone the repo** and **run the setup script** for your platform.  
It copies the right files to `~/.claude/` and merges the `statusLine` entry into `settings.json` (existing files are backed up as `.bak.<timestamp>`).

```bash
git clone https://github.com/luport-dev/Claude-Code-CLI-StatusLine.git
cd Claude-Code-CLI-StatusLine
```

<details>
<summary><strong>Linux</strong></summary>

Requires `git` and Python 3.

**Setup scripts:**

```bash
./setup/linux/install.sh      # install
./setup/linux/uninstall.sh    # uninstall
./setup/linux/settings.sh    # configure thresholds & visibility
```

**Manual installation:**

Copy [`scripts/statusline.py`](scripts/statusline.py) to `~/.claude/statusline.py`. Then reference it in `~/.claude/settings.json` under `statusLine`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 /home/YOUR_USERNAME/.claude/statusline.py"
  }
}
```

</details>

<details>
<summary><strong>macOS</strong></summary>

Requires `git` and Python 3.

**Setup scripts:**

```bash
./setup/macos/install.sh      # install
./setup/macos/uninstall.sh    # uninstall
./setup/macos/settings.sh    # configure thresholds & visibility
```

**Manual installation:**

Copy [`scripts/statusline.py`](scripts/statusline.py) to `~/.claude/statusline.py`. Reference it in `~/.claude/settings.json` under `statusLine`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 /Users/YOUR_USERNAME/.claude/statusline.py"
  }
}
```

</details>

<details>
<summary><strong>Windows</strong></summary>

Requires `git`. Python 3 is installed automatically if missing.

**Setup scripts** — in a regular terminal (CMD):

```cmd
setup\win\install.cmd      rem install
setup\win\uninstall.cmd    rem uninstall
setup\win\settings.cmd    rem configure thresholds & visibility
```

The install script copies `statusline.py` to `%USERPROFILE%\.claude\statusline.py` and merges the `statusLine` entry into `settings.json` (existing files are backed up as `.bak.<timestamp>`). It also installs `windows-curses` so the configuration TUI works.

**Manual installation:**

Copy [`scripts/statusline.py`](scripts/statusline.py) to `%USERPROFILE%\.claude\statusline.py`. In `~/.claude/settings.json`, reference it under `statusLine`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "python C:/Users/YOUR_USERNAME/.claude/statusline.py"
  }
}
```

> Replace `YOUR_USERNAME` with your Windows username. **Use forward slashes** in the path — Claude Code routes status line commands through Git Bash on Windows when present, and backslashes get eaten as escape characters. See the [official docs](https://code.claude.com/docs/en/statusline#windows-configuration).

</details>
</br>


> *Restart Claude Code — the status line will be loaded on **next startup**.*


# License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
