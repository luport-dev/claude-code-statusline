#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SRC="$REPO_ROOT/scripts/statusline.py"
DEST_DIR="$HOME/.claude"
DEST="$DEST_DIR/statusline.py"

echo ">> Claude Code Status Line — Linux Setup"

# --- Python prüfen und ggf. installieren --------------------------------
PY=""
command -v python3 >/dev/null 2>&1 && PY="python3"
if [[ -z "$PY" ]]; then
    echo
    echo "   Python 3 wurde nicht gefunden."
    read -r -p "   Python 3 installieren? Paketmanager-Befehl eingeben oder Enter zum Abbrechen: " INSTALL_CMD
    if [[ -n "$INSTALL_CMD" ]]; then
        eval "$INSTALL_CMD"
        command -v python3 >/dev/null 2>&1 && PY="python3"
    fi
fi
if [[ -z "$PY" ]]; then
    echo "ERROR: Python 3 wird benoetigt. Setup abgebrochen." >&2
    echo "       z.B.: sudo apt install python3  oder  sudo dnf install python3" >&2
    exit 1
fi

# --- git prüfen ---------------------------------------------------------
if ! command -v git >/dev/null 2>&1; then
    echo "ERROR: 'git' ist erforderlich aber nicht installiert." >&2
    exit 1
fi

# --- Quelldatei prüfen --------------------------------------------------
if [[ ! -f "$SRC" ]]; then
    echo "ERROR: Quelldatei nicht gefunden: $SRC" >&2
    exit 1
fi

# --- statusline.py installieren -----------------------------------------
mkdir -p "$DEST_DIR"
cp "$SRC" "$DEST"
chmod +x "$DEST"
echo "   installed: $DEST"

# --- settings.json aktualisieren ----------------------------------------
"$PY" "$SCRIPT_DIR/../_settings.py" install
echo ">> Done. Restart Claude Code to load the status line."
