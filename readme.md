
# Claude Code CLI Status Line

A two-line, colored status line for the [Claude Code CLI](https://claude.ai/code) that shows all relevant session data at a glance: the current model (color-coded by type), the effort level, context usage, and rate limits for both the 5-hour and 7-day windows. The second line displays the working directory, the active git branch, and — if applicable — the active worktree.

Colors automatically shift from green to yellow to red as defined thresholds are crossed, making critical states immediately visible without interrupting Claude's output.

## Preview

![Status line preview Haiku](screenshots/preview_haiku.png)

![Status line preview Sonnet](screenshots/preview_sonnet.png)

![Status line preview Opus](screenshots/preview_opus.png)

> *Example values for illustrating the color stages — context:73% (warning), 5h:92% (critical), 5h:0% (low/green).*

**Line 1** — Model (colored by type), effort, thinking status, context usage, rate limits (5h / 7d)
**Line 2** — Working directory, git branch, active worktree (in bronze tones)

Colors automatically shift green → yellow → red depending on usage.

## Files

| File | Platform |
|------|----------|
| [`scripts/linux/statusline.sh`](scripts/linux/statusline.sh) | Linux / macOS (Bash + `jq`) |
| [`scripts/win/statusline.ps1`](scripts/win/statusline.ps1) | Windows (PowerShell, no `jq` required) |
| [`scripts/win/statusline.cmd`](scripts/win/statusline.cmd) | Windows wrapper that runs `statusline.ps1` hidden |

## Requirements

| Platform | Requirements |
|----------|--------------|
| Linux | `git`, `jq` |
| macOS | `git`, `jq` |
| Windows | `git`, PowerShell 5.1+ (preinstalled) or PowerShell 7 (`pwsh`) |

### Installing Git

**Windows**: Download and run the installer from [git-scm.com](https://git-scm.com/download/win) — Git ships with Git Bash. Alternatively via [winget](https://learn.microsoft.com/en-us/windows/package-manager/winget/):

```powershell
winget install --id Git.Git -e
```

**macOS** (via [Homebrew](https://brew.sh)):

```bash
brew install git
```

Alternatively, running `git --version` will prompt to install via the Xcode Command Line Tools.

**Linux** — depending on the distribution:

```bash
sudo apt install git           # Debian / Ubuntu / Mint
sudo dnf install git           # Fedora / RHEL / CentOS
sudo pacman -S git             # Arch / Manjaro
sudo zypper install git        # openSUSE
```

Verify: `git --version` should output a version number.

### Installing `jq`

> Only required on Linux/macOS — the Windows variant works without `jq`.

**macOS** (via [Homebrew](https://brew.sh)):

```bash
brew install jq
```

**Linux** — depending on the distribution:

```bash
sudo apt install jq            # Debian / Ubuntu / Mint
sudo dnf install jq            # Fedora / RHEL / CentOS
sudo pacman -S jq              # Arch / Manjaro
sudo zypper install jq         # openSUSE
```

Verify: `jq --version` should output a version number.

## Installing the Status Line

Each platform has two variants: **Manual** (you do it yourself) or **Prompt** (let Claude Code do it for you — run from the repo root).

### Linux

#### Manual Installation

Copy [`scripts/linux/statusline.sh`](scripts/linux/statusline.sh) to `~/.claude/statusline.sh` and make it executable (`chmod +x`). Then reference it in `~/.claude/settings.json` under `statusLine` as a command pointing to the absolute path (type `command`).

#### Prompt for Claude Code

```
Copy the file `scripts/linux/statusline.sh` to `~/.claude/statusline.sh`, make it executable, and add it to `~/.claude/settings.json` under `statusLine` as a command (`type: "command"`) using the absolute path. Create `settings.json` if it doesn't exist, and merge `statusLine` without overwriting existing keys.
```

### macOS

#### Manual Installation

Copy [`scripts/linux/statusline.sh`](scripts/linux/statusline.sh) to `~/.claude/statusline.sh` and make it executable (`chmod +x`). Reference it in `~/.claude/settings.json` under `statusLine` as a command pointing to the absolute path (`/Users/YOUR_USERNAME/.claude/statusline.sh`, type `command`).

> Note: `jq` is not preinstalled on macOS — install it via Homebrew first (`brew install jq`).

#### Prompt for Claude Code

```
Make sure `jq` is installed (install via Homebrew if not). Copy `scripts/linux/statusline.sh` to `~/.claude/statusline.sh`, make it executable, and add it to `~/.claude/settings.json` under `statusLine` as a command (`type: "command"`) using the absolute macOS path. Create `settings.json` if it doesn't exist, and merge `statusLine` without overwriting existing keys.
```

### Windows

#### Manual Installation

Copy [`scripts/win/statusline.ps1`](scripts/win/statusline.ps1) and [`scripts/win/statusline.cmd`](scripts/win/statusline.cmd) together to `%USERPROFILE%\.claude\`. In `%APPDATA%\Claude\settings.json`, reference the `.cmd` file under `statusLine` as a command (type `command`):

```json
{
  "statusLine": {
    "type": "command",
    "command": "C:\\Users\\YOUR_USERNAME\\.claude\\statusline.cmd"
  }
}
```

> Replace `YOUR_USERNAME` with your Windows username. Backslashes in the JSON path must be doubled.

#### Prompt for Claude Code

```
Copy `scripts/win/statusline.ps1` and `scripts/win/statusline.cmd` to `%USERPROFILE%\.claude\` (create the folder if needed). In `%APPDATA%\Claude\settings.json`, add the full path to `statusline.cmd` under `statusLine` as a command (`type: "command"`), escaping backslashes in the JSON. Create `settings.json` if it doesn't exist, and merge `statusLine` without overwriting existing keys.
```

### Finally

Restart Claude Code — the status line will be loaded on next startup.

## Color Scheme

| Element | Color |
|---------|-------|
| Opus | Gold |
| Sonnet | Light blue |
| Haiku | White |
| thinking:on | Teal |
| thinking:off | Dimmed gray |
| effort / ctx / 5h / 7d (low) | Green |
| effort / ctx / 5h / 7d (medium) | Yellow |
| effort / ctx / 5h / 7d (high) | Red |
| dir / branch / worktree labels | Rust brown |
| dir / branch / worktree values | Warm bronze |

## Thresholds

| Metric | Yellow at | Red at |
|--------|-----------|--------|
| ctx | 70% | 90% |
| 5h rate limit | 70% | 90% |
| 7d rate limit | 50% | 80% |

## Customizing

The scripts can be freely edited:

- **Change colors**: Adjust `model_color`, `effort_color`, and `color` (or `Model-Color`, `Effort-Color`, `Color-Threshold` in PowerShell). Truecolor (`38;2;R;G;B`) or [256-color ANSI codes](https://www.ditig.com/256-colors-cheat-sheet).
- **Remove fields**: Delete individual entries from the array or line composition.
- **Thresholds**: Adjust the values in the `color` calls (`warn`, `crit`).
- **Single-line**: Remove the second block (line 2).

## How it Works

Claude Code passes a JSON object to the status line via stdin. The script reads it, determines the git branch via `git branch --show-current` in the current working directory, and returns the formatted, colored output — Linux/macOS via `jq`, Windows natively via PowerShell `ConvertFrom-Json`.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
