#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST_DIR="$HOME/.claude"
DEST="$DEST_DIR/statusline.py"

echo ">> Claude Code Status Line — Linux Uninstall"

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
    echo "ERROR: Python 3 wird benoetigt. Uninstall abgebrochen." >&2
    echo "       z.B.: sudo apt install python3  oder  sudo dnf install python3" >&2
    exit 1
fi

# --- statusline.py entfernen --------------------------------------------
if [[ -f "$DEST" ]]; then
    rm -f "$DEST"
    echo "   removed: $DEST"
else
    echo "   skipped: $DEST (not found)"
fi

# --- settings.json bereinigen -------------------------------------------
"$PY" "$SCRIPT_DIR/../_install_helper.py" uninstall
echo ">> Done. Restart Claude Code."
