# Release Notes v3.7.3

## 🚀 Neue Features

### Auto-Reconnect
- Bot erkennt automatisch wenn die Session abgelaufen ist
- Automatischer Re-Login nach 1 Stunde
- Bei 5 aufeinanderfolgenden Fehlern: automatischer Browser-Neustart

### Verbessertes Lizenz-System
- **Grace-Period**: 7 Tage Offline-Nutzung (war: 1 Stunde)
- **Online-Check**: Nur alle 24 Stunden (war: alle 15 Minuten)
- Neue Funktion `get_license_status_text()` für GUI-Anzeige
- Bessere Fehlermeldungen für Kunden (Ablaufdatum, verbleibende Tage)
- Lizenz-Bindung an Gerät mit Bestätigungsmeldung

## ⚡ Performance-Verbesserungen

### Fahrzeugauswahl (select_vehicles_by_checkboxes)
- Fahrzeugtyp-Mapping wird einmalig beim Start gecacht (kein Re-Create pro Einsatz)
- Alle Checkboxen werden **einmal** geladen statt mehrfach
- Vorfiltern: Nur nicht-ausgewählte Checkboxen werden verarbeitet
- Bereits gewählte Checkboxen werden aus der Liste entfernt
- Sleep-Zeiten reduziert: **0.3s → 0.15s** pro Checkbox

### Code-Qualität
- `re` und `traceback` als Top-Level-Imports (kein wiederholtes `import re` in Funktionen)
- Doppelte Imports in `license_manager.py` entfernt
- Fehlerbehandlung verbessert (bare `except` → `except Exception`)

## 🐛 Bugfixes

- **license_manager.py**: Doppelte Import-Blöcke entfernt
- **license_manager.py**: Cache Grace-Period Inkonsistenz behoben (Code stimmte nicht mit README überein)
- **bot.py**: `connect_db()` prüft jetzt ob `db_config` geladen ist bevor Verbindung versucht wird
- **bot.py**: DB-Verbindung mit `connect_timeout=10` (verhindert endloses Warten)

## 🔄 Update-System

### Automatischer Update-Check
- GUI prüft beim Start automatisch ob eine neue Version verfügbar ist
- Update-Quelle: `version.json` auf GitHub (Raw-URL)
- Bei verfügbarem Update: **orangefarbener Banner** erscheint unter dem Header
- Banner zeigt: aktuelle Version → neue Version + Changelog
- **⬇ Jetzt herunterladen** Button öffnet Download-Link im Browser
- Kann in den Einstellungen deaktiviert werden ("Automatische Updates")

## 📦 Geänderte Dateien

| Datei | Änderung |
|-------|----------|
| `bot.py` | Auto-Reconnect, Performance, Imports |
| `bot_gui_new.py` | Update-System (check_for_updates, Banner) |
| `license_manager.py` | Imports bereinigt, Grace-Period, neue Methode |
| `version.txt` | 3.7.3 |
| `version.json` | 3.7.3 |
| `TODO.md` | Alle Punkte abgehakt |
| `PERFORMANCE_OPTIMIZATION_TODO.md` | Alle Punkte abgehakt |
