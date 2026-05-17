# Claude Status Line

Displays the current status of the **Claude Code VS Code plugin** directly in the status bar: active session, model, effort level, thinking mode, and more.

## Features

- **Live status of the active session** (idle / running) with spinner icon
- **Model detection** (Opus, Sonnet, Haiku)
- **Effort level** and **thinking mode**
- **Context window size** shown in the tooltip
- **Switch sessions** by clicking the status bar item
- Refreshes every 1.5 seconds

## How it works

The extension reads the log file of the official Claude Code plugin from:

```
~/.config/Code/logs/<session>/window<N>/exthost/Anthropic.claude-code/Claude VSCode.log
```

It automatically picks the most recent log (modified within the last hour) and parses session events, model, and settings from it.

## Requirements

- VS Code `^1.90.0`
- The official **Anthropic Claude Code** plugin (`Anthropic.claude-code`) installed and actively writing logs

## Installation

### From VSIX

```bash
code --install-extension claude-status-line-extension-0.1.0.vsix
```

Or via the UI: Extensions panel → `…` → **Install from VSIX…**

### From source

```bash
cd extension
npm install
npm run compile
```

Then press `F5` inside the `extension/` folder in VS Code to launch an Extension Development Host.

## Commands

| Command | Description |
|---------|-------------|
| `Claude Status Line: Select Session` | Pick between multiple active Claude sessions |

Clicking the status bar item also opens the session picker.

## Related

The repository root also ships shell scripts for the Claude Code CLI status line (`scripts/linux/statusline.sh`, `scripts/win/statusline.ps1`).

## License

MIT — see [LICENSE](LICENSE).
