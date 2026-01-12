# 🛠️ Leitstellenspiel Bot v3.7.2 - Build Process Hotfix

## 🚀 Was ist neu?

Version 3.7.2 ist ein kleiner Hotfix, der kritische Probleme beim Erstellen der `.exe`-Datei behebt, die nach den Änderungen in v3.7.1 aufgetreten sind.

---

## 🐛 BUGFIXES

### ✅ Korrektur des EXE-Builds
- **Problem**: Ein Syntaxfehler (`IndentationError`) im Quellcode hat verhindert, dass die `.exe`-Datei erfolgreich erstellt werden konnte.
- **Lösung**: Der Fehler wurde gefunden und behoben. Der Build-Prozess läuft jetzt wieder fehlerfrei durch.

### ✅ Robusteres Build-Skript
- **Problem**: Das `BUILD_GUI_EXE.bat`-Skript funktionierte auf manchen Systemen nicht, weil der `python`-Befehl nicht gefunden wurde.
- **Lösung**: Das Skript wurde angepasst und verwendet jetzt den `py.exe`-Launcher, der unter Windows standardmäßig verfügbar ist.

---

## 📥 INSTALLATION

Wie immer, lade die `Leitstellenspiel-Bot-GUI.exe` aus diesem Release herunter und ersetze die alte Datei.

---

## 📝 CHANGELOG

Siehe [CHANGELOG.md](CHANGELOG.md) für eine vollständige Liste aller Änderungen.

---

**Version**: 3.7.2
**Release-Datum**: 2026-01-11
**Build**: Standalone EXE (Windows 64-bit)
