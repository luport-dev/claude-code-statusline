# Claude Code CLI Statuszeile

Eine zweizeilige, farbige Statuszeile für die [Claude Code CLI](https://claude.ai/code), die auf einen Blick alle relevanten Sitzungsdaten anzeigt: das aktuelle Modell (farblich nach Typ hervorgehoben), den Effort-Level, die Kontextauslastung sowie die Rate-Limits für das 5-Stunden- und 7-Tage-Fenster. Die zweite Zeile zeigt das Arbeitsverzeichnis, den aktiven Git-Branch und — sofern vorhanden — den aktiven Worktree.

Die Farben wechseln automatisch von Grün über Gelb nach Rot, sobald definierte Schwellenwerte überschritten werden, sodass kritische Zustände sofort erkennbar sind — ohne die Ausgabe von Claude zu unterbrechen.

## Vorschau

![Statuszeile Vorschau Haiku](screenshots/preview_haiku.png)

![Statuszeile Vorschau Sonnet](screenshots/preview_sonnet.png)

![Statuszeile Vorschau Opus](screenshots/preview_opus.png)


> *Beispielwerte zur Veranschaulichung der Farbstufen — context:73% (Warnung), 5h:92% (Kritisch), 5h:0% (niedrig/grün).*

**Zeile 1** — Modell (farbig nach Typ), Effort, Thinking-Status, Kontext-Auslastung, Rate-Limits (5h / 7d)
**Zeile 2** — Arbeitsverzeichnis, Git-Branch, aktiver Worktree (in Bronze-Tönen)

Farben wechseln automatisch grün → gelb → rot je nach Auslastung.

## Dateien

| Datei | Plattform |
|-------|-----------|
| [`scripts/linux/statusline.sh`](scripts/linux/statusline.sh) | Linux / macOS (Bash + `jq`) |
| [`scripts/win/statusline.ps1`](scripts/win/statusline.ps1) | Windows (PowerShell, kein `jq` nötig) |
| [`scripts/win/statusline.cmd`](scripts/win/statusline.cmd) | Windows-Wrapper, der `statusline.ps1` versteckt ausführt |

## Voraussetzungen

| Plattform | Voraussetzungen |
|-----------|----------------|
| Linux | `git`, `jq` |
| macOS | `git`, `jq` |
| Windows | `git`, PowerShell 5.1+ (vorinstalliert) oder PowerShell 7 (`pwsh`) |

### Git installieren

**Windows**: Installer von [git-scm.com](https://git-scm.com/download/win) herunterladen und ausführen — Git wird inklusive Git Bash mitgeliefert. Alternativ via [winget](https://learn.microsoft.com/en-us/windows/package-manager/winget/):

```powershell
winget install --id Git.Git -e
```

**macOS** (via [Homebrew](https://brew.sh)):

```bash
brew install git
```

Alternativ wird Git nach dem Aufruf von `git --version` automatisch über die Xcode Command Line Tools angeboten.

**Linux** — je nach Distribution:

```bash
sudo apt install git           # Debian / Ubuntu / Mint
sudo dnf install git           # Fedora / RHEL / CentOS
sudo pacman -S git             # Arch / Manjaro
sudo zypper install git        # openSUSE
```

Prüfen: `git --version` sollte eine Versionsnummer ausgeben.

### `jq` installieren

> Nur für Linux/macOS erforderlich — die Windows-Variante kommt ohne `jq` aus.

**macOS** (via [Homebrew](https://brew.sh)):

```bash
brew install jq
```

**Linux** — je nach Distribution:

```bash
sudo apt install jq            # Debian / Ubuntu / Mint
sudo dnf install jq            # Fedora / RHEL / CentOS
sudo pacman -S jq              # Arch / Manjaro
sudo zypper install jq         # openSUSE
```

Prüfen: `jq --version` sollte eine Versionsnummer ausgeben.

## Installation der Statuszeile

Jede Plattform hat zwei Varianten: **Manuell** (du machst es selbst) oder **Prompt** (du lässt Claude Code es für dich erledigen — vom Repo-Root ausführen).

### Linux

#### Manuelle Installation

[`scripts/linux/statusline.sh`](scripts/linux/statusline.sh) nach `~/.claude/statusline.sh` kopieren und ausführbar machen (`chmod +x`). Anschließend in `~/.claude/settings.json` unter `statusLine` als Command auf den absoluten Pfad verweisen (Typ `command`).

#### Prompt für Claude Code

```
Kopiere die Datei `scripts/linux/statusline.sh` nach `~/.claude/statusline.sh`, mache sie ausführbar und trage sie in `~/.claude/settings.json` unter `statusLine` als Command (`type: "command"`) mit dem absoluten Pfad ein. Lege `settings.json` an, falls sie nicht existiert, und füge `statusLine` mergend hinzu, ohne bestehende Keys zu überschreiben.
```

### macOS

#### Manuelle Installation

[`scripts/linux/statusline.sh`](scripts/linux/statusline.sh) nach `~/.claude/statusline.sh` kopieren und ausführbar machen (`chmod +x`). In `~/.claude/settings.json` unter `statusLine` als Command auf den absoluten Pfad (`/Users/DEIN_USERNAME/.claude/statusline.sh`) verweisen (Typ `command`).

> Hinweis: `jq` ist auf macOS nicht vorinstalliert — vorher per Homebrew installieren (`brew install jq`).

#### Prompt für Claude Code

```
Stelle sicher, dass `jq` installiert ist (sonst per Homebrew nachinstallieren). Kopiere `scripts/linux/statusline.sh` nach `~/.claude/statusline.sh`, mache sie ausführbar und trage sie in `~/.claude/settings.json` unter `statusLine` als Command (`type: "command"`) mit dem absoluten macOS-Pfad ein. Lege `settings.json` an, falls sie nicht existiert, und füge `statusLine` mergend hinzu, ohne bestehende Keys zu überschreiben.
```

### Windows

#### Manuelle Installation

[`scripts/win/statusline.ps1`](scripts/win/statusline.ps1) und [`scripts/win/statusline.cmd`](scripts/win/statusline.cmd) gemeinsam nach `%USERPROFILE%\.claude\` kopieren. In `%APPDATA%\Claude\settings.json` unter `statusLine` als Command auf die `.cmd`-Datei verweisen (Typ `command`):

```json
{
  "statusLine": {
    "type": "command",
    "command": "C:\\Users\\DEIN_USERNAME\\.claude\\statusline.cmd"
  }
}
```

> `DEIN_USERNAME` durch deinen Windows-Benutzernamen ersetzen. Backslashes im JSON-Pfad müssen doppelt geschrieben werden.

#### Prompt für Claude Code

```
Kopiere `scripts/win/statusline.ps1` und `scripts/win/statusline.cmd` nach `%USERPROFILE%\.claude\` (Ordner anlegen falls nötig). Trage in `%APPDATA%\Claude\settings.json` unter `statusLine` als Command (`type: "command"`) den vollen Pfad zur `statusline.cmd` ein (Backslashes im JSON doppelt escapen). Lege `settings.json` an, falls sie nicht existiert, und füge `statusLine` mergend hinzu, ohne bestehende Keys zu überschreiben.
```

### Abschließend

Claude Code neu starten — die Statuszeile wird beim nächsten Start geladen.

## Farbschema

| Element | Farbe |
|---------|-------|
| Opus | Gold |
| Sonnet | Hellblau |
| Haiku | Weiß |
| thinking:on | Türkis |
| thinking:off | Gedimmtes Grau |
| effort / ctx / 5h / 7d (niedrig) | Grün |
| effort / ctx / 5h / 7d (mittel) | Gelb |
| effort / ctx / 5h / 7d (hoch) | Rot |
| dir / branch / worktree Labels | Rostbraun |
| dir / branch / worktree Werte | Warmes Bronze |

## Schwellenwerte

| Metrik | Gelb ab | Rot ab |
|--------|---------|--------|
| ctx | 70% | 90% |
| 5h Rate-Limit | 70% | 90% |
| 7d Rate-Limit | 50% | 80% |

## Anpassen

Die Scripte können frei bearbeitet werden:

- **Farben ändern**: `model_color`, `effort_color` und `color` (bzw. `Model-Color`, `Effort-Color`, `Color-Threshold` in PowerShell) anpassen. Truecolor (`38;2;R;G;B`) oder [256-Farben ANSI-Codes](https://www.ditig.com/256-colors-cheat-sheet).
- **Felder entfernen**: Einzelne Einträge aus dem Array bzw. der Zeilen-Komposition entfernen.
- **Schwellenwerte**: Werte in den `color`-Aufrufen anpassen (`warn`, `crit`).
- **Einzeilig**: Den zweiten Block (Zeile 2) entfernen.

## Funktionsweise

Claude Code übergibt der Statuszeile ein JSON-Objekt über stdin. Das Script liest es ein, ermittelt den Git-Branch via `git branch --show-current` im aktuellen Arbeitsverzeichnis und gibt die formatierte, farbige Ausgabe zurück — Linux/macOS via `jq`, Windows nativ via PowerShell `ConvertFrom-Json`.
