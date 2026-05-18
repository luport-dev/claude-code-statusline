#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SRC="$REPO_ROOT/scripts/linux/statusline.sh"
DEST_DIR="$HOME/.claude"
DEST="$DEST_DIR/statusline.sh"
SETTINGS="$DEST_DIR/settings.json"

echo ">> Claude Code Status Line — macOS Setup"

if ! command -v git >/dev/null 2>&1; then
  echo "ERROR: 'git' is required. Install via Xcode Command Line Tools or Homebrew." >&2
  exit 1
fi
if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: 'jq' is required. Install via Homebrew: 'brew install jq'." >&2
  exit 1
fi
if [[ ! -f "$SRC" ]]; then
  echo "ERROR: source file not found: $SRC" >&2
  exit 1
fi

mkdir -p "$DEST_DIR"
cp "$SRC" "$DEST"
chmod +x "$DEST"
echo "   installed: $DEST"

if [[ -f "$SETTINGS" ]]; then
  cp "$SETTINGS" "$SETTINGS.bak.$(date +%s)"
  tmp="$(mktemp)"
  jq --arg cmd "$DEST" '.statusLine = {type:"command", command:$cmd}' "$SETTINGS" > "$tmp"
  mv "$tmp" "$SETTINGS"
else
  jq -n --arg cmd "$DEST" '{statusLine:{type:"command", command:$cmd}}' > "$SETTINGS"
fi
echo "   updated:   $SETTINGS"

# Default-Config anlegen (nur bei Erstinstallation)
CONFIG_DEST="$HOME/.claude/statusline_config.json"
CONFIG_SRC="$REPO_ROOT/setup/default_config.json"
if [[ ! -f "$CONFIG_DEST" && -f "$CONFIG_SRC" ]]; then
  cp "$CONFIG_SRC" "$CONFIG_DEST"
  echo "   installed: $CONFIG_DEST (default config)"
fi

echo ">> Done. Restart Claude Code to load the status line."
