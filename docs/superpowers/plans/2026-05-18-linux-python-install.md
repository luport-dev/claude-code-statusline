# Linux Python Install Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die Linux-Installation auf Python umstellen, `statusline.py` als cross-platform gemeinsames Skript etablieren und `_settings.py` in einen gemeinsamen `setup/`-Ordner verschieben.

**Architecture:** `scripts/statusline.py` ersetzt `scripts/win/statusline.py` und `scripts/linux/statusline.sh` als einzige, plattformunabhängige Status-Line-Implementierung. `setup/_settings.py` ersetzt `setup/win/_settings.py` und wird von beiden Plattform-Installern referenziert. `setup/linux/install.sh` und `uninstall.sh` werden durch Python-basierte `.sh`-Wrapper ersetzt, die analog zu Windows mit Benutzerbestätigung Python installieren (Hinweis auf Paketmanager, kein automatischer Install da kein einheitlicher Linux-Paketmanager).

**Tech Stack:** Python 3, Bash, Windows Batch (.cmd)

---

## Dateistruktur nach Abschluss

```
scripts/
  statusline.py          ← NEU (verschoben aus scripts/win/statusline.py)
  linux/
    statusline.sh        ← GELÖSCHT
  win/
    statusline.py        ← GELÖSCHT

setup/
  _settings.py           ← NEU (verschoben aus setup/win/_settings.py)
  linux/
    install.sh           ← GEÄNDERT (Python-basiert, kein jq mehr)
    uninstall.sh         ← GEÄNDERT (Python-basiert, kein jq mehr)
  win/
    _settings.py         ← GELÖSCHT
    install.cmd          ← GEÄNDERT (Pfad auf scripts/statusline.py)
    uninstall.cmd        ← GEÄNDERT (Pfad auf scripts/statusline.py, setup/_settings.py)
```

---

### Task 1: `statusline.py` nach `scripts/` verschieben

**Files:**
- Verschieben: `scripts/win/statusline.py` → `scripts/statusline.py`
- Löschen: `scripts/win/statusline.py`
- Löschen: `scripts/linux/statusline.sh`

- [ ] **Schritt 1: `scripts/statusline.py` erstellen**

Inhalt ist identisch mit `scripts/win/statusline.py`. Datei kopieren:

```bash
cp scripts/win/statusline.py scripts/statusline.py
```

- [ ] **Schritt 2: Verifizieren — Skript läuft auf Linux**

```bash
echo '{"cwd":"/tmp","model":{"display_name":"Claude Sonnet 4.6"},"effort":{"level":"medium"},"context_window":{"used_percentage":42},"rate_limits":{"five_hour":{"used_percentage":10},"seven_day":{"used_percentage":5}}}' | python3 scripts/statusline.py
```

Erwartete Ausgabe: Zweizeilige ANSI-farbige Status-Line ohne Fehler.

- [ ] **Schritt 3: Alte Dateien löschen**

```bash
git rm scripts/win/statusline.py
git rm scripts/linux/statusline.sh
```

- [ ] **Schritt 4: Neue Datei stagen und committen**

```bash
git add scripts/statusline.py
git commit -m "refactor: statusline.py als cross-platform Skript unter scripts/"
```

---

### Task 2: `_settings.py` nach `setup/` verschieben

**Files:**
- Verschieben: `setup/win/_settings.py` → `setup/_settings.py`
- Löschen: `setup/win/_settings.py`

- [ ] **Schritt 1: `setup/_settings.py` erstellen**

```bash
cp setup/win/_settings.py setup/_settings.py
```

- [ ] **Schritt 2: Verifizieren — Skript läuft**

```bash
python3 setup/_settings.py install
python3 setup/_settings.py uninstall
```

Erwartete Ausgabe bei `install`: `updated: ~/.claude/settings.json` (oder `backup:` + `updated:`).  
Erwartete Ausgabe bei `uninstall`: `updated:` oder `skipped:`.

- [ ] **Schritt 3: Alte Datei löschen**

