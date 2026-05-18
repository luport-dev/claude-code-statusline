# Design: Python-Autoinstall via winget in install.cmd

**Datum:** 2026-05-18  
**Status:** Genehmigt

## Ziel

Wenn Python beim Ausführen von `setup/win/install.cmd` nicht gefunden wird, soll der Benutzer gefragt werden, ob Python 3.12 automatisch via `winget` installiert werden soll. Bei Ablehnung bricht das Skript mit einer klaren Fehlermeldung ab.

## Betroffene Datei

`setup/win/install.cmd`

## Änderung

Der bestehende Python-Prüfblock wird erweitert:

1. Python wird wie bisher via `where python` und `where py` gesucht.
2. Wird Python nicht gefunden, erscheint eine interaktive Abfrage:  
   `Python 3 wurde nicht gefunden. Jetzt Python 3.12 via winget installieren? [J/N]:`
3. Bei Bestätigung (`J`/`j`): `winget install -e --id Python.Python.3.12` wird ausgeführt.
   - Schlägt winget fehl → Abbruch mit Fehlermeldung.
   - Danach wird Python erneut im PATH gesucht.
   - Wird Python immer noch nicht gefunden (PATH noch nicht aktualisiert) → Hinweis, neues Terminal zu öffnen, und Abbruch.
4. Bei Ablehnung (`N` oder andere Eingabe): Abbruch mit der Meldung  
   `ERROR: Python 3 wird benoetigt. Setup abgebrochen.`

## Technische Details

- `setlocal EnableDelayedExpansion` wird ergänzt, damit `!INSTALL_PY!` innerhalb des `if`-Blocks ausgewertet wird.
- Der `set /p`-Vergleich nutzt `/i` (case-insensitiv); nur der erste Buchstabe `J` wird akzeptiert.
- Python-Version: `Python.Python.3.12` (winget-ID, unveränderlich).
- Keine neuen Dateien, keine neuen Abhängigkeiten.

## Nicht im Scope

- Automatische PATH-Aktualisierung nach winget (erfordert Shell-Neustart).
- Installation anderer Python-Versionen.
- Fallback auf `choco` oder andere Paketmanager.
