# 🔧 Leitstellenspiel Bot - Version 3.6.0

## 🎯 KRITISCHE BUGFIXES

Diese Version behebt **3 wichtige Bugs** für bessere Stabilität und Funktionalität!

---

## 🐛 Bugfixes

### 1. ✅ "Mehr laden" Button mehrfach klicken
**Problem**: Der "Mehr Fahrzeuge laden" Button wurde nur 1x geklickt, wodurch nicht alle verfügbaren Fahrzeuge geladen wurden.

**Lösung**: 
- Button wird jetzt in einer Schleife geklickt bis alle Fahrzeuge geladen sind (max 10x)
- Besseres Logging zeigt wie viele Klicks durchgeführt wurden
- Automatische Erkennung wenn alle Fahrzeuge geladen sind

**Ergebnis**: Alle verfügbaren Fahrzeuge werden jetzt korrekt geladen! ✅

---

### 2. ✅ Update-Check mehrfach während Bot läuft
**Problem**: Update-Check wurde nur beim Start durchgeführt, nicht während der Bot läuft.

**Lösung**: 
- Update-Check jetzt alle 10 Zyklen (~5 Minuten bei 30s Intervall)
- Funktioniert sowohl im Standalone- als auch im GUI-Modus
- Automatisches Update und Neustart wenn neue Version verfügbar

**Ergebnis**: Bot erkennt Updates automatisch während er läuft! ✅

---

### 3. ✅ Fahrzeuge auf Status 6 setzen bei Personalmangel
**Problem**: Fahrzeuge wurden nicht auf Status 6 (außer Dienst wegen Personalmangel) gesetzt wenn die Alarmierung fehlschlug.

**Lösung**: 
- Detailliertes Logging in `set_vehicle_status()` Funktion
- Längere Wartezeit (0.5s) nach Alarmieren-Button für stabilere Erkennung
- Debug-Ausgaben für HTTP-Response und JSON-Antworten
- Erfolgs-/Fehler-Meldungen für jedes Fahrzeug

**Ergebnis**: Fahrzeuge werden jetzt korrekt auf Status 6 gesetzt! ✅

---

## 🔧 Verbesserungen

- **Logging**: Bessere Debug-Ausgaben für Status-Änderungen
- **Stabilität**: Robustere Fehlerbehandlung
- **Performance**: Optimierte Wartezeiten

---

## 📥 Installation

1. **Download**: `Leitstellenspiel-Bot-GUI.exe` herunterladen
2. **Ausführen**: Doppelklick auf die `.exe` Datei
3. **Konfigurieren**: Benutzername und Passwort eingeben
4. **Starten**: Bot starten und genießen! 🎉

---

## 🔄 Update von älteren Versionen

Der Bot hat **Auto-Update** eingebaut:
- Beim Start wird automatisch auf Updates geprüft
- Während der Bot läuft wird alle ~5 Minuten auf Updates geprüft
- Bei verfügbarem Update wird automatisch heruntergeladen und installiert
- Bot startet sich automatisch neu

**Manuelles Update**:
1. Alte Version schließen
2. Neue `Leitstellenspiel-Bot-GUI.exe` herunterladen
3. Alte Datei ersetzen
4. Neue Version starten

---

## ⚙️ Systemanforderungen

- **OS**: Windows 10/11
- **RAM**: Mindestens 2 GB
- **Internet**: Stabile Verbindung erforderlich
- **Browser**: Chrome/Edge (wird automatisch installiert)

---

## 📝 Changelog

Vollständiges Changelog: [CHANGELOG.md](https://github.com/DEIN_USERNAME/DEIN_REPO/blob/main/CHANGELOG.md)

---

## 🐛 Bug Reports & Feature Requests

Probleme oder Wünsche? Erstelle ein [Issue auf GitHub](https://github.com/DEIN_USERNAME/DEIN_REPO/issues)!

---

## 📜 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert.

---

**Viel Spaß mit Version 3.6.0!** 🚀

