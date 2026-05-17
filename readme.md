
# Claude Code CLI Status Line

> ⚠️ **Beta**  
  This project is currently in beta. There is **no guarantee** that the scripts work correctly on every system or configuration.  
  *Use at your own risk and feel free to report issues!*

## What is it?

A two-line, colored status line for the **[Claude Code CLI](https://claude.ai/code)** that shows all relevant session data at a glance: 
- the current model (color-coded by type)
- the effort level
- context usage
- rate limits for both the 5-hour and 7-day windows
- the working directory
- the active git branch
- the active worktree (if applicable)

Colors automatically shift from green to yellow to red as defined thresholds are crossed, making critical states immediately visible without interrupting Claude's output.

## How it Works

Claude Code passes a JSON object to the status line via stdin. The script reads it, determines the git branch via `git branch --show-current` in the current working directory, and returns the formatted, colored output — Linux/macOS via `jq`, Windows natively via PowerShell `ConvertFrom-Json`.


## Examples

![Status line preview Haiku](screenshots/preview_haiku.png)

![Status line preview Sonnet](screenshots/preview_sonnet.png)

![Status line preview Opus](screenshots/preview_opus.png)

> *Example values for illustrating the color stages.*

**Line 1** — Model (colored by type), effort, thinking status, context usage, rate limits (5h / 7d)<br>
**Line 2** — Working directory, git branch, active worktree (in bronze tones)

Colors automatically shift green → yellow → red depending on usage.


## Color Scheme

| Element | Color |
|---------|-------|
| Opus | 🟡 Gold |
| Sonnet | 🔵 Light blue |
| Haiku | ⚪ White |
| thinking:on | 🟢 Teal |
| thinking:off | ⚫ Dimmed gray |
| effort / ctx / 5h / 7d (low) | 🟢 Green |
| effort / ctx / 5h / 7d (medium) | 🟡 Yellow |
| effort / ctx / 5h / 7d (high) | 🔴 Red |
| dir / branch / worktree labels | 🟤 Rust brown |
| dir / branch / worktree values | 🟠 Warm bronze |


## Thresholds

| Metric | Yellow at | Red at |
|--------|-----------|--------|
| ctx | 70% | 90% |
| 5h rate limit | 70% | 90% |
| 7d rate limit | 50% | 80% |


## Customizing

The scripts can be freely edited:

- **Change colors**: Adjust `model_color`, `effort_color`, and `color` (or `Model-Color`, `Effort-Color`, `Color-Threshold` in PowerShell). Truecolor (`38;2;R;G;B`) or [256-color ANSI codes](https://www.ditig.com/256-colors-cheat-sheet) can be used for more variety.
- **Remove fields**: Delete individual entries from the array or line composition.
- **Thresholds**: Adjust the values in the `color` calls (`warn`, `crit`).
- **Single-line**: Remove the second block (line 2).


## Files

| File | Platform |
|------|----------|
| [`scripts/linux/statusline.sh`](scripts/linux/statusline.sh) | Linux / macOS (Bash + `jq`) |
| [`scripts/win/statusline.ps1`](scripts/win/statusline.ps1) | Windows (PowerShell, no `jq` required) |
| [`scripts/win/statusline.cmd`](scripts/win/statusline.cmd) | Windows wrapper that runs `statusline.ps1` hidden |


# Requirements

| Platform | Requirements |
|----------|--------------|
| Linux | `git`, `jq` |
| macOS | `git`, `jq` |
| Windows | `git`, PowerShell 5.1+ (preinstalled) or PowerShell 7 (`pwsh`) |

<details>
<summary><strong>Linux</strong> — Installing Git and <code>jq</code></summary>

Depending on the distribution:

```bash
sudo apt install git jq        # Debian / Ubuntu / Mint
sudo dnf install git jq        # Fedora / RHEL / CentOS
sudo pacman -S git jq          # Arch / Manjaro
sudo zypper install git jq     # openSUSE
```

Verify: `git --version` and `jq --version` should both output a version number.

</details>

<details>
<summary><strong>macOS</strong> — Installing Git and <code>jq</code></summary>

Via [Homebrew](https://brew.sh):

```bash
brew install git jq
```

Alternatively, running `git --version` will prompt to install Git via the Xcode Command Line Tools. `jq` must be installed separately (Homebrew).

Verify: `git --version` and `jq --version` should both output a version number.

</details>

<details>
<summary><strong>Windows</strong> — Installing Git</summary>

> `jq` is not required on Windows — the PowerShell variant works without it.

Download and run the installer from [git-scm.com](https://git-scm.com/download/win) — Git ships with Git Bash. Alternatively via [winget](https://learn.microsoft.com/en-us/windows/package-manager/winget/):

```powershell
winget install --id Git.Git -e
```

Verify: `git --version` should output a version number.

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

Requires `git` and `jq`.

**Setup script:**

```bash
./setup/linux/install.sh      # install
./setup/linux/uninstall.sh    # uninstall
```

**Manual installation:**

Copy [`scripts/linux/statusline.sh`](scripts/linux/statusline.sh) to `~/.claude/statusline.sh` and make it executable (`chmod +x`). Then reference it in `~/.claude/settings.json` under `statusLine` as a command pointing to the absolute path (type `command`).

</details>

<details>
<summary><strong>macOS</strong></summary>

Requires `git` and `jq` (install via Homebrew: `brew install jq`).

**Setup script:**

```bash
./setup/macos/install.sh      # install
./setup/macos/uninstall.sh    # uninstall
```

**Manual installation:**

Copy [`scripts/linux/statusline.sh`](scripts/linux/statusline.sh) to `~/.claude/statusline.sh` and make it executable (`chmod +x`). Reference it in `~/.claude/settings.json` under `statusLine` as a command pointing to the absolute path (`/Users/YOUR_USERNAME/.claude/statusline.sh`, type `command`).

</details>

<details>
<summary><strong>Windows</strong></summary>

Requires `git` and PowerShell 5.1+ (preinstalled on Windows 10/11).

**Setup script** — in a regular terminal (CMD):

```cmd
setup\win\install.cmd
setup\win\uninstall.cmd
```

Or directly in PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File setup\win\install.ps1
powershell -ExecutionPolicy Bypass -File setup\win\uninstall.ps1
```

**Manual installation:**

Copy [`scripts/win/statusline.ps1`](scripts/win/statusline.ps1) and [`scripts/win/statusline.cmd`](scripts/win/statusline.cmd) together to `%USERPROFILE%\.claude\`. In `~/.claude/settings.json`, reference the `.cmd` file under `statusLine` as a command (type `command`):

```json
{
  "statusLine": {
    "type": "command",
    "command": "C:\\Users\\YOUR_USERNAME\\.claude\\statusline.cmd"
  }
}
```

> Replace `YOUR_USERNAME` with your Windows username. Backslashes in the JSON path must be doubled.

</details>
</br>


> *Restart Claude Code — the status line will be loaded on **next startup**.*


# License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
