# 🚨 Leitstellenspiel Bot

Automatischer Bot für Leitstellenspiel.de mit modernem GUI

## 🚀 Schnellstart

### Option 1: Mit Python (Entwicklung)

1. **Installiere Abhängigkeiten:**
```bash
pip install -r requirements.txt
```

2. **Starte das GUI:**
```bash
python bot_gui_new.py
```
oder
```bash
START_GUI.bat
```

3. **Konfiguriere im GUI:**
   - Gehe zum Tab "Einstellungen"
   - Trage Email und Passwort ein
   - Passe Intervall und Max. Einsätze an
   - Klicke "EINSTELLUNGEN SPEICHERN"

4. **Starte den Bot:**
   - Gehe zum Tab "Dashboard"
   - Klicke "BOT STARTEN"

### Option 2: Mit EXE (Portable)

1. **Erstelle EXE:**
```bash
BUILD_GUI_EXE.bat
```

2. **Starte:**
   - `dist/Leitstellenspiel-Bot-GUI.exe`
   - Konfiguriere alles im GUI
   - Fertig!

## 📁 Projektstruktur

```
Leitstellenspiel bot/
├── cache/                      # Alle Daten (automatisch erstellt)
│   ├── settings.json          # GUI-Einstellungen
│   ├── mission_cache.json     # Einsatz-Datenbank
│   └── bot.log                # Logs
│
├── bot.py                     # Haupt-Bot
├── bot_gui_new.py             # Modernes GUI
├── vehicle_types.py           # Fahrzeugtypen
│
├── config.json.example        # Beispiel-Config (für Bot ohne GUI)
├── requirements.txt           # Python-Abhängigkeiten
│
└── *.bat                      # Starter-Skripte
```

## ⚙️ Features

- ✅ **Modernes GUI** mit Tab-System
- ✅ **Keine Config-Datei** nötig - alles im GUI
- ✅ **Auto-Alarmierung** von Einsätzen
- ✅ **Live-Logs** im GUI
- ✅ **Statistiken** in Echtzeit
- ✅ **Cache-System** für schnellere Verarbeitung
- ✅ **Headless Mode** - Browser unsichtbar

## 🛠️ Entwicklung

### Batch-Dateien

- `START_GUI.bat` - Startet das GUI
- `START_BOT.bat` - Startet den Bot (Konsole)
- `BUILD_GUI_EXE.bat` - Erstellt GUI-EXE
- `BUILD_EXE.bat` - Erstellt Bot-EXE
- `SETUP.bat` - Installiert Abhängigkeiten
- `CONFIG_BEARBEITEN.bat` - Öffnet Config
- `LOGS_ANZEIGEN.bat` - Zeigt Logs

### Abhängigkeiten

```
requests>=2.31.0
beautifulsoup4>=4.12.0
selenium>=4.39.0
customtkinter>=5.2.0
pillow>=10.0.0
colorama>=0.4.6
pyinstaller>=6.10.0
```

## 📝 Einstellungen

Alle Einstellungen werden im GUI-Tab "Einstellungen" gemacht:

- **Email** - Dein Leitstellenspiel-Login
- **Passwort** - Dein Passwort
- **Check-Intervall** - Sekunden zwischen Checks (Standard: 30)
- **Max. Einsätze** - Pro Durchlauf (Standard: 10)
- **Headless Mode** - Browser unsichtbar
- **Auto-Alarmierung** - Automatisch alarmieren
- **Auto-Nachalarmierung** - Automatisch nachalarmieren

## 🎯 Verwendung

1. Starte das GUI
2. Gehe zu "Einstellungen"
3. Trage deine Daten ein
4. Speichere die Einstellungen
5. Gehe zu "Dashboard"
6. Klicke "BOT STARTEN"
7. Beobachte die Logs und Statistiken

## 🔒 Sicherheit

- Alle sensiblen Daten in `cache/` (wird nicht ins Git committed)
- Passwörter werden lokal gespeichert
- Keine Daten werden an Dritte gesendet

## 📦 Distribution

Für die Weitergabe:

1. Erstelle EXE: `BUILD_GUI_EXE.bat`
2. Gib weiter: `dist/Leitstellenspiel-Bot-GUI.exe`
3. Fertig - keine Config nötig!

## 🐛 Troubleshooting

**Bot startet nicht:**
- Prüfe Email/Passwort in den Einstellungen
- Schaue in die Logs (Tab "Dashboard")

**Keine Einsätze gefunden:**
- Prüfe ob du eingeloggt bist
- Erhöhe das Check-Intervall

**EXE funktioniert nicht:**
- Installiere Python-Abhängigkeiten neu
- Lösche `build/` und `dist/` Ordner
- Erstelle EXE neu

## 📄 Lizenz

Privates Projekt - Keine Lizenz

## 🤝 Support

Bei Fragen oder Problemen:
- Schaue in die Logs: `cache/bot.log`
- Prüfe die Einstellungen im GUI

