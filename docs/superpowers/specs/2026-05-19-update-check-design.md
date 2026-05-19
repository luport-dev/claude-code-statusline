# Design: Automatische Update-Prüfung

**Datum:** 2026-05-19  
**Repo:** https://github.com/luport-dev/Claude-Code-CLI-StatusLine  
**Status:** Approved

---

## Überblick

Die Statuszeile und die Settings-TUI prüfen periodisch, ob eine neue Version auf GitHub verfügbar ist. Die Prüfung läuft nicht-blockierend im Hintergrund. Das Ergebnis wird gecacht und beim nächsten Render angezeigt.

---

## Konfiguration

In `~/.claude/statusline_config.json` unter dem neuen Schlüssel `"updates"`:

```json
"updates": {
  "check": "weekly"
}
```

Gültige Werte: `"never"` | `"daily"` | `"weekly"` | `"monthly"`  
Default (wenn Schlüssel fehlt): `"weekly"`

Der Wert wird im Settings-TUI über einen neuen Menüeintrag konfiguriert.

---

## Cache-Datei

Pfad: `~/.claude/statusline_update.json`

```json
{
  "last_checked": "2026-05-19T10:00:00",
  "latest_version": "1.2.0",
  "current_version": "0.1.0",
  "update_available": true
}
```

- `last_checked`: ISO-8601 Zeitstempel der letzten erfolgreichen Prüfung
- `latest_version`: neueste Version laut GitHub API
- `current_version`: Version aus `package.json` zum Prüfzeitpunkt
- `update_available`: `true` wenn `latest_version > current_version` (semver-Vergleich)

---

## Ablauf in `statusline.py`

1. Config laden → `updates.check` lesen (Default: `"weekly"`)
2. Bei `"never"`: nichts tun
3. Cache-Datei laden; `last_checked` gegen Intervall prüfen:
   - `"daily"` → 1 Tag
   - `"weekly"` → 7 Tage
   - `"monthly"` → 30 Tage
4. Wenn Prüfung fällig: `threading.Thread(daemon=True)` starten, der:
   - `GET https://api.github.com/repos/luport-dev/Claude-Code-CLI-StatusLine/releases/latest` abruft (Timeout: 3 s)
   - `current_version` aus dem `package.json` im Repo liest (Fallback: aus Cache oder `"0.0.0"`)
   - Cache-Datei atomar schreibt
   - Bei Fehler (Netzwerk, Rate-Limit): Cache unangetastet lassen, kein Crash
5. Cache lesen (ggf. bereits vom letzten Lauf befüllt) → wenn `update_available`: Hinweis-Segment rendern

### Anzeige in der Statuszeile

Wird an das Ende von Zeile 2 angehängt (nach Worktree), nur wenn `update_available == true`:

```
⬆ v1.2.0
```

Farbe: gedimmt (weiß), kein Farbwechsel, kein Threshold.  
Die Anzeige respektiert die Einstellung `"updates": {"check": "never"}` — bei `never` wird der Cache nicht geschrieben und der Hinweis nie gezeigt.

---

## Settings-TUI — neuer Menüeintrag

`MENU_ITEMS` bekommt einen weiteren Eintrag:

```python
("Update checks", "🔄"),
```

Das zugehörige Untermenü `menu_updates()` zeigt Radio-Buttons:

```
(*) weekly    ( ) daily    ( ) monthly    ( ) never
```

Navigation: `←→` / `↑↓`, `Ent`/`Spc` wählt aus, `Esc` zurück.

### Update-Hinweis im Hauptmenü

Wenn `update_available == true` im Cache, erscheint unterhalb der Menüeinträge (vor dem Divider) eine Zeile:

```
  ⬆  Update available: v1.2.0
```

Farbe: `CP_WARN` (gelb). Kein Link (Terminal kann URLs nicht klickbar machen).

---

## Versionserkennung (`current_version`)

`current_version` wird aus `npm/package.json` → `"version"` gelesen.  
Suchpfad: ausgehend von `statusline.py` (`~/.claude/statusline.py`) wird **nicht** auf das Repo zugegriffen — stattdessen wird die Version einmalig beim Build/Install in die Cache-Datei geschrieben.

**Konkret:** `settings.py` schreibt beim Install/Update die aktuelle Version aus `package.json` in den Update-Cache:

```json
{ "current_version": "0.1.0", "last_checked": null, "latest_version": null, "update_available": false }
```

So kennt `statusline.py` die installierte Version ohne Repo-Zugriff.

---

## Fehlerbehandlung

| Szenario | Verhalten |
|---|---|
| Kein Netzwerk | Cache unverändert, kein Crash, kein Hinweis |
| GitHub API Rate-Limit (403/429) | Cache unverändert, Retry beim nächsten fälligen Intervall |
| Malformatiertes JSON in Cache | Cache wird ignoriert/neu angelegt |
| `package.json` nicht lesbar | `current_version = "0.0.0"`, Prüfung läuft trotzdem |

---

## Betroffene Dateien

| Datei | Änderung |
|---|---|
| `scripts/statusline.py` | Update-Check-Logik + Anzeige Zeile 2 |
| `setup/settings.py` | Neuer Menüeintrag + `menu_updates()` + Hinweis im Hauptmenü + Version in Cache schreiben bei Install |
| `setup/default_config.json` | `"updates": {"check": "weekly"}` hinzufügen |
| `npm/payload/statusline.py` | Sync mit `scripts/statusline.py` |
| `npm/payload/settings.py` | Sync mit `setup/settings.py` |

---

## Nicht im Scope

- Automatisches Selbst-Update (nur Hinweis, kein Download)
- Prüfung gegen npm-Registry
- Update-Hinweis in Zeile 1 der Statuszeile
