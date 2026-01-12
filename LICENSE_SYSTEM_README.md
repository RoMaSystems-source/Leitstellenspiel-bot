# 🔐 Lizenz-System - Dokumentation

## 📋 Übersicht

Das Lizenz-System schützt den Bot vor unbefugter Nutzung durch:
- **MySQL-Datenbank** Validierung
- **Hardware-ID Binding** (verhindert Sharing)
- **Offline-Grace-Period** (7 Tage)
- **Automatische Checks** alle 24h

---

## 🗄️ Datenbank-Setup

### 1. Tabelle erstellen

```bash
mysql -h 185.44.211.53 -P 3307 -u roma -p roma_portal < create_license_table.sql
```

Oder manuell:

```sql
CREATE TABLE IF NOT EXISTS licenses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    license_key VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME DEFAULT NULL,
    max_activations INT DEFAULT 1,
    current_activations INT DEFAULT 0,
    hardware_id VARCHAR(255) DEFAULT NULL,
    last_check DATETIME DEFAULT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT DEFAULT NULL
);
```

---

## 🔑 Lizenzen erstellen

### Methode 1: Python-Tool

```bash
python generate_license.py
```

**Menü**:
1. Neue Lizenz erstellen
2. Alle Lizenzen anzeigen
3. Beenden

### Methode 2: Direkt in DB

```sql
INSERT INTO licenses (license_key, email, expires_at, is_active) 
VALUES ('ABCD-1234-EFGH-5678', 'kunde@example.com', DATE_ADD(NOW(), INTERVAL 1 YEAR), TRUE);
```

---

## 📱 Nutzung (Endbenutzer)

### Erste Aktivierung

1. **Bot starten** → Lizenz-Dialog erscheint
2. **Lizenzschlüssel eingeben** (Format: `XXXX-XXXX-XXXX-XXXX`)
3. **Aktivieren** klicken
4. **Fertig!** Bot startet normal

### Lizenz-Check

- **Beim Start**: Automatisch
- **Während Betrieb**: Alle 24h
- **Bei Fehler**: 7 Tage Grace-Period (Offline-Modus)

---

## 🔧 Technische Details

### Hardware-ID

Die Hardware-ID wird automatisch generiert aus:
- System (Windows/Linux/Mac)
- Hostname
- MAC-Adresse
- Machine-ID

**Beispiel**: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`

### Lizenz-Cache

Gespeichert in: `cache/license_cache.json`

```json
{
  "license_key": "ABCD-1234-EFGH-5678",
  "hardware_id": "a1b2c3d4...",
  "valid_until": "2026-01-18T12:00:00",
  "last_check": "2026-01-11T12:00:00"
}
```

### Offline-Modus

- **Grace-Period**: 7 Tage
- **Funktionsweise**: Nutzt Cache wenn Online-Check fehlschlägt
- **Nach Ablauf**: Online-Check erforderlich

---

## 🛠️ Admin-Funktionen

### Lizenz deaktivieren

```sql
UPDATE licenses SET is_active = FALSE WHERE license_key = 'XXXX-XXXX-XXXX-XXXX';
```

### Lizenz verlängern

```sql
UPDATE licenses 
SET expires_at = DATE_ADD(NOW(), INTERVAL 1 YEAR) 
WHERE license_key = 'XXXX-XXXX-XXXX-XXXX';
```

### Hardware-ID zurücksetzen

```sql
UPDATE licenses 
SET hardware_id = NULL 
WHERE license_key = 'XXXX-XXXX-XXXX-XXXX';
```

### Alle Lizenzen anzeigen

```sql
SELECT 
    license_key, 
    email, 
    created_at, 
    expires_at, 
    is_active, 
    last_check 
FROM licenses 
ORDER BY created_at DESC;
```

---

## 🔒 Sicherheit

### Best Practices

1. **DB-Config schützen**: `db_config.json` NICHT committen!
2. **Starke Passwörter**: Für DB-Zugang
3. **SSL-Verbindung**: Für Produktiv-Umgebung
4. **Regelmäßige Backups**: Der Lizenz-Datenbank

### Dateien in .gitignore

```
db_config.json
license.key
license_cache.json
licenses.db
```

---

## 📊 Monitoring

### Aktive Lizenzen

```sql
SELECT COUNT(*) as active_licenses 
FROM licenses 
WHERE is_active = TRUE 
AND (expires_at IS NULL OR expires_at > NOW());
```

### Abgelaufene Lizenzen

```sql
SELECT license_key, email, expires_at 
FROM licenses 
WHERE expires_at < NOW() 
AND is_active = TRUE;
```

### Letzte Aktivitäten

```sql
SELECT license_key, email, last_check 
FROM licenses 
WHERE last_check IS NOT NULL 
ORDER BY last_check DESC 
LIMIT 10;
```

---

## ❓ Troubleshooting

### Problem: "Keine DB-Verbindung"

**Lösung**:
1. Prüfe `db_config.json`
2. Teste DB-Verbindung: `mysql -h HOST -P PORT -u USER -p`
3. Prüfe Firewall-Regeln

### Problem: "Lizenz an anderes Gerät gebunden"

**Lösung**:
1. Hardware-ID in DB zurücksetzen (siehe Admin-Funktionen)
2. Oder: Neue Lizenz erstellen

### Problem: "Grace-Period abgelaufen"

**Lösung**:
1. Internet-Verbindung herstellen
2. Bot neu starten
3. Online-Check wird durchgeführt

---

## 📝 Changelog

### Version 3.7.0 (2026-01-11)
- ✅ Initiales Lizenz-System
- ✅ MySQL-Datenbank Integration
- ✅ Hardware-ID Binding
- ✅ Offline-Grace-Period
- ✅ GUI-Dialog
- ✅ Admin-Tools

---

**Support**: Bei Fragen oder Problemen → GitHub Issues

