# 🚀 Leitstellenspiel Bot v3.7.1 - Performance & Bugfix Release

## 🚀 Was ist neu?

Version 3.7.1 ist ein Wartungsrelease, das die Bot-Geschwindigkeit erheblich verbessert und einen kritischen Fehler beim Setzen des Fahrzeugstatus behebt.

---

## ✨ NEUE FEATURES & VERBESSERUNGEN

### 🚀 Deutlich verbesserte Performance
Der Bot ist jetzt spürbar schneller und reaktionsfreudiger!
- ✅ **Dynamische Wartezeiten**: Ineffiziente, feste Wartezeiten (`time.sleep`) wurden durch intelligente, dynamische Waits (`WebDriverWait`) ersetzt.
- ✅ **Schnellere Sprechwünsche**: Die Verarbeitung von Sprechwünschen ist jetzt deutlich flotter, da unnötige Seiten-Navigationen entfernt wurden.
- ✅ **Schnelleres Laden von Fahrzeugen**: Das Nachladen von Fahrzeuglisten in der Einsatzansicht (`Mehr Fahrzeuge laden`) ist jetzt um ein Vielfaches schneller.
- ✅ **Kürzere Pausen**: Die Wartezeiten zwischen der Abarbeitung von Einsätzen wurden optimiert.

### ✅ Fehlerbehebung: Status 6 setzen
Ein langanhaltender Fehler wurde endlich behoben!
- ✅ **Problem**: Das Setzen von Fahrzeugen auf "Status 6" (Personalmangel) schlug oft fehl, da die Anfrage nicht korrekt authentifiziert war.
- ✅ **Lösung**: Die Browser-Session (Cookies) wird jetzt vor dem API-Aufruf zuverlässig synchronisiert.
- ✅ **Ergebnis**: Fahrzeuge werden jetzt **zuverlässig** auf Status 6 gesetzt, wenn sie wegen Personalmangel nicht ausrücken können.

### 📝 Deutsche Log-Ausgaben
- ✅ Diverse Log-Meldungen im GUI wurden zur besseren Verständlichkeit ins Deutsche übersetzt oder klarer formuliert.

---

## 📥 INSTALLATION

### Option 1: Standalone EXE (Empfohlen)
1. Lade `Leitstellenspiel-Bot-GUI.exe` aus diesem Release herunter.
2. Doppelklick auf die EXE.
3. Fertig! 🎉

### Option 2: Python-Version
1. Lade den Source-Code herunter (`Leitstellenspiel-Bot-v3.7.1-Release.zip`).
2. Installiere Python 3.8+.
3. Installiere Abhängigkeiten: `pip install -r requirements.txt`
4. Starte mit: `python bot_gui_new.py`

---

## 📝 CHANGELOG

Siehe [CHANGELOG.md](CHANGELOG.md) für eine vollständige Liste aller Änderungen.

---

## 🙏 DANKE

Vielen Dank an alle Nutzer für das Feedback und die Unterstützung! 🎉

---

**Version**: 3.7.1
**Release-Datum**: 2026-01-11
**Build**: Standalone EXE (Windows 64-bit)