```bash
git rm setup/win/_settings.py
```

- [ ] **Schritt 4: Stagen und committen**

```bash
git add setup/_settings.py
git commit -m "refactor: _settings.py als gemeinsames Setup-Skript unter setup/"
```

---

### Task 3: `setup/win/install.cmd` und `uninstall.cmd` auf neue Pfade anpassen

**Files:**
- Modify: `setup/win/install.cmd`
- Modify: `setup/win/uninstall.cmd`

- [ ] **Schritt 1: Pfad zu `statusline.py` in `install.cmd` anpassen**

In `setup/win/install.cmd` aktuell:
```bat
set "SRC=%REPO_ROOT%\scripts\win\statusline.py"
```
Ersetzen durch:
```bat
set "SRC=%REPO_ROOT%\scripts\statusline.py"
```

- [ ] **Schritt 2: Pfad zu `_settings.py` in `install.cmd` anpassen**

In `setup/win/install.cmd` aktuell:
```bat
%PY% "%SCRIPT_DIR%_settings.py" install
```
Ersetzen durch:
```bat
%PY% "%SCRIPT_DIR%.._settings.py" install
```

- [ ] **Schritt 3: Pfad zu `_settings.py` in `uninstall.cmd` anpassen**

In `setup/win/uninstall.cmd` aktuell:
```bat
%PY% "%SCRIPT_DIR%_settings.py" uninstall
```
Ersetzen durch:
```bat
%PY% "%SCRIPT_DIR%.._settings.py" uninstall
```

- [ ] **Schritt 4: Stagen und committen**

```bash
git add setup/win/install.cmd setup/win/uninstall.cmd
git commit -m "fix(win): Pfade auf gemeinsame statusline.py und _settings.py anpassen"
```

---

### Task 4: `setup/linux/install.sh` auf Python umstellen

**Files:**
- Modify: `setup/linux/install.sh`

Die neue Version ersetzt `jq` durch `python3` + `setup/_settings.py`. Bei fehlendem Python3 erscheint eine Abfrage — da es keinen einheitlichen Linux-Paketmanager gibt, wird nur ein Hinweis ausgegeben und abgebrochen wenn der Nutzer ablehnt.

- [ ] **Schritt 1: `setup/linux/install.sh` vollständig ersetzen**

```bash
cat > setup/linux/install.sh << 'EOF'
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
EOF
chmod +x setup/linux/install.sh
```

- [ ] **Schritt 2: Verifizieren — Syntaxprüfung**

```bash
bash -n setup/linux/install.sh
```

Erwartete Ausgabe: keine (kein Fehler).

- [ ] **Schritt 3: Stagen und committen**

```bash
git add setup/linux/install.sh
git commit -m "feat(linux): install.sh auf Python umgestellt, jq-Abhängigkeit entfernt"
```

---

### Task 5: `setup/linux/uninstall.sh` auf Python umstellen

**Files:**
- Modify: `setup/linux/uninstall.sh`

- [ ] **Schritt 1: `setup/linux/uninstall.sh` vollständig ersetzen**

```bash
cat > setup/linux/uninstall.sh << 'EOF'
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
"$PY" "$SCRIPT_DIR/../_settings.py" uninstall
echo ">> Done. Restart Claude Code."
EOF
chmod +x setup/linux/uninstall.sh
```

- [ ] **Schritt 2: Verifizieren — Syntaxprüfung**

```bash
bash -n setup/linux/uninstall.sh
```

Erwartete Ausgabe: keine (kein Fehler).

- [ ] **Schritt 3: Stagen und committen**

```bash
git add setup/linux/uninstall.sh
git commit -m "feat(linux): uninstall.sh auf Python umgestellt, jq-Abhängigkeit entfernt"
```

---

### Task 6: `_settings.py` — Pfad zu `statusline.py` für Linux anpassen

**Files:**
- Modify: `setup/_settings.py`

