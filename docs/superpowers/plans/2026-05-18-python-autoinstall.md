# Python-Autoinstall via winget Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `setup/win/install.cmd` installiert Python 3.12 automatisch via winget, wenn Python nicht gefunden wird — nach Bestätigung durch den Benutzer.

**Architecture:** Der bestehende Python-Prüfblock in `install.cmd` wird erweitert: bei fehlendem Python erscheint eine `set /p`-Abfrage, bei Bestätigung wird `winget install` ausgeführt und Python erneut gesucht, bei Ablehnung bricht das Skript ab. `setlocal EnableDelayedExpansion` wird ergänzt, damit die Variable im `if`-Block ausgewertet werden kann.

**Tech Stack:** Windows Batch (`.cmd`), winget

---

### Task 1: Python-Prüfblock in install.cmd erweitern

**Files:**
- Modify: `setup/win/install.cmd:1-2` (setlocal-Zeile)
- Modify: `setup/win/install.cmd:13-21` (Python-Prüfblock)

- [ ] **Schritt 1: `EnableDelayedExpansion` zur setlocal-Zeile hinzufügen**

Zeile 2 in `setup/win/install.cmd` aktuell:
```bat
setlocal EnableExtensions
```
Ersetzen durch:
```bat
setlocal EnableExtensions EnableDelayedExpansion
```

- [ ] **Schritt 2: Python-Prüfblock ersetzen**

Aktueller Block (Zeilen 13–21):
```bat
rem --- Locate a Python interpreter (python or py launcher) -----------
set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY where py >nul 2>nul && set "PY=py -3"
if not defined PY (
    echo ERROR: Python 3 is required but was not found in PATH.
    echo Install from https://www.python.org/downloads/windows/ or via:
    echo     winget install -e --id Python.Python.3.12
    exit /b 1
)
```

Ersetzen durch:
```bat
rem --- Locate a Python interpreter (python or py launcher) -----------
set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY where py >nul 2>nul && set "PY=py -3"
if not defined PY (
    echo.
    echo    Python 3 wurde nicht gefunden.
    set /p "INSTALL_PY=   Jetzt Python 3.12 via winget installieren? [J/N]: "
    if /i "!INSTALL_PY!"=="J" (
        echo    Installiere Python 3.12 via winget...
        winget install -e --id Python.Python.3.12
        if errorlevel 1 (
            echo ERROR: winget-Installation fehlgeschlagen.
            exit /b 1
        )
        where python >nul 2>nul && set "PY=python"
        if not defined PY set "PY=py -3"
    ) else (
        echo ERROR: Python 3 wird benoetigt. Setup abgebrochen.
        exit /b 1
    )
)
if not defined PY (
    echo ERROR: Python 3 nach Installation nicht gefunden.
    echo        Bitte ein neues Terminal oeffnen und install.cmd erneut ausfuehren.
    exit /b 1
)
```

- [ ] **Schritt 3: Manuell testen — Python vorhanden (Normalfall)**

Szenario: Python ist im PATH verfügbar.  
Erwartetes Verhalten: Keine Änderung gegenüber vorher — Skript läuft durch ohne Abfrage.

```bat
setup\win\install.cmd
```

Erwartete Ausgabe (Auszug):
```
>> Claude Code Status Line - Windows Setup
   installed: C:\Users\<user>\.claude\statusline.py
   updated:   C:\Users\<user>\.claude\settings.json
>> Done. Restart Claude Code to load the status line.
```

- [ ] **Schritt 4: Manuell testen — Python fehlt, Benutzer bestätigt mit J**

Szenario: Python temporär aus PATH entfernen (z.B. in einem neuen `cmd`-Fenster mit `set PATH=C:\Windows\System32`), dann Skript starten und `J` eingeben.

```bat
set PATH=C:\Windows\System32
setup\win\install.cmd
```

Erwartete Ausgabe:
```
   Python 3 wurde nicht gefunden.
   Jetzt Python 3.12 via winget installieren? [J/N]: J
   Installiere Python 3.12 via winget...
[winget-Ausgabe]
   installed: ...
>> Done. Restart Claude Code to load the status line.
```

- [ ] **Schritt 5: Manuell testen — Python fehlt, Benutzer lehnt ab**

Gleiche Umgebung wie Schritt 4, diesmal `N` eingeben.

Erwartete Ausgabe:
```
   Python 3 wurde nicht gefunden.
   Jetzt Python 3.12 via winget installieren? [J/N]: N
ERROR: Python 3 wird benoetigt. Setup abgebrochen.
```
Exit-Code muss ungleich 0 sein. Prüfen mit:
```bat
echo %errorlevel%
```
Erwarteter Wert: `1`

- [ ] **Schritt 6: Committen**

```bash
git add setup/win/install.cmd
git commit -m "feat(win): Python 3.12 via winget installieren mit Benutzerbestaetigung"
```
