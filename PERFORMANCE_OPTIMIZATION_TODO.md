# Leitstellenspiel Bot Performance Optimierungen

## ✅ Abgeschlossen (v3.7.3)

- [x] TODO-Datei erstellt
- [x] 1. Reduziere Selenium Wait Times & Sleeps
- [x] 2. Optimiere Fahrzeugauswahl-Logik
- [x] 3. Cache mehr API-Daten
- [x] 4. Minimiere Seiten-Neuladungen
- [x] 5. Batch Fahrzeug-Status-Updates
- [x] 6. Stromlinie Einsatzverarbeitung
- [x] 7. Verwende schnellere Selektoren
- [x] 8. Reduziere Browser-Interaktionen

## 📋 Umgesetzte Details

### 1. Reduzierte Sleep-Zeiten
- Checkbox-Klick: 0.3s → 0.15s
- Scroll-Pause: 0.2s → entfernt (direkt klicken)

### 2. Fahrzeugauswahl-Optimierung
- Fahrzeugtyp-Mapping einmalig in `__init__` gecacht (kein Re-Create pro Einsatz)
- Alle Checkboxen EINMAL laden statt mehrfach
- Vorfiltern: Nur nicht-ausgewählte Checkboxen verarbeiten
- Bereits gewählte Checkboxen aus Liste entfernen (kein Doppel-Check)

### 3. API-Daten-Caching
- `api_vehicles` und `api_buildings` werden gecacht
- Mission-Cache: 24h Gültigkeit

### 4. Session-Management
- Automatischer Reconnect nach 1h
- Auto-Neustart bei 5 aufeinanderfolgenden Fehlern
- Session-Check vor jedem Zyklus

### 5. Lizenz-System
- Grace-Period: 7 Tage (war: 1h)
- Online-Check-Intervall: 24h (war: 15min)
- Neue Methode: get_license_status_text() für GUI-Anzeige
