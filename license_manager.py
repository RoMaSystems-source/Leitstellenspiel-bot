"""
Lizenz-Manager für Leitstellenspiel Bot
Validiert Lizenzen gegen MySQL-Datenbank
"""

import json
import os
import sys
import time
import hashlib
import platform
import uuid
import base64
from datetime import datetime, timedelta
import pymysql
from colorama import Fore

class LicenseManager:
    def __init__(self):
        # WICHTIGE WARNUNG: Die Speicherung von Zugangsdaten im Code ist NICHT sicher.
        # Dies ist nur eine einfache Verschleierung, kein echter Schutz.
        self.db_config = self._load_db_config()
        
        self.license_cache_file = 'cache/license_cache.json'
        self.license_key = None
        self.hardware_id = self.get_hardware_id()
        
        # Grace-Period: 7 Tage Offline-Nutzung nach letztem Online-Check
        self.GRACE_PERIOD_DAYS = 7
        # Online-Check alle 24 Stunden erzwingen
        self.ONLINE_CHECK_INTERVAL_HOURS = 24
        
        # Erstelle cache-Ordner falls nicht vorhanden
        if not os.path.exists('cache'):
            os.makedirs('cache')
    
    def _load_db_config(self):
        """Lädt die verschleierte DB-Konfiguration aus der db.dat Datei."""
        try:
            # Bestimme den Pfad zur db.dat (funktioniert für Skript und .exe)
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
            
            config_path = os.path.join(base_path, 'db.dat')

            with open(config_path, 'r', encoding='utf-8') as f:
                encoded_string = f.read()

            decoded_bytes = base64.b64decode(encoded_string)
            json_string = decoded_bytes.decode('utf-8')
            return json.loads(json_string)

        except FileNotFoundError:
            print(f"{Fore.RED}FEHLER: 'db.dat' nicht gefunden!")
            print(f"{Fore.YELLOW}Bitte das Skript 'encode_config.py' ausführen, um die Datei zu erstellen.")
            return None
        except Exception as e:
            print(f"{Fore.RED}Fehler beim Laden der DB-Config aus 'db.dat': {e}")
            return None
    
    def get_hardware_id(self):
        """Generiert eindeutige Hardware-ID"""
        try:
            # Kombiniere verschiedene Hardware-Infos
            system = platform.system()
            node = platform.node()
            machine = platform.machine()
            
            # Versuche MAC-Adresse zu bekommen
            try:
                mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                               for elements in range(0,2*6,2)][::-1])
            except Exception:
                mac = "unknown"
            
            # Erstelle Hash
            hw_string = f"{system}-{node}-{machine}-{mac}"
            return hashlib.sha256(hw_string.encode()).hexdigest()[:32]
        except Exception:
            return "unknown"
    
    def connect_db(self):
        """Verbindet zur Datenbank"""
        if not self.db_config:
            print(f"{Fore.RED}FEHLER: Keine DB-Konfiguration geladen.")
            return None
        try:
            connection = pymysql.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database=self.db_config['database'],
                charset=self.db_config.get('charset', 'utf8mb4'),
                connect_timeout=10,
                cursorclass=pymysql.cursors.DictCursor
            )
            return connection
        except Exception as e:
            print(f"{Fore.RED}FEHLER: Die Datenbankverbindung konnte nicht hergestellt werden.")
            print(f"{Fore.YELLOW}Mögliche Ursachen:")
            print(f"{Fore.YELLOW}1. Die Zugangsdaten in 'db.dat' sind falsch.")
            print(f"{Fore.YELLOW}2. Der Datenbankserver ist nicht erreichbar (evtl. Firewall-Problem).")
            print(f"{Fore.YELLOW}3. Es wurde noch keine 'db.dat' erstellt. Führe 'encode_config.py' aus.")
            print(f"{Fore.CYAN}Technische Details: {e}")
            return None
    
    def validate_license_online(self, license_key):
        """Validiert Lizenz gegen Datenbank"""
        try:
            conn = self.connect_db()
            if not conn:
                return False, "Keine DB-Verbindung"
            
            with conn.cursor() as cursor:
                # Prüfe Lizenz
                sql = """
                    SELECT * FROM licenses 
                    WHERE license_key = %s 
                    AND is_active = 1
                """
                cursor.execute(sql, (license_key,))
                result = cursor.fetchone()
                
                if not result:
                    return False, "Ungültiger Lizenzschlüssel"
                
                # Prüfe Ablaufdatum
                if result.get('expires_at'):
                    expires_at = result['expires_at']
                    if isinstance(expires_at, str):
                        expires_at = datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S')
                    
                    if datetime.now() > expires_at:
                        return False, f"Lizenz abgelaufen (am {expires_at.strftime('%d.%m.%Y')})"
                
                # Prüfe Hardware-ID (falls gesetzt)
                db_hardware_id = result.get('hardware_id')
                if db_hardware_id and db_hardware_id != self.hardware_id:
                    return False, "Lizenz an anderes Gerät gebunden"
                
                # Setze Hardware-ID falls noch nicht gesetzt
                if not db_hardware_id:
                    update_sql = """
                        UPDATE licenses 
                        SET hardware_id = %s, last_check = NOW()
                        WHERE license_key = %s
                    """
                    cursor.execute(update_sql, (self.hardware_id, license_key))
                    conn.commit()
                    print(f"{Fore.GREEN}✓ Lizenz erfolgreich an dieses Gerät gebunden.")
                else:
                    # Update last_check
                    update_sql = "UPDATE licenses SET last_check = NOW() WHERE license_key = %s"
                    cursor.execute(update_sql, (license_key,))
                    conn.commit()
                
                conn.close()
                return True, "Lizenz gültig"
                
        except Exception as e:
            print(f"{Fore.RED}Lizenz-Validierung fehlgeschlagen: {e}")
            return False, str(e)
    
    def save_license_cache(self, license_key, valid_until):
        """Speichert Lizenz-Cache für Offline-Nutzung"""
        try:
            cache_data = {
                'license_key': license_key,
                'hardware_id': self.hardware_id,
                'valid_until': valid_until.isoformat(),
                'last_check': datetime.now().isoformat()
            }
            with open(self.license_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            print(f"{Fore.YELLOW}Warnung: Konnte Lizenz-Cache nicht speichern: {e}")
    
    def load_license_cache(self):
        """Lädt Lizenz-Cache"""
        try:
            if not os.path.exists(self.license_cache_file):
                return None

            with open(self.license_cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None

    def check_license(self, license_key=None, force_online=False):
        """
        Prüft Lizenz (online oder offline)

        Args:
            license_key: Lizenzschlüssel (optional, wird aus Cache geladen falls None)
            force_online: Erzwingt Online-Check

        Returns:
            (bool, str): (Gültig, Nachricht)
        """
        # Lade aus Cache falls kein Key angegeben
        if not license_key:
            cache = self.load_license_cache()
            if cache:
                license_key = cache.get('license_key')

            if not license_key:
                return False, "Kein Lizenzschlüssel gefunden"

        # Prüfe Cache
        cache = self.load_license_cache()

        # Online-Check wenn:
        # - force_online = True
        # - Kein Cache vorhanden
        # - Cache älter als ONLINE_CHECK_INTERVAL_HOURS (24h)
        # - Hardware-ID stimmt nicht überein
        need_online_check = force_online

        if cache:
            # Prüfe Hardware-ID
            if cache.get('hardware_id') != self.hardware_id:
                return False, "Lizenz an anderes Gerät gebunden"

            # Prüfe Alter des Cache
            try:
                last_check = datetime.fromisoformat(cache.get('last_check', ''))
                cache_age = datetime.now() - last_check

                if cache_age > timedelta(hours=self.ONLINE_CHECK_INTERVAL_HOURS):
                    need_online_check = True
                    print(f"{Fore.YELLOW}⚠ Lizenz-Cache älter als {self.ONLINE_CHECK_INTERVAL_HOURS}h - Online-Check erforderlich")
            except Exception:
                need_online_check = True
        else:
            need_online_check = True

        # Online-Check
        if need_online_check:
            valid, message = self.validate_license_online(license_key)

            if valid:
                # Speichere Cache mit 7-Tage Grace-Period
                valid_until = datetime.now() + timedelta(days=self.GRACE_PERIOD_DAYS)
                self.save_license_cache(license_key, valid_until)
                self.license_key = license_key
                return True, "Lizenz gültig (Online-Check)"
            else:
                # Online-Check fehlgeschlagen - Grace-Period nur zulassen, wenn nicht erzwungen
                if cache and not force_online:
                    try:
                        valid_until = datetime.fromisoformat(cache.get('valid_until', ''))
                        if datetime.now() < valid_until:
                            remaining = valid_until - datetime.now()
                            remaining_days = remaining.days
                            print(f"{Fore.YELLOW}⚠ Online-Check fehlgeschlagen, nutze Cache (noch {remaining_days} Tag(e) Grace-Period)")
                            self.license_key = license_key
                            return True, f"Lizenz gültig (Offline-Modus, noch {remaining_days} Tag(e))"
                        else:
                            return False, "Grace-Period abgelaufen - Internetverbindung erforderlich"
                    except Exception:
                        pass

                return False, message

        # Offline-Check (Cache)
        if cache:
            try:
                valid_until = datetime.fromisoformat(cache.get('valid_until', ''))
                if datetime.now() < valid_until:
                    remaining = valid_until - datetime.now()
                    self.license_key = license_key
                    return True, f"Lizenz gültig (Offline-Cache, noch {remaining.days} Tag(e))"
                else:
                    return False, "Grace-Period abgelaufen - Online-Check erforderlich"
            except Exception:
                return False, "Ungültiger Cache"

        return False, "Keine gültige Lizenz gefunden"

    def get_license_info(self):
        """Gibt Lizenz-Informationen zurück"""
        try:
            if not self.license_key:
                cache = self.load_license_cache()
                if cache:
                    self.license_key = cache.get('license_key')

            if not self.license_key:
                return None

            conn = self.connect_db()
            if not conn:
                return None

            with conn.cursor() as cursor:
                sql = "SELECT * FROM licenses WHERE license_key = %s"
                cursor.execute(sql, (self.license_key,))
                result = cursor.fetchone()
                conn.close()
                return result
        except Exception:
            return None

    def get_license_status_text(self):
        """Gibt einen lesbaren Status-Text zurück (für GUI)"""
        cache = self.load_license_cache()
        if not cache:
            return "Keine Lizenz aktiviert", False
        
        license_key = cache.get('license_key', '')
        masked_key = license_key[:4] + "****" + license_key[-4:] if len(license_key) >= 8 else "****"
        
        try:
            valid_until = datetime.fromisoformat(cache.get('valid_until', ''))
            if datetime.now() < valid_until:
                remaining = valid_until - datetime.now()
                return f"Lizenz aktiv ({masked_key}) - noch {remaining.days} Tag(e)", True
            else:
                return f"Lizenz abgelaufen ({masked_key})", False
        except Exception:
            return "Lizenz-Status unbekannt", False