Der generierte `command`-Wert in `status_line_command()` muss auf `scripts/statusline.py` zeigen (nicht mehr `scripts/win/statusline.py`). Außerdem muss `SCRIPT` plattformabhängig gesetzt werden: unter Windows `statusline.py`, unter Linux `statusline.py` (gleicher Name, aber anderer Pfad).

- [ ] **Schritt 1: `SCRIPT`-Pfad und `status_line_command()` in `setup/_settings.py` anpassen**

Aktuell in `setup/_settings.py`:
```python
CLAUDE_DIR = Path.home() / ".claude"
SETTINGS = CLAUDE_DIR / "settings.json"
SCRIPT = CLAUDE_DIR / "statusline.py"


def status_line_command() -> str:
    # Forward slashes: Git Bash (the shell Claude Code routes through on
    # Windows when present) treats backslashes as escapes and will eat them.
    # See https://code.claude.com/docs/en/statusline#windows-configuration
    script_posix = str(SCRIPT).replace("\\", "/")
    return f"python {script_posix}"
```

Ersetzen durch:
```python
import platform

CLAUDE_DIR = Path.home() / ".claude"
SETTINGS = CLAUDE_DIR / "settings.json"
SCRIPT = CLAUDE_DIR / "statusline.py"


def status_line_command() -> str:
    if platform.system() == "Windows":
        # Forward slashes: Git Bash treats backslashes as escapes.
        script_posix = str(SCRIPT).replace("\\", "/")
        return f"python {script_posix}"
    return f"python3 {SCRIPT}"
```

- [ ] **Schritt 2: Verifizieren**

```bash
python3 -c "
import sys; sys.argv = ['_settings.py', 'install']
import importlib.util, pathlib
spec = importlib.util.spec_from_file_location('s', 'setup/_settings.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
print(m.status_line_command())
"
```

Erwartete Ausgabe (Linux): `python3 /home/<user>/.claude/statusline.py`

- [ ] **Schritt 3: Stagen und committen**

```bash
git add setup/_settings.py
git commit -m "fix: status_line_command() plattformabhaengig (python3 auf Linux)"
```

---

### Task 7: Integrations-Smoke-Test auf Linux

**Files:** keine Änderungen

- [ ] **Schritt 1: Vollständigen Install-Flow testen**

```bash
bash setup/linux/install.sh
```

Erwartete Ausgabe:
```
>> Claude Code Status Line — Linux Setup
   installed: /home/<user>/.claude/statusline.py
   backup:    /home/<user>/.claude/settings.json.bak.<timestamp>  (falls vorhanden)
   updated:   /home/<user>/.claude/settings.json
>> Done. Restart Claude Code to load the status line.
```

- [ ] **Schritt 2: settings.json prüfen**

```bash
python3 -c "import json; d=json.load(open('$HOME/.claude/settings.json')); print(d['statusLine'])"
```

Erwartete Ausgabe:
```python
{'type': 'command', 'command': 'python3 /home/<user>/.claude/statusline.py'}
```

- [ ] **Schritt 3: statusline.py direkt testen**

```bash
echo '{"cwd":"'"$PWD"'","model":{"display_name":"Claude Sonnet 4.6"},"effort":{"level":"medium"},"context_window":{"used_percentage":55},"rate_limits":{"five_hour":{"used_percentage":20},"seven_day":{"used_percentage":10}}}' | python3 ~/.claude/statusline.py
```

Erwartete Ausgabe: Zweizeilige ANSI-farbige Status-Line.

- [ ] **Schritt 4: Uninstall-Flow testen**

```bash
bash setup/linux/uninstall.sh
```

Erwartete Ausgabe:
```
>> Claude Code Status Line — Linux Uninstall
   removed: /home/<user>/.claude/statusline.py
   backup:  /home/<user>/.claude/settings.json.bak.<timestamp>
   updated: /home/<user>/.claude/settings.json (statusLine removed)
>> Done. Restart Claude Code.
```

- [ ] **Schritt 5: Abschließend committen (falls nötig)**

Wenn alle Tests bestanden: kein weiterer Commit nötig — alle Änderungen sind bereits committed.
