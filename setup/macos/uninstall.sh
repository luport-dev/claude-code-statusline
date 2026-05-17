#!/usr/bin/env bash
set -euo pipefail

DEST_DIR="$HOME/.claude"
DEST="$DEST_DIR/statusline.sh"
SETTINGS="$DEST_DIR/settings.json"

echo ">> Claude Code Status Line — macOS Uninstall"

if [[ -f "$DEST" ]]; then
  rm -f "$DEST"
  echo "   removed: $DEST"
else
  echo "   skipped: $DEST (not found)"
fi

if [[ -f "$SETTINGS" ]]; then
  if ! command -v jq >/dev/null 2>&1; then
    echo "WARN: 'jq' not installed — leaving $SETTINGS untouched. Remove the 'statusLine' key manually." >&2
  else
    cp "$SETTINGS" "$SETTINGS.bak.$(date +%s)"
    tmp="$(mktemp)"
    jq 'del(.statusLine)' "$SETTINGS" > "$tmp"
    mv "$tmp" "$SETTINGS"
    echo "   updated: $SETTINGS (statusLine removed)"
  fi
else
  echo "   skipped: $SETTINGS (not found)"
fi

echo ">> Done. Restart Claude Code."
