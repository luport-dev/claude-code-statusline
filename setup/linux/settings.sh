    #!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SETTINGS="$SCRIPT_DIR/../settings.py"

if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 is required but not installed."
    exit 1
fi

exec python3 "$SETTINGS"
