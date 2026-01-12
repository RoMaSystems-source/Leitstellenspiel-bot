# 🔧 Version 3.6.0 - Kritische Bugfixes

## 🎯 Was ist neu?

Diese Version behebt **3 wichtige Bugs** für bessere Stabilität und Funktionalität!

## 🐛 Bugfixes

### ✅ "Mehr laden" Button mehrfach klicken
- **Problem**: Button wurde nur 1x geklickt → nicht alle Fahrzeuge geladen
- **Fix**: Button wird jetzt in Schleife geklickt bis alle Fahrzeuge geladen sind (max 10x)
- **Ergebnis**: Alle verfügbaren Fahrzeuge werden korrekt geladen!

### ✅ Update-Check während Bot läuft
- **Problem**: Update-Check nur beim Start
- **Fix**: Update-Check jetzt alle 10 Zyklen (~5 Minuten bei 30s Intervall)
- **Ergebnis**: Bot erkennt Updates automatisch während er läuft!

### ✅ Status 6 bei Personalmangel
- **Problem**: Fahrzeuge wurden nicht auf Status 6 gesetzt
- **Fix**: Besseres Logging, längere Wartezeit, detaillierte Debug-Ausgaben
- **Ergebnis**: Fahrzeuge werden korrekt auf Status 6 gesetzt!

## 🔧 Verbesserungen

- Bessere Debug-Ausgaben für Status-Änderungen
- Robustere Fehlerbehandlung
- Optimierte Wartezeiten

## 📥 Installation

1. Download `Leitstellenspiel-Bot-GUI.exe`
2. Doppelklick auf die `.exe` Datei
3. Benutzername und Passwort eingeben
4. Bot starten! 🎉

## 🔄 Auto-Update

Der Bot hat Auto-Update eingebaut - einfach starten und er aktualisiert sich selbst!

## 📝 Vollständiges Changelog

Siehe [CHANGELOG.md](https://github.com/DEIN_USERNAME/DEIN_REPO/blob/main/CHANGELOG.md)

---

**Viel Spaß mit Version 3.6.0!** 🚀

