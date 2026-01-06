#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Leitstellenspiel.de Bot - Modernes GUI
Professionelles Interface mit CustomTkinter - ALLES IN EINER DATEI!
"""

import customtkinter as ctk
import threading
import queue
import time
from datetime import datetime, timedelta
import json
import sys
import os
import random

# Bot imports
import requests
from bs4 import BeautifulSoup
import logging
from colorama import init, Fore, Style
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, NoAlertPresentException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from vehicle_types import VEHICLE_TYPES, CATEGORY_TO_TYPES

# Colorama initialisieren
init(autoreset=True)

# CustomTkinter Einstellungen
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def random_delay(min_seconds=0.5, max_seconds=2.0):
    """Wartet eine zufällige Zeit (Anti-Ban)"""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)

class LeitstellenspielBot:
    def __init__(self, config_path='config.json'):
        """Initialisiert den Bot mit der Konfiguration"""
        # Bestimme den richtigen Pfad (für .exe und normale Ausführung)
        if getattr(sys, 'frozen', False):
            # Läuft als .exe
            base_path = sys._MEIPASS
        else:
            # Läuft als Python-Skript
            base_path = os.path.dirname(os.path.abspath(__file__))

        # Erstelle Cache-Ordner
        self.cache_dir = 'cache'
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

        # Config-Pfad anpassen
        if not os.path.isabs(config_path):
            config_path = os.path.join(base_path, config_path)

        self.config = self.load_config(config_path)
        self.session = requests.Session()
        self.driver = None
        self.base_url = 'https://www.leitstellenspiel.de'
        self.setup_logging()
        self.logged_in = False
        self.mission_cache = {}
        self.mission_cache_file = os.path.join(self.cache_dir, 'mission_cache.json')
        self.mission_cache_age = None

        # API-Daten Cache
        self.api_vehicles = []
        self.api_buildings = []
        self.api_vehicle_types = {}  # Mapping von vehicle_type ID zu Name
        
    def load_config(self, config_path):
        """Lädt die Konfigurationsdatei"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"{Fore.RED}Fehler: config.json nicht gefunden!")
            print(f"{Fore.YELLOW}Bitte kopieren Sie config.json.example zu config.json und tragen Sie Ihre Daten ein.")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Fehler beim Lesen der config.json: {e}")
            sys.exit(1)
    
    def setup_logging(self):
        """Richtet das Logging-System ein"""
        # Hole Logging-Konfiguration mit Defaults
        logging_config = self.config.get('logging', {})
        log_level = getattr(logging, logging_config.get('level', 'INFO'), logging.INFO)
        log_file = os.path.join(self.cache_dir, logging_config.get('file', 'bot.log'))

        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def init_browser(self, headless=True):
        """Initialisiert den Selenium-Browser"""
        try:
            self.logger.info(f"{Fore.CYAN}Initialisiere Browser...")

            # Versuche Chrome mit automatischem ChromeDriver
            try:
                from selenium.webdriver.chrome.service import Service
                from selenium.webdriver.chrome.options import Options

                chrome_options = Options()
                if headless:
                    chrome_options.add_argument('--headless=new')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--window-size=1920,1080')
                chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
                chrome_options.add_experimental_option('useAutomationExtension', False)

                # Versuche mit automatischem ChromeDriver Management
                try:
                    from selenium.webdriver.chrome.service import Service as ChromeService
                    from webdriver_manager.chrome import ChromeDriverManager

                    service = ChromeService(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    self.logger.info(f"{Fore.GREEN}✓ Chrome-Browser gestartet (mit webdriver-manager)")
                except ImportError:
                    # Fallback: Ohne webdriver-manager
                    self.driver = webdriver.Chrome(options=chrome_options)
                    self.logger.info(f"{Fore.GREEN}✓ Chrome-Browser gestartet")

                return True

            except Exception as e:
                self.logger.warning(f"{Fore.YELLOW}Chrome nicht verfügbar: {e}")

                # Versuche Firefox
                try:
                    from selenium.webdriver.firefox.service import Service as FirefoxService
                    from selenium.webdriver.firefox.options import Options as FirefoxOptions

                    firefox_options = FirefoxOptions()
                    if headless:
                        firefox_options.add_argument('--headless')
                    firefox_options.add_argument('--disable-gpu')

                    # Versuche mit automatischem GeckoDriver Management
                    try:
                        from webdriver_manager.firefox import GeckoDriverManager

                        service = FirefoxService(GeckoDriverManager().install())
                        self.driver = webdriver.Firefox(service=service, options=firefox_options)
                        self.logger.info(f"{Fore.GREEN}✓ Firefox-Browser gestartet (mit webdriver-manager)")
                    except ImportError:
                        # Fallback: Ohne webdriver-manager
                        self.driver = webdriver.Firefox(options=firefox_options)
                        self.logger.info(f"{Fore.GREEN}✓ Firefox-Browser gestartet")

                    return True

                except Exception as e2:
                    self.logger.error(f"{Fore.RED}Firefox nicht verfügbar: {e2}")
                    self.logger.error(f"{Fore.RED}Kein Browser verfügbar!")
                    self.logger.error(f"{Fore.YELLOW}Tipp: Installiere 'pip install webdriver-manager' für automatisches Driver-Management")
                    return False

        except Exception as e:
            self.logger.error(f"{Fore.RED}Fehler beim Initialisieren des Browsers: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

    def close_browser(self):
        """Schließt den Browser"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info(f"{Fore.CYAN}Browser geschlossen")
            except:
                pass

    def load_mission_cache(self):
        """Lädt den Mission-Cache aus der Datei"""
        try:
            if os.path.exists(self.mission_cache_file):
                with open(self.mission_cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    self.mission_cache = cache_data.get('missions', {})
                    self.mission_cache_age = cache_data.get('timestamp', 0)

                    # Prüfe Alter des Cache (24 Stunden)
                    cache_age_hours = (time.time() - self.mission_cache_age) / 3600
                    if cache_age_hours > 24:
                        self.logger.info(f"{Fore.YELLOW}Mission-Cache ist {cache_age_hours:.1f}h alt - wird aktualisiert")
                        self.mission_cache = {}
                    else:
                        self.logger.info(f"{Fore.GREEN}✓ Mission-Cache geladen ({len(self.mission_cache)} Einsätze, {cache_age_hours:.1f}h alt)")
        except Exception as e:
            self.logger.warning(f"{Fore.YELLOW}Konnte Mission-Cache nicht laden: {e}")
            self.mission_cache = {}

    def update_mission_cache(self):
        """Aktualisiert den Mission-Cache von der API"""
        try:
            self.logger.info(f"{Fore.CYAN}Lade Einsatz-Datenbank von API...")
            response = self.session.get(f'{self.base_url}/einsaetze.json')

            if response.status_code == 200:
                missions_data = response.json()

                # Konvertiere zu Dictionary mit ID als Key
                self.mission_cache = {}
                for mission in missions_data:
                    mission_id = str(mission.get('id', ''))
                    self.mission_cache[mission_id] = {
                        'name': mission.get('name', ''),
                        'requirements': mission.get('requirements', {}),
                        'chances': mission.get('chances', {}),
                        'average_credits': mission.get('average_credits', 0)
                    }

                # Speichere Cache
                cache_data = {
                    'timestamp': time.time(),
                    'missions': self.mission_cache
                }

                with open(self.mission_cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, indent=2, ensure_ascii=False)

                self.mission_cache_age = time.time()
                self.logger.info(f"{Fore.GREEN}✓ Mission-Cache aktualisiert ({len(self.mission_cache)} Einsätze)")
                return True
            else:
                self.logger.warning(f"{Fore.YELLOW}Konnte Mission-Cache nicht aktualisieren (Status {response.status_code})")
                return False

        except Exception as e:
            self.logger.error(f"{Fore.RED}Fehler beim Aktualisieren des Mission-Cache: {e}")
            return False
    
    def login(self):
        """Meldet sich bei Leitstellenspiel.de an (mit Selenium)"""
        try:
            self.logger.info(f"{Fore.CYAN}Versuche Login...")

            # Hole Account-Daten (unterstützt beide Formate)
            account = None

            # Neues Format: credentials
            if 'credentials' in self.config:
                account = self.config['credentials']
                self.logger.info(f"{Fore.CYAN}Verwende credentials aus config")
            # Altes Format: accounts
            elif 'accounts' in self.config:
                for acc in self.config.get('accounts', []):
                    if acc.get('enabled', True):
                        account = acc
                        break
                self.logger.info(f"{Fore.CYAN}Verwende accounts aus config")

            if not account or not account.get('email') or not account.get('password'):
                self.logger.error(f"{Fore.RED}Keine Login-Daten in config.json gefunden!")
                self.logger.error(f"{Fore.YELLOW}Config: {self.config}")
                return False

            self.logger.info(f"{Fore.CYAN}Login mit: {account['email']}")

            # Öffne Login-Seite
            self.driver.get(f'{self.base_url}/users/sign_in')
            time.sleep(2)

            # Prüfe ob bereits eingeloggt
            if "Du bist bereits angemeldet" in self.driver.page_source:
                self.logged_in = True
                self.logger.info(f"{Fore.GREEN}✓ Bereits eingeloggt!")

                # Aktualisiere Mission-Cache
                if not self.mission_cache or (self.mission_cache_age and (time.time() - self.mission_cache_age) > 86400):
                    self.update_mission_cache()
                return True

            # Finde Login-Felder
            try:
                self.logger.info(f"{Fore.CYAN}Suche Login-Felder...")
                email_field = self.driver.find_element(By.ID, "user_email")
                password_field = self.driver.find_element(By.ID, "user_password")

                # Fülle Felder aus
                self.logger.info(f"{Fore.CYAN}Fülle Login-Felder aus...")
                email_field.clear()
                email_field.send_keys(account['email'])
                password_field.clear()
                password_field.send_keys(account['password'])

                # Klicke Login-Button
                self.logger.info(f"{Fore.CYAN}Klicke Login-Button...")
                login_button = self.driver.find_element(By.NAME, "commit")
                login_button.click()

                # Warte auf Redirect
                self.logger.info(f"{Fore.CYAN}Warte auf Redirect...")
                time.sleep(3)

                # Prüfe ob Login erfolgreich
                current_url = self.driver.current_url
                self.logger.info(f"{Fore.CYAN}Aktuelle URL: {current_url}")

                if 'users/sign_in' not in current_url:
                    self.logged_in = True
                    self.logger.info(f"{Fore.GREEN}✓ Login erfolgreich!")

                    # Übertrage Cookies von Selenium zu requests-Session
                    self.logger.info(f"{Fore.CYAN}Übertrage Session-Cookies...")
                    selenium_cookies = self.driver.get_cookies()
                    for cookie in selenium_cookies:
                        self.session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain'))
                    self.logger.info(f"{Fore.GREEN}✓ {len(selenium_cookies)} Cookies übertragen")

                    # Aktualisiere Mission-Cache
                    if not self.mission_cache or (self.mission_cache_age and (time.time() - self.mission_cache_age) > 86400):
                        self.update_mission_cache()

                    return True
                else:
                    self.logger.error(f"{Fore.RED}✗ Login fehlgeschlagen! Noch auf Login-Seite.")
                    # Prüfe auf Fehlermeldungen
                    if "alert" in self.driver.page_source.lower():
                        self.logger.error(f"{Fore.RED}Mögliche Fehlermeldung auf der Seite")
                    return False

            except NoSuchElementException as e:
                self.logger.error(f"{Fore.RED}Login-Felder nicht gefunden: {e}")
                self.logger.error(f"{Fore.YELLOW}Aktuelle URL: {self.driver.current_url}")
                return False

        except Exception as e:
            self.logger.error(f"{Fore.RED}Fehler beim Login: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

    def get_api_vehicles(self, force_refresh=False):
        """Holt alle Fahrzeuge über die offizielle API"""
        try:
            # Nutze Cache wenn vorhanden und nicht zu alt
            if self.api_vehicles and not force_refresh:
                return self.api_vehicles

            response = self.session.get(f'{self.base_url}/api/vehicles')

            if response.status_code == 200:
                self.api_vehicles = response.json()
                self.logger.debug(f"API: {len(self.api_vehicles)} Fahrzeuge geladen")
                return self.api_vehicles
            else:
                self.logger.warning(f"API-Fehler beim Laden der Fahrzeuge: {response.status_code}")
                return []

        except Exception as e:
            self.logger.warning(f"Fehler beim Laden der Fahrzeuge-API: {e}")
            return []

    def get_api_buildings(self, force_refresh=False):
        """Holt alle Gebäude über die offizielle API"""
        try:
            # Nutze Cache wenn vorhanden und nicht zu alt
            if self.api_buildings and not force_refresh:
                return self.api_buildings

            response = self.session.get(f'{self.base_url}/api/buildings')

            if response.status_code == 200:
                self.api_buildings = response.json()
                self.logger.debug(f"API: {len(self.api_buildings)} Gebaeude geladen")
                return self.api_buildings
            else:
                self.logger.warning(f"API-Fehler beim Laden der Gebaeude: {response.status_code}")
                return []

        except Exception as e:
            self.logger.warning(f"Fehler beim Laden der Gebaeude-API: {e}")
            return []

    def set_vehicle_status(self, vehicle_id, status):
        """Setzt den Status eines Fahrzeugs (6 = außer Dienst wegen Personalmangel)"""
        try:
            url = f'{self.base_url}/vehicles/{vehicle_id}/set_fms/{status}'
            response = self.session.post(url)

            if response.status_code == 200:
                self.logger.debug(f"Fahrzeug {vehicle_id} auf Status {status} gesetzt")
                return True
            else:
                self.logger.warning(f"Fehler beim Setzen des Status für Fahrzeug {vehicle_id}: {response.status_code}")
                return False

        except Exception as e:
            self.logger.warning(f"Fehler beim Setzen des Fahrzeugstatus: {e}")
            return False

    def get_credits(self):
        """Holt die aktuellen Credits über die API"""
        try:
            response = self.session.get(f'{self.base_url}/api/credits')

            if response.status_code == 200:
                data = response.json()
                # API gibt zurück: {"user_credits": 12345, "user_credits_current": 12345}
                credits = data.get('user_credits', 0)
                self.logger.debug(f"Aktuelle Credits: {credits:,}")
                return credits
            else:
                self.logger.warning(f"Fehler beim Abrufen der Credits: {response.status_code}")
                return None

        except Exception as e:
            self.logger.warning(f"Fehler beim Abrufen der Credits: {e}")
            return None

    def auto_expand_buildings(self):
        """Automatischer Gebäude-Ausbau"""
        try:
            self.logger.info(f"{Fore.CYAN}🏗️ Prüfe Gebäude-Ausbau...")

            # Hole aktuelle Gebäude
            buildings = self.get_api_buildings(force_refresh=True)
            if not buildings:
                self.logger.warning("Keine Gebäude gefunden")
                return

            # Hole aktuelle Credits
            credits = self.get_credits()
            if credits is None:
                self.logger.warning("Konnte Credits nicht abrufen")
                return

            self.logger.info(f"Verfügbare Credits: {credits:,}")

            # Prüfe jedes Gebäude auf Ausbau-Möglichkeiten
            for building in buildings:
                building_id = building.get('id')
                building_type = building.get('building_type')
                level = building.get('level', 0)
                is_building = building.get('is_building', False)

                # Überspringe Gebäude, die gerade ausgebaut werden
                if is_building:
                    continue

                # Prüfe ob Ausbau möglich ist (z.B. max Level 3 für Wachen)
                max_level = 3
                if level >= max_level:
                    continue

                # Prüfe ob genug Credits vorhanden (Ausbau kostet ca. 10.000 Credits)
                expansion_cost = 10000
                if credits < expansion_cost:
                    self.logger.info(f"Nicht genug Credits für Ausbau (benötigt: {expansion_cost:,})")
                    break

                # Starte Ausbau
                self.logger.info(f"🏗️ Starte Ausbau von Gebäude {building_id} (Level {level} → {level+1})")

                try:
                    # Ausbau über Selenium (da API keinen direkten Ausbau-Endpoint hat)
                    self.driver.get(f'{self.base_url}/buildings/{building_id}')
                    time.sleep(2)

                    # Suche Ausbau-Button
                    expand_button = self.driver.find_element(By.LINK_TEXT, "Ausbauen")
                    expand_button.click()
                    time.sleep(1)

                    # Bestätige Ausbau
                    confirm_button = self.driver.find_element(By.XPATH, "//a[contains(@href, '/buildings/') and contains(@href, '/expand')]")
                    confirm_button.click()

                    self.logger.info(f"✓ Ausbau gestartet für Gebäude {building_id}")
                    credits -= expansion_cost

                    # Nur ein Gebäude pro Durchlauf ausbauen
                    break

                except Exception as e:
                    self.logger.warning(f"Fehler beim Ausbau von Gebäude {building_id}: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Fehler beim automatischen Gebäude-Ausbau: {e}")

    def check_for_updates(self):
        """Prüft auf verfügbare Updates"""
        try:
            # Aktuelle Version aus Datei lesen
            current_version = "2.1.0"
            try:
                with open('version.txt', 'r') as f:
                    current_version = f.read().strip()
            except:
                pass

            # Prüfe GitHub Releases (Beispiel-URL - anpassen!)
            update_url = "https://api.github.com/repos/DEIN_USERNAME/leitstellenspiel-bot/releases/latest"

            response = requests.get(update_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                latest_version = data.get('tag_name', '').replace('v', '')

                if latest_version and latest_version != current_version:
                    self.logger.info(f"🆕 Update verfügbar: {current_version} → {latest_version}")
                    self.logger.info(f"Download: {data.get('html_url')}")
                    return True, latest_version, data
                else:
                    self.logger.info(f"✓ Bot ist aktuell (Version {current_version})")
                    return False, current_version, None
            else:
                self.logger.debug("Update-Check fehlgeschlagen")
                return False, current_version, None

        except Exception as e:
            self.logger.debug(f"Update-Check Fehler: {e}")
            return False, "2.1.0", None

    def auto_update(self, release_data):
        """Führt automatisches Update durch"""
        try:
            self.logger.info(f"{Fore.CYAN}🔄 Starte automatisches Update...")

            # Finde die richtige Download-URL (z.B. bot_standalone.py oder .exe)
            assets = release_data.get('assets', [])
            download_url = None

            # Suche nach bot_standalone.py oder der EXE
            for asset in assets:
                name = asset.get('name', '')
                if 'bot_standalone.py' in name or 'Leitstellenspiel-Bot-GUI.exe' in name:
                    download_url = asset.get('browser_download_url')
                    break

            # Fallback: Nutze zipball_url
            if not download_url:
                download_url = release_data.get('zipball_url')

            if not download_url:
                self.logger.error(f"{Fore.RED}Keine Download-URL gefunden!")
                return False

            self.logger.info(f"{Fore.CYAN}Download von: {download_url}")

            # Lade Update herunter
            response = requests.get(download_url, timeout=30)
            if response.status_code != 200:
                self.logger.error(f"{Fore.RED}Download fehlgeschlagen: {response.status_code}")
                return False

            # Erstelle Backup der aktuellen Datei
            current_file = __file__
            backup_file = current_file + '.backup'

            self.logger.info(f"{Fore.CYAN}Erstelle Backup: {backup_file}")
            import shutil
            shutil.copy2(current_file, backup_file)

            # Speichere neue Version
            self.logger.info(f"{Fore.CYAN}Installiere Update...")

            if download_url.endswith('.zip'):
                # ZIP-Datei entpacken
                import zipfile
                import io

                zip_file = zipfile.ZipFile(io.BytesIO(response.content))

                # Finde bot_standalone.py im ZIP
                for file_name in zip_file.namelist():
                    if 'bot_standalone.py' in file_name:
                        with open(current_file, 'wb') as f:
                            f.write(zip_file.read(file_name))
                        break
            else:
                # Direkte Datei
                with open(current_file, 'wb') as f:
                    f.write(response.content)

            self.logger.info(f"{Fore.GREEN}✓ Update erfolgreich installiert!")
            self.logger.info(f"{Fore.YELLOW}⚠ Bot wird neu gestartet...")

            # Neustart
            import sys
            import subprocess

            # Starte neuen Prozess
            subprocess.Popen([sys.executable] + sys.argv)

            # Beende aktuellen Prozess
            sys.exit(0)

        except Exception as e:
            self.logger.error(f"{Fore.RED}Update fehlgeschlagen: {e}")

            # Stelle Backup wieder her
            try:
                if os.path.exists(backup_file):
                    self.logger.info(f"{Fore.YELLOW}Stelle Backup wieder her...")
                    shutil.copy2(backup_file, current_file)
                    self.logger.info(f"{Fore.GREEN}✓ Backup wiederhergestellt")
            except:
                pass

            return False

    def check_session(self):
        """Prüft ob die Session noch gültig ist"""
        try:
            # Teste mit einem einfachen API-Call
            response = self.session.get(f'{self.base_url}/api/credits', timeout=5)

            # Wenn wir zur Login-Seite umgeleitet werden, ist die Session abgelaufen
            if 'sign_in' in response.url or response.status_code == 401:
                self.logger.warning(f"{Fore.YELLOW}⚠ Session abgelaufen!")
                self.logged_in = False
                return False

            return response.status_code == 200

        except Exception as e:
            self.logger.warning(f"Session-Check Fehler: {e}")
            return False

    def ensure_logged_in(self):
        """Stellt sicher, dass der Bot eingeloggt ist - loggt ggf. neu ein"""
        if not self.logged_in or not self.check_session():
            self.logger.info(f"{Fore.CYAN}🔄 Versuche automatischen Re-Login...")
            if self.login():
                self.logger.info(f"{Fore.GREEN}✓ Re-Login erfolgreich!")
                return True
            else:
                self.logger.error(f"{Fore.RED}✗ Re-Login fehlgeschlagen!")
                return False
        return True

    def get_available_vehicles_api(self):
        """Gibt alle verfügbaren Fahrzeuge zurück (Status 2 = verfügbar)"""
        vehicles = self.get_api_vehicles()
        # FMS 2 = verfügbar, 6 = auf Wache
        available = [v for v in vehicles if v.get('fms_real') in [2, 6]]
        return available

    def get_vehicles_by_type_api(self, vehicle_type_id):
        """Gibt alle verfügbaren Fahrzeuge eines bestimmten Typs zurück"""
        available = self.get_available_vehicles_api()
        return [v for v in available if v.get('vehicle_type') == vehicle_type_id]

    def get_missions(self):
        """Ruft alle offenen Einsätze ab"""
        try:
            self.logger.info(f"{Fore.CYAN}Rufe Einsätze ab...")

            # Hole eigene Einsätze über die richtige API
            url = f'{self.base_url}/map/mission_markers_own.js.erb'
            self.logger.info(f"{Fore.CYAN}URL: {url}")

            response = self.session.get(url)
            self.logger.info(f"{Fore.CYAN}Status Code: {response.status_code}")

            if response.status_code != 200:
                self.logger.error(f"{Fore.RED}Fehler beim Abrufen der Einsätze: Status {response.status_code}")
                # Prüfe ob wir eingeloggt sind
                if 'sign_in' in response.url:
                    self.logger.warning(f"{Fore.YELLOW}Session abgelaufen! Versuche automatisch neu einzuloggen...")
                    # Versuche neu einzuloggen
                    if self.login():
                        self.logger.info(f"{Fore.GREEN}✓ Automatischer Re-Login erfolgreich!")
                        # Versuche nochmal Einsätze abzurufen
                        return self.get_missions()
                    else:
                        self.logger.error(f"{Fore.RED}✗ Automatischer Re-Login fehlgeschlagen!")
                        return []
                return []

            # Debug: Zeige ersten Teil der Response
            response_preview = response.text[:200] if len(response.text) > 200 else response.text
            self.logger.info(f"{Fore.CYAN}Response Preview: {response_preview}...")

            # Extrahiere JSON aus JavaScript-Response
            # Suche nach: const mList = [...]
            import re
            match = re.search(r'const mList = (\[.*?\]);', response.text, re.DOTALL)

            if not match:
                self.logger.warning(f"{Fore.YELLOW}Keine Einsätze gefunden (mList nicht im Response)")
                self.logger.warning(f"{Fore.YELLOW}Response Länge: {len(response.text)} Zeichen")
                # Speichere Response für Debug
                with open(os.path.join(self.cache_dir, 'last_missions_response.txt'), 'w', encoding='utf-8') as f:
                    f.write(response.text)
                self.logger.info(f"{Fore.CYAN}Response gespeichert in: cache/last_missions_response.txt")
                return []

            json_str = match.group(1)
            # Entferne trailing commas (JavaScript erlaubt sie, JSON nicht)
            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)

            import json
            missions_data = json.loads(json_str)
            self.logger.info(f"{Fore.CYAN}JSON geparst: {len(missions_data)} Einträge")

            missions = []
            for mission in missions_data:
                missions.append({
                    'id': mission['id'],
                    'title': mission.get('caption', 'Unbekannt'),
                    'address': mission.get('address', ''),
                    'mission_type_id': mission.get('mtid'),
                    'patients_count': mission.get('patients_count', 0),
                    'possible_patients_count': mission.get('possible_patients_count', 0),
                    'prisoners_count': mission.get('prisoners_count', 0),
                    'possible_prisoners_count': mission.get('possible_prisoners_count', 0),
                    'vehicle_state': mission.get('vehicle_state', 0),
                    'missing_text': mission.get('missing_text'),
                    'icon': mission.get('icon', ''),
                    'latitude': mission.get('latitude'),
                    'longitude': mission.get('longitude'),
                    'created_at': mission.get('created_at'),
                    'filter_id': mission.get('filter_id', '')
                })

            self.logger.info(f"{Fore.GREEN}✓ {len(missions)} eigene Einsätze gefunden")

            # Hole auch Verbandseinsätze, falls aktiviert
            if self.config.get('features', {}).get('alliance_mission', False):
                alliance_missions = self.get_alliance_missions()
                if alliance_missions:
                    missions.extend(alliance_missions)
                    self.logger.info(f"{Fore.GREEN}✓ {len(alliance_missions)} Verbandseinsätze gefunden")

            return missions

        except Exception as e:
            self.logger.error(f"{Fore.RED}Fehler beim Abrufen der Einsätze: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return []

    def get_alliance_missions(self):
        """Ruft Verbandseinsätze ab"""
        try:
            response = self.session.get(f'{self.base_url}/map/mission_markers_alliance.js.erb')

            if response.status_code != 200:
                self.logger.error(f"{Fore.RED}Fehler beim Abrufen der Verbandseinsätze: Status {response.status_code}")
                return []

            # Extrahiere JSON aus JavaScript-Response
            import re
            match = re.search(r'const mList = (\[.*?\]);', response.text, re.DOTALL)

            if not match:
                # Keine Verbandseinsätze vorhanden
                return []

            json_str = match.group(1)
            # Entferne trailing commas
            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)

            import json
            missions_data = json.loads(json_str)

            missions = []
            for mission in missions_data:
                missions.append({
                    'id': mission['id'],
                    'title': mission.get('caption', 'Unbekannt'),
                    'address': mission.get('address', ''),
                    'mission_type_id': mission.get('mtid'),
                    'patients_count': mission.get('patients_count', 0),
                    'possible_patients_count': mission.get('possible_patients_count', 0),
                    'prisoners_count': mission.get('prisoners_count', 0),
                    'possible_prisoners_count': mission.get('possible_prisoners_count', 0),
                    'vehicle_state': mission.get('vehicle_state', 0),
                    'missing_text': mission.get('missing_text'),
                    'icon': mission.get('icon', ''),
                    'latitude': mission.get('latitude'),
                    'longitude': mission.get('longitude'),
                    'created_at': mission.get('created_at'),
                    'filter_id': mission.get('filter_id', ''),
                    'alliance_mission': True  # Markiere als Verbandseinsatz
                })

            return missions

        except Exception as e:
            self.logger.error(f"{Fore.RED}Fehler beim Abrufen der Verbandseinsätze: {e}")
            return []

    def get_mission_details(self, mission_id):
        """Ruft Details eines spezifischen Einsatzes ab"""
        try:
            response = self.session.get(f'{self.base_url}/missions/{mission_id}')
            soup = BeautifulSoup(response.content, 'html.parser')
            
            details = {
                'id': mission_id,
                'vehicles_required': [],
                'has_follow_up': False
            }
            
            # Prüfe auf Nachalarmierung
            follow_up_alert = soup.find('div', class_='alert-danger')
            if follow_up_alert and 'Nachalarmierung' in follow_up_alert.text:
                details['has_follow_up'] = True
            
            return details
            
        except Exception as e:
            self.logger.error(f"{Fore.RED}Fehler beim Abrufen der Einsatzdetails {mission_id}: {e}")
            return None

    def analyze_mission_requirements(self, soup, mission_id):
        """Analysiert die Anforderungen eines Einsatzes"""
        try:
            requirements = {
                'needed': [],
                'en_route': [],
                'on_scene': [],
                'missing': []
            }

            # Suche nach fehlenden Fahrzeugen (missing_text)
            # Versuche verschiedene Selektoren
            missing_alert = soup.find('div', class_='alert-missing-vehicles')
            if not missing_alert:
                # Alternative: Suche nach alert-Boxen mit "Fehlende Fahrzeuge"
                for alert in soup.find_all('div', class_=lambda x: x and 'alert' in x):
                    if 'Fehlende Fahrzeuge' in alert.get_text() or 'nachgefordert' in alert.get_text().lower():
                        missing_alert = alert
                        break

            if missing_alert:
                missing_text = missing_alert.get_text(strip=True)
                requirements['missing'].append(missing_text)
                self.logger.info(f"{Fore.YELLOW}Fehlende Anforderungen: {missing_text}")
            else:
                self.logger.info(f"{Fore.YELLOW}Fehlende Anforderungen: ")

            # Suche nach Fahrzeuganforderungen
            vehicle_requirements = soup.find_all('span', class_='building_list_vehicle_element_body_requirement')
            for req in vehicle_requirements:
                req_text = req.get_text(strip=True)
                requirements['needed'].append(req_text)

            # Suche nach bereits unterwegs befindlichen Fahrzeugen
            vehicle_rows = soup.find_all('tr', class_='vehicle_select_table_tr')
            for row in vehicle_rows:
                # Prüfe Status des Fahrzeugs
                status_span = row.find('span', class_='building_list_vehicle_element_body_right')
                if status_span:
                    status_text = status_span.get_text(strip=True)
                    if 'unterwegs' in status_text.lower() or 'fährt' in status_text.lower():
                        vehicle_name = row.find('label')
                        if vehicle_name:
                            requirements['en_route'].append(vehicle_name.get_text(strip=True))
                    elif 'vor ort' in status_text.lower() or 'angekommen' in status_text.lower():
                        vehicle_name = row.find('label')
                        if vehicle_name:
                            requirements['on_scene'].append(vehicle_name.get_text(strip=True))

            if requirements['en_route']:
                self.logger.info(f"{Fore.CYAN}Bereits unterwegs: {len(requirements['en_route'])} Fahrzeug(e)")
            if requirements['on_scene']:
                self.logger.info(f"{Fore.GREEN}Bereits vor Ort: {len(requirements['on_scene'])} Fahrzeug(e)")

            return requirements

        except Exception as e:
            self.logger.error(f"{Fore.RED}Fehler bei Anforderungsanalyse: {e}")
            return None

    def handle_alert(self):
        """Behandelt Browser-Alerts (z.B. Fahrzeug nicht verfügbar)"""
        try:
            WebDriverWait(self.driver, 1).until(EC.alert_is_present())
            alert = self.driver.switch_to.alert
            alert_text = alert.text
            self.logger.debug(f"Alert: {alert_text}")
            alert.accept()

            # Logge spezielle Fehler
            if "fehl" in alert_text.lower():
                self.logger.warning(f"{Fore.YELLOW}⚠ {alert_text}")

            return alert_text
        except TimeoutException:
            return None
        except NoAlertPresentException:
            return None

    def dispatch_vehicles(self, mission_id, mission_title="", missing_text_from_api="", patients_count=0, possible_patients_count=0):
        """Alarmiert Fahrzeuge für einen Einsatz mit Selenium"""
        try:
            self.logger.info(f"{Fore.CYAN}Öffne Einsatz {mission_id}...")

            # Öffne Einsatzseite
            self.driver.get(f'{self.base_url}/missions/{mission_id}')
            time.sleep(2)

            # Prüfe ob "Mehr Fahrzeuge laden" Button vorhanden ist
            try:
                load_more_button = self.driver.find_element(By.CLASS_NAME, "missing_vehicles_load")
                self.logger.info(f"{Fore.CYAN}🔄 'Mehr Fahrzeuge laden' Button gefunden - lade alle Fahrzeuge...")
                # Scrolle zum Button und klicke mit JavaScript (um Überlagerungen zu vermeiden)
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", load_more_button)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", load_more_button)
                time.sleep(2)  # Warte bis Fahrzeuge geladen sind
            except NoSuchElementException:
                pass  # Kein Button = alle Fahrzeuge bereits geladen
            except Exception as e:
                self.logger.debug(f"Fehler beim Laden weiterer Fahrzeuge: {e}")

            # Debug: Speichere Seite
            page_source = self.driver.page_source

            # Prüfe ob Einsatz abgeschlossen
            if "Der Einsatz wurde erfolgreich abgeschlossen" in page_source:
                self.logger.info(f"{Fore.GREEN}✓ Einsatz {mission_id} bereits abgeschlossen")
                return True

            # Prüfe ob Einsatz noch nicht begonnen hat
            if "Beginn in:" in page_source:
                self.logger.info(f"{Fore.YELLOW}⏳ Einsatz {mission_id} hat noch nicht begonnen")
                return False

            # Debug: Zeige was auf der Seite steht
            self.logger.info(f"{Fore.CYAN}Prüfe Einsatzstatus...")
            has_min_needed = "Wir benötigen noch min." in page_source
            has_additional = "Zusätzlich benötigte Fahrzeuge:" in page_source
            self.logger.info(f"{Fore.CYAN}  'Wir benötigen noch min.': {has_min_needed}")
            self.logger.info(f"{Fore.CYAN}  'Zusätzlich benötigte Fahrzeuge:': {has_additional}")

            # Prüfe ob bereits Fahrzeuge vor Ort sind und nichts mehr benötigt wird
            if not has_min_needed and not has_additional:
                # Prüfe ob missing_text Element existiert aber versteckt ist
                try:
                    missing_text_elem = self.driver.find_element(By.ID, "missing_text")
                    style = missing_text_elem.get_attribute("style")
                    if "display: none" in style or "display:none" in style:
                        # missing_text versteckt - prüfe ob es Fahrzeug-Checkboxen gibt
                        try:
                            checkboxes = self.driver.find_elements(By.CLASS_NAME, "vehicle_checkbox")
                            if len(checkboxes) > 0:
                                self.logger.info(f"{Fore.YELLOW}⚠ missing_text versteckt, aber {len(checkboxes)} Fahrzeuge verfügbar")
                                self.logger.info(f"{Fore.CYAN}📦 Versuche Anforderungen aus Cache zu laden...")
                                # NICHT abbrechen - weiter unten werden die Anforderungen aus dem Cache geholt
                            else:
                                # Keine Checkboxen = alle Fahrzeuge sind bereits unterwegs/vor Ort
                                self.logger.info(f"{Fore.GREEN}✓ Fahrzeuge unterwegs/vor Ort (missing_text versteckt, keine Checkboxen), nichts mehr benötigt für Einsatz {mission_id}")
                                return True
                        except:
                            pass
                except NoSuchElementException:
                    # Kein missing_text Element - prüfe ob Fahrzeuge vor Ort/unterwegs sind
                    try:
                        vehicles_at_mission = self.driver.find_element(By.ID, "mission_vehicle_at_mission")
                        # Prüfe ob es Checkboxen gibt
                        checkboxes = self.driver.find_elements(By.CLASS_NAME, "vehicle_checkbox")
                        if len(checkboxes) == 0:
                            self.logger.info(f"{Fore.GREEN}✓ Fahrzeuge vor Ort, keine weiteren Checkboxen, nichts mehr benötigt für Einsatz {mission_id}")
                            return True
                        else:
                            self.logger.info(f"{Fore.YELLOW}⚠ Fahrzeuge vor Ort, aber {len(checkboxes)} Checkboxen verfügbar - prüfe Cache")
                    except NoSuchElementException:
                        try:
                            vehicles_driving = self.driver.find_element(By.ID, "mission_vehicle_driving")
                            # Prüfe ob es Checkboxen gibt
                            checkboxes = self.driver.find_elements(By.CLASS_NAME, "vehicle_checkbox")
                            if len(checkboxes) == 0:
                                self.logger.info(f"{Fore.GREEN}✓ Fahrzeuge unterwegs, keine weiteren Checkboxen, nichts mehr benötigt für Einsatz {mission_id}")
                                return True
                            else:
                                self.logger.info(f"{Fore.YELLOW}⚠ Fahrzeuge unterwegs, aber {len(checkboxes)} Checkboxen verfügbar - prüfe Cache")
                        except NoSuchElementException:
                            pass

                # Wenn wir hier sind, gibt es keine Anforderungen auf der Seite
                # Aber wir brechen NICHT ab - weiter unten wird aus Cache/Hilfe geladen
                self.logger.info(f"{Fore.CYAN}Keine Anforderungen auf Seite gefunden, versuche Cache/Hilfe...")
                # Speichere Seite für Debug
                with open(os.path.join(self.cache_dir, f'mission_{mission_id}_no_requirements.html'), 'w', encoding='utf-8') as f:
                    f.write(page_source)
                self.logger.info(f"{Fore.CYAN}Seite gespeichert: cache/mission_{mission_id}_no_requirements.html")

                # Versuche Anforderungen aus Cache/Hilfe zu laden
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(page_source, 'html.parser')

                # HÖCHSTE PRIORITÄT: missing_text aus API (das was JETZT fehlt!)
                mission_requirements = {}
                import re
                if missing_text_from_api and missing_text_from_api.strip():
                    self.logger.info(f"{Fore.CYAN}📝 Verwende missing_text aus API: {missing_text_from_api}")
                    mission_requirements = self.parse_missing_text(missing_text_from_api)
                    if mission_requirements:
                        self.logger.info(f"{Fore.GREEN}✓ Anforderungen aus API missing_text geparst: {mission_requirements}")

                # FALLBACK 1: Versuche "Wir benötigen:" Text auf der Seite zu parsen
                if not mission_requirements:
                    benötigen_match = re.search(r'Wir benötigen:\s*(.+?)(?:\.|<|$)', page_source, re.DOTALL | re.IGNORECASE)
                    if benötigen_match:
                        benötigen_text = benötigen_match.group(1).strip()
                        self.logger.info(f"{Fore.CYAN}📝 Gefunden 'Wir benötigen' auf Seite: {benötigen_text}")
                        mission_requirements = self.parse_missing_text(benötigen_text)
                        if mission_requirements:
                            self.logger.info(f"{Fore.GREEN}✓ Anforderungen aus 'Wir benötigen' geparst: {mission_requirements}")

                # FALLBACK 2: Hole Mission-Type-ID aus Hilfe-Link und lade aus Cache
                if not mission_requirements:
                    mission_type_id = self.get_mission_type_from_help(mission_id, soup)
                    if mission_type_id:
                        mission_requirements = self.get_mission_requirements_from_cache(mission_type_id)
                        if mission_requirements:
                            self.logger.info(f"{Fore.CYAN}📦 Anforderungen aus Cache geladen (Type-ID: {mission_type_id}): {mission_requirements}")

                # Wenn nicht im Cache, versuche Hilfe-Seite zu parsen
                if not mission_requirements:
                    mission_requirements = self.get_mission_requirements_from_help(mission_id, soup)
                    if mission_requirements:
                        self.logger.info(f"{Fore.CYAN}📄 Anforderungen aus Hilfe-Seite geparst: {mission_requirements}")

                # WICHTIG: Füge RTW basierend auf Patientenanzahl hinzu
                if patients_count > 0 or possible_patients_count > 0:
                    # Verwende die tatsächliche Patientenanzahl, falls vorhanden, sonst die mögliche
                    required_rtw = patients_count if patients_count > 0 else possible_patients_count

                    # Prüfe ob bereits RTW in den Anforderungen sind
                    current_rtw = mission_requirements.get('RTW', 0)

                    # Wenn mehr RTW benötigt werden als bereits gefordert, erhöhe die Anzahl
                    if required_rtw > current_rtw:
                        mission_requirements['RTW'] = required_rtw
                        self.logger.info(f"{Fore.CYAN}🚑 Erhöhe RTW-Anforderung auf {required_rtw} (Patienten: {patients_count or possible_patients_count})")
                    elif current_rtw > 0:
                        self.logger.info(f"{Fore.CYAN}🚑 RTW bereits gefordert: {current_rtw} (Patienten: {patients_count or possible_patients_count})")

                # Wenn wir Anforderungen haben, wähle Fahrzeuge über Checkboxen aus
                if mission_requirements:
                    self.logger.info(f"{Fore.CYAN}Wähle Fahrzeuge über Checkboxen aus...")
                    selected_count, selected_vehicle_ids = self.select_vehicles_by_checkboxes(mission_requirements)
                    if selected_count > 0:
                        self.logger.info(f"{Fore.GREEN}✓ {selected_count} Fahrzeuge ausgewählt")
                    else:
                        self.logger.warning(f"{Fore.YELLOW}⚠ Keine Fahrzeuge ausgewählt")
                        selected_vehicle_ids = []
                else:
                    # Keine Anforderungen gefunden - prüfe nochmal ob wirklich nichts benötigt wird
                    checkboxes = self.driver.find_elements(By.CLASS_NAME, "vehicle_checkbox")
                    if len(checkboxes) == 0:
                        self.logger.info(f"{Fore.GREEN}✓ Keine Anforderungen und keine Checkboxen - Einsatz vollständig")
                        return True
                    else:
                        self.logger.warning(f"{Fore.YELLOW}⚠ Keine Anforderungen gefunden, aber {len(checkboxes)} Checkboxen verfügbar!")

            # Prüfe auf "Zusätzlich benötigte Fahrzeuge:"
            if "Zusätzlich benötigte Fahrzeuge:" in page_source:
                self.logger.info(f"{Fore.CYAN}Nachalarmierung für Einsatz {mission_id}")

                # Extrahiere benötigte Fahrzeuge
                import re
                match = re.search(r'Zusätzlich benötigte Fahrzeuge:\s*(.+?)\.', page_source, re.DOTALL)
                if match:
                    needed_text = match.group(1)
                    self.logger.info(f"{Fore.YELLOW}Benötigt: {needed_text}")

                    # Parse benötigte Fahrzeuge (z.B. "1 LF, 1 RTW")
                    vehicles_needed = []
                    for part in needed_text.split(','):
                        part = part.strip()
                        # Entferne Klammern-Inhalte
                        part = re.sub(r'\([^)]*\)', '', part).strip()
                        if part:
                            vehicles_needed.append(part)

                    # Alarmiere benötigte Fahrzeuge
                    for vehicle_spec in vehicles_needed:
                        # Format: "1 LF" oder "2 RTW"
                        match = re.match(r'(\d+)\s+(.+)', vehicle_spec)
                        if match:
                            count = int(match.group(1))
                            vehicle_type = match.group(2).strip()

                            for i in range(count):
                                try:
                                    # Klicke auf Fahrzeug-Button
                                    button = self.driver.find_element(By.XPATH, f'//*[@title="1 {vehicle_type}"]')
                                    button.click()
                                    time.sleep(0.5)
                                    self.handle_alert()
                                    self.logger.info(f"{Fore.GREEN}✓ {vehicle_type} alarmiert")
                                except NoSuchElementException:
                                    self.logger.warning(f"{Fore.YELLOW}⚠ Button für {vehicle_type} nicht gefunden")
                                except Exception as e:
                                    self.logger.error(f"{Fore.RED}Fehler beim Alarmieren von {vehicle_type}: {e}")

            # Wenn nichts Spezifisches benötigt wird, schicke 1 Fahrzeug als Vorhut
            elif "Wir benötigen noch min." in page_source:
                self.logger.info(f"{Fore.CYAN}Schicke Vorhut für Einsatz {mission_id}")

                # Suche alle verfügbaren Fahrzeug-Buttons
                try:
                    # Finde alle Buttons mit vehicle_select_table_
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(page_source, 'html.parser')

                    # Suche nach Fahrzeug-Buttons
                    vehicle_buttons = soup.find_all('a', class_='btn')
                    self.logger.info(f"{Fore.CYAN}Gefundene Buttons: {len(vehicle_buttons)}")

                    # Zeige erste 5 Buttons
                    for i, btn in enumerate(vehicle_buttons[:5]):
                        title = btn.get('title', 'Kein Title')
                        self.logger.info(f"{Fore.CYAN}  Button {i+1}: {title}")

                except Exception as e:
                    self.logger.error(f"{Fore.RED}Fehler beim Suchen von Buttons: {e}")

                # Versuche LF zu schicken
                try:
                    button = self.driver.find_element(By.XPATH, '//*[@title="1 LF"]')
                    self.logger.info(f"{Fore.CYAN}LF-Button gefunden, klicke...")
                    button.click()
                    time.sleep(0.5)
                    self.handle_alert()
                    self.logger.info(f"{Fore.GREEN}✓ 1 LF als Vorhut alarmiert")
                except NoSuchElementException:
                    self.logger.warning(f"{Fore.YELLOW}⚠ LF-Button nicht gefunden, versuche RTW...")
                    # Versuche RTW
                    try:
                        button = self.driver.find_element(By.XPATH, '//*[@title="1 RTW"]')
                        self.logger.info(f"{Fore.CYAN}RTW-Button gefunden, klicke...")
                        button.click()
                        time.sleep(0.5)
                        self.handle_alert()
                        self.logger.info(f"{Fore.GREEN}✓ 1 RTW als Vorhut alarmiert")
                    except NoSuchElementException:
                        self.logger.warning(f"{Fore.YELLOW}⚠ RTW-Button nicht gefunden, versuche FuStW...")
                        # Versuche FuStW
                        try:
                            button = self.driver.find_element(By.XPATH, '//*[@title="1 FuStW"]')
                            self.logger.info(f"{Fore.CYAN}FuStW-Button gefunden, klicke...")
                            button.click()
                            time.sleep(0.5)
                            self.handle_alert()
                            self.logger.info(f"{Fore.GREEN}✓ 1 FuStW als Vorhut alarmiert")
                        except NoSuchElementException:
                            self.logger.warning(f"{Fore.YELLOW}⚠ Kein Fahrzeug zum Alarmieren gefunden")
                            # Speichere Seite für Debug
                            with open(os.path.join(self.cache_dir, f'mission_{mission_id}_page.html'), 'w', encoding='utf-8') as f:
                                f.write(page_source)
                            self.logger.info(f"{Fore.CYAN}Seite gespeichert: cache/mission_{mission_id}_page.html")
                            return False
                except Exception as e:
                    self.logger.error(f"{Fore.RED}Fehler beim Klicken: {e}")

            # Klicke "Alarmieren" Button
            try:
                self.logger.info(f"{Fore.CYAN}Suche Alarmieren-Button...")
                commit_button = self.driver.find_element(By.NAME, "commit")
                self.logger.info(f"{Fore.CYAN}Alarmieren-Button gefunden, klicke...")
                self.driver.execute_script("arguments[0].click();", commit_button)
                time.sleep(2)

                # Prüfe auf Erfolgs-/Fehler-Meldung
                try:
                    success_alert = self.driver.find_element(By.XPATH, "//div[contains(@class, 'alert-success')]")
                    success_text = success_alert.text
                    self.logger.info(f"{Fore.GREEN}✓ {success_text}")

                    # Prüfe, ob Fahrzeuge wegen Personalmangel nicht alarmiert wurden
                    # Gehe zurück zur Einsatzseite und prüfe noch ausgewählte Checkboxen
                    self.driver.get(f'{self.base_url}/missions/{mission_id}')
                    time.sleep(1)

                    # Finde noch ausgewählte Checkboxen (= nicht alarmierte Fahrzeuge)
                    still_selected = self.driver.find_elements(By.CSS_SELECTOR, "input.vehicle_checkbox:checked")
                    if len(still_selected) > 0:
                        self.logger.warning(f"{Fore.YELLOW}⚠ {len(still_selected)} Fahrzeuge wurden nicht alarmiert (vermutlich Personalmangel)")
                        for checkbox in still_selected:
                            vehicle_id = checkbox.get_attribute("value")
                            if vehicle_id:
                                self.logger.info(f"{Fore.CYAN}Setze Fahrzeug {vehicle_id} auf Status 6 (Personalmangel)...")
                                self.set_vehicle_status(vehicle_id, 6)

                    return True
                except NoSuchElementException:
                    try:
                        error_alert = self.driver.find_element(By.XPATH, "//div[contains(@class, 'alert-danger')]")
                        error_text = error_alert.text
                        self.logger.error(f"{Fore.RED}✗ {error_text}")
                        return False
                    except NoSuchElementException:
                        # Keine Meldung gefunden - vermutlich erfolgreich
                        self.logger.info(f"{Fore.GREEN}✓ Fahrzeuge alarmiert für Einsatz {mission_id}")
                        return True

            except NoSuchElementException:
                self.logger.warning(f"{Fore.YELLOW}⚠ Alarmieren-Button nicht gefunden")
                # Speichere Seite für Debug
                with open(os.path.join(self.cache_dir, f'mission_{mission_id}_no_button.html'), 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                self.logger.info(f"{Fore.CYAN}Seite gespeichert: cache/mission_{mission_id}_no_button.html")
                return False

        except Exception as e:
            self.logger.error(f"{Fore.RED}Fehler beim Alarmieren von Fahrzeugen für {mission_id}: {e}")
            return False

    def select_vehicles_by_checkboxes(self, requirements):
        """Wählt Fahrzeuge über Checkboxen aus basierend auf Anforderungen

        Returns:
            tuple: (selected_count, selected_vehicle_ids) - Anzahl und IDs der ausgewählten Fahrzeuge
        """
        try:
            selected_vehicle_ids = []  # Liste der ausgewählten Fahrzeug-IDs
            # Mapping von internen Namen zu Checkbox-Attributen
            # Basierend auf den tatsächlichen HTML-Attributen
            vehicle_type_mapping = {
                'LF': ['lf_only', 'hlf_only', 'fire'],  # Löschfahrzeuge (fire=1 ist generisch für Feuerwehr)
                'DLK': ['dlk'],  # Drehleiter
                'RW': ['rw', 'ab_ruest_rw'],  # Rüstwagen
                'ELW': ['elw', 'kdow_elw', 'elw_or_battalion_chief_vehicle'],  # Einsatzleitwagen
                'GW-A': ['gw_a', 'gwa'],  # Atemschutz
                'TLF': ['tlf'],  # Tanklöschfahrzeug
                'RTW': ['rtw', 'ambulance'],  # Rettungswagen
                'NEF': ['nef'],  # Notarzteinsatzfahrzeug
                'KTW': ['ktw', 'patient_transport'],  # Krankentransportwagen
                'RTH': ['rth'],  # Rettungshubschrauber
                'FuStW': ['fustw', 'fustw_or_police_motorcycle'],  # Funkstreifenwagen
                'GefKw': ['gefkw'],  # Gefangenenkraftwagen
                'FwK': ['fwk'],  # Feuerwehrkran
                'Hundestaffel': ['k9'],  # Hundeführer
            }

            # Fallback-Mapping: Wenn Fahrzeugtyp nicht verfügbar, verwende Alternative
            fallback_mapping = {
                'KTW': 'RTW',  # Wenn kein KTW verfügbar, nimm RTW
            }

            selected_count = 0

            for vehicle_type, count_needed in requirements.items():
                attr_names = vehicle_type_mapping.get(vehicle_type, [vehicle_type.lower()])

                # Wähle die benötigte Anzahl aus
                selected_for_this_type = 0

                # DEBUG: Zähle verfügbare Fahrzeuge dieses Typs
                checkboxes_all = self.driver.find_elements(By.CLASS_NAME, "vehicle_checkbox")
                available_count = 0
                available_with_state_2 = 0

                for cb in checkboxes_all:
                    if cb.is_selected():
                        continue
                    for attr_name in attr_names:
                        try:
                            if cb.get_attribute(attr_name) == "1":
                                available_count += 1
                                # Prüfe vehicle_state
                                v_state = cb.get_attribute("vehicle_state")
                                if v_state == "2":
                                    available_with_state_2 += 1
                                break
                        except:
                            pass

                self.logger.info(f"{Fore.CYAN}🔍 Suche {count_needed}x {vehicle_type} (gefunden: {available_count} Checkboxen, davon {available_with_state_2} mit state=2)")

                for i in range(count_needed):
                    try:
                        # Hole Checkboxen JEDES MAL neu (weil sie nach Klick neu geladen werden)
                        checkboxes = self.driver.find_elements(By.CLASS_NAME, "vehicle_checkbox")

                        # Finde nächste passende, nicht-ausgewählte Checkbox
                        found = False
                        for checkbox in checkboxes:
                            # Prüfe ob Checkbox bereits ausgewählt ist
                            if checkbox.is_selected():
                                continue

                            # Prüfe ob Fahrzeug verfügbar ist (vehicle_state="2")
                            vehicle_state = None
                            try:
                                vehicle_state = checkbox.get_attribute("vehicle_state")
                            except:
                                pass

                            # Wenn vehicle_state existiert und NICHT "2" ist, überspringe
                            if vehicle_state and vehicle_state != "2":
                                continue

                            # Prüfe alle möglichen Attributnamen
                            for attr_name in attr_names:
                                try:
                                    attr_value = checkbox.get_attribute(attr_name)
                                    if attr_value == "1":
                                        # Hole Fahrzeug-ID
                                        vehicle_id = checkbox.get_attribute("value")

                                        # Scrolle zur Checkbox damit sie sichtbar ist
                                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
                                        time.sleep(0.2)

                                        # Klicke die Checkbox
                                        self.driver.execute_script("arguments[0].click();", checkbox)
                                        selected_count += 1
                                        selected_for_this_type += 1
                                        selected_vehicle_ids.append(vehicle_id)  # Speichere ID
                                        self.logger.info(f"{Fore.GREEN}✓ {vehicle_type} #{selected_for_this_type} ausgewählt (ID: {vehicle_id})")
                                        time.sleep(0.5)  # Warte länger nach Klick
                                        found = True
                                        break
                                except:
                                    pass

                            if found:
                                break

                        if not found:
                            self.logger.warning(f"{Fore.YELLOW}⚠ Keine weiteren {vehicle_type} verfügbar")
                            break

                    except Exception as e:
                        self.logger.warning(f"{Fore.YELLOW}⚠ Fehler beim Auswählen von {vehicle_type}: {e}")

                # Wenn nicht genug Fahrzeuge gefunden, versuche Fallback
                if selected_for_this_type < count_needed:
                    still_needed = count_needed - selected_for_this_type
                    fallback_type = fallback_mapping.get(vehicle_type)

                    if fallback_type:
                        self.logger.info(f"{Fore.CYAN}Versuche Fallback: {fallback_type} statt {vehicle_type}")

                        # Hole neue Checkboxen-Liste
                        checkboxes = self.driver.find_elements(By.CLASS_NAME, "vehicle_checkbox")
                        fallback_checkboxes = []
                        fallback_attr_names = vehicle_type_mapping.get(fallback_type, [fallback_type.lower()])

                        for checkbox in checkboxes:
                            if checkbox.is_selected():
                                continue

                            # Prüfe ob Fahrzeug verfügbar ist
                            try:
                                vehicle_state = checkbox.get_attribute("vehicle_state")
                                if vehicle_state != "2":
                                    continue
                            except:
                                pass

                            for attr_name in fallback_attr_names:
                                try:
                                    attr_value = checkbox.get_attribute(attr_name)
                                    if attr_value == "1":
                                        fallback_checkboxes.append(checkbox)
                                        break
                                except:
                                    pass

                        # Wähle Fallback-Fahrzeuge
                        for i in range(min(still_needed, len(fallback_checkboxes))):
                            try:
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", fallback_checkboxes[i])
                                time.sleep(0.2)
                                self.driver.execute_script("arguments[0].click();", fallback_checkboxes[i])
                                selected_count += 1
                                selected_for_this_type += 1
                                self.logger.info(f"{Fore.GREEN}✓ {fallback_type} #{i+1} (Fallback für {vehicle_type}) ausgewählt")
                                time.sleep(0.3)
                            except Exception as e:
                                self.logger.warning(f"{Fore.YELLOW}⚠ Fehler beim Auswählen von {fallback_type}: {e}")

                    if selected_for_this_type < count_needed:
                        self.logger.warning(f"{Fore.YELLOW}⚠ Nur {selected_for_this_type}/{count_needed} {vehicle_type} verfügbar")

            return (selected_count, selected_vehicle_ids)

        except Exception as e:
            self.logger.error(f"{Fore.RED}Fehler beim Auswählen von Fahrzeugen: {e}")
            return (0, [])

    def get_mission_type_from_help(self, mission_id, soup):
        """Extrahiert die Mission-Type-ID aus der Hilfe-Seite URL"""
        try:
            mission_help_link = soup.find('a', id='mission_help')
            if mission_help_link:
                help_url = mission_help_link.get('href', '')
                # URL Format: /einsaetze/123?mission_id=456
                # Extrahiere die 123 (mission_type_id)
                import re
                match = re.search(r'/einsaetze/(\d+)', help_url)
                if match:
                    return match.group(1)
        except Exception as e:
            self.logger.debug(f"Fehler beim Extrahieren der Mission-Type-ID: {e}")
        return None

    def get_mission_requirements_from_cache(self, mission_type_id):
        """Holt die Anforderungen aus dem Cache"""
        if not self.mission_cache:
            return {}

        mission_data = self.mission_cache.get(str(mission_type_id))
        if not mission_data:
            return {}

        # Konvertiere API-Format zu internem Format
        requirements = {}
        api_reqs = mission_data.get('requirements', {})
        api_chances = mission_data.get('chances', {})
        mission_name = mission_data.get('name', '').lower()

        # Mapping von API-Namen zu internen Namen
        mapping = {
            'firetrucks': 'LF',
            'battalion_chief_vehicles': 'ELW',
            'heavy_rescue_vehicles': 'RW',
            'mobile_air': 'GW-A',
            'water_tankers': 'TLF',
            'turntable_ladder_vehicles': 'DLK',
            'ambulances': 'RTW',
            'fly_cars': 'NEF',
            'mobile_command_vehicles': 'ELW',
            'police_cars': 'FuStW',
            'rescue_helicopters': 'RTH',
            'patient_transport': 'KTW',
            'fwk': 'FwK',  # Feuerwehrkran
            'oneof_police_patrol_or_motorcycle': 'FuStW',  # Funkstreifenwagen oder Polizeimotorrad
            'police_motorcycles': 'FuStW',  # Polizeimotorrad
            'k9': 'Hundestaffel',  # Hundeführer
            'swat_armoured_vehicles': 'GefKw',  # Gefangenenkraftwagen
        }

        # Zuerst: Feste Anforderungen (requirements)
        for api_name, internal_name in mapping.items():
            if api_name in api_reqs:
                count = api_reqs[api_name]
                if count > 0:
                    requirements[internal_name] = count
                    # Spezialfall: patient_transport wird als KTW erkannt
                    if api_name == 'patient_transport':
                        self.logger.info(f"{Fore.CYAN}📦 Krankentransport erkannt (API) - schicke {count}x KTW")

        # Wenn keine festen Anforderungen, prüfe "chances"
        # Für Rettungsdienst-Einsätze: nef und patient_transport sind in "chances" definiert
        if not requirements and api_chances:
            # Wenn NEF mit hoher Wahrscheinlichkeit (>= 50%), schicke NEF + RTW
            nef_chance = api_chances.get('nef', 0)
            patient_transport_chance = api_chances.get('patient_transport', 0)

            if nef_chance >= 50:
                # Hohe NEF-Chance: Schicke NEF + RTW
                requirements['NEF'] = 1
                requirements['RTW'] = 1
                self.logger.info(f"{Fore.CYAN}📦 Notfall erkannt (NEF-Chance: {nef_chance}%) - schicke NEF + RTW")
            elif nef_chance > 0:
                # Niedrige NEF-Chance: Nur RTW
                requirements['RTW'] = 1
                self.logger.info(f"{Fore.CYAN}📦 Rettungsdienst-Einsatz (NEF-Chance: {nef_chance}%) - schicke RTW")
            elif patient_transport_chance > 0:
                # Nur patient_transport: Krankentransport mit KTW
                requirements['KTW'] = 1
                self.logger.info(f"{Fore.CYAN}📦 Krankentransport erkannt (Chance) - schicke KTW")

        # FALLBACK: Wenn immer noch keine Requirements, prüfe Einsatznamen
        if not requirements:
            # Krankentransport-Fallback
            if 'krankentransport' in mission_name:
                requirements['KTW'] = 1
                self.logger.info(f"{Fore.CYAN}📦 Krankentransport erkannt (Name-Fallback) - schicke KTW")
            # Weitere Name-basierte Fallbacks können hier hinzugefügt werden
            elif 'brand' in mission_name or 'feuer' in mission_name:
                requirements['LF'] = 1
                self.logger.info(f"{Fore.CYAN}📦 Feuerwehr-Einsatz erkannt (Name-Fallback) - schicke LF")

        return requirements

    def get_mission_requirements_from_help(self, mission_id, soup):
        """Holt die Mindestanforderungen aus der Einsatz-Hilfe-Seite"""
        try:
            # Finde den Link zur Einsatz-Hilfe auf der Einsatzseite
            mission_help_link = soup.find('a', id='mission_help')
            if not mission_help_link:
                self.logger.warning(f"{Fore.YELLOW}Keine Einsatz-Hilfe gefunden")
                return {}

            help_url = mission_help_link.get('href')
            if not help_url:
                return {}

            # Hole die Hilfe-Seite
            help_response = self.session.get(f'{self.base_url}{help_url}')
            if help_response.status_code != 200:
                self.logger.warning(f"{Fore.YELLOW}Konnte Einsatz-Hilfe nicht laden (Status: {help_response.status_code})")
                return {}

            help_soup = BeautifulSoup(help_response.content, 'html.parser')

            import re
            requirements = {}

            # Finde den Text-Bereich
            text_content = help_soup.get_text()
            lines = text_content.split('\n')

            # Fahrzeugtypen-Mapping (was wir suchen -> was wir zurückgeben)
            vehicle_mapping = {
                'RTW': ['Rettungswagen', 'RTW'],
                'NEF': ['Notarzteinsatzfahrzeug', 'NEF'],
                'KTW': ['Krankentransportwagen', 'KTW'],
                'NAW': ['Notarztwagen', 'NAW'],
                'RTH': ['Rettungshubschrauber', 'RTH'],
                'ITW': ['Intensivtransportwagen', 'ITW'],
                'LF': ['Löschfahrzeug', 'LF'],
                'DLK': ['Drehleiter', 'DLK'],
                'TLF': ['Tanklöschfahrzeug', 'TLF'],
                'RW': ['Rüstwagen', 'RW'],
                'GW': ['Gerätewagen', 'GW'],
                'ELW': ['Einsatzleitwagen', 'ELW'],
                'MTW': ['Mannschaftstransportwagen', 'MTW'],
                'SW': ['Schlauchwagen', 'SW'],
                'FuStW': ['Funkstreifenwagen', 'FuStW'],
                'GefKw': ['Gefangenenkraftwagen', 'GefKw'],
                'GW-A': ['GW-A', 'GW A'],
                'GW-L': ['GW-L', 'GW L'],
                'GW-Öl': ['GW-Öl', 'GW Öl'],
                'GW-Mess': ['GW-Mess', 'GW Mess'],
            }

            in_requirements = False
            for line in lines:
                line = line.strip()

                # Starte bei "Mindestanforderung"
                if 'Mindestanforderung' in line:
                    in_requirements = True
                    continue

                # Stoppe bei bestimmten Schlüsselwörtern
                if in_requirements and any(keyword in line for keyword in ['Weitere', 'Einsatzvarianten', 'Wahrscheinlichkeit', 'Voraussetzung']):
                    break

                if in_requirements and line:
                    # Suche nach Muster: "Zahl x Fahrzeugtyp" oder "Zahl Fahrzeugtyp"
                    match = re.match(r'^(\d+)\s*x?\s*(.+)$', line)
                    if match:
                        count = int(match.group(1))
                        vehicle_desc = match.group(2).strip()

                        # Bereinige Beschreibung (entferne Klammern etc.)
                        vehicle_desc = re.sub(r'\s*\([^)]*\).*$', '', vehicle_desc)
                        vehicle_desc = vehicle_desc.split(' oder ')[0].strip()

                        # Finde passenden Fahrzeugtyp
                        for vtype, aliases in vehicle_mapping.items():
                            for alias in aliases:
                                if alias.lower() in vehicle_desc.lower():
                                    if vtype in requirements:
                                        requirements[vtype] = max(requirements[vtype], count)
                                    else:
                                        requirements[vtype] = count
                                    break

            if requirements:
                self.logger.info(f"{Fore.CYAN}Mindestanforderungen aus Hilfe-Seite:")
                for vtype, count in requirements.items():
                    self.logger.info(f"{Fore.CYAN}  - {count}x {vtype}")

            return requirements

        except Exception as e:
            self.logger.error(f"{Fore.RED}Fehler beim Abrufen der Einsatzanforderungen: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {}

    def match_vehicle_to_requirement(self, vehicle, requirement_type):
        """Prüft ob ein Fahrzeug zu einer Anforderung passt"""
        vehicle_type = vehicle.get_text(strip=True).upper()
        requirement_type = requirement_type.upper()

        # Direkte Übereinstimmung
        if requirement_type in vehicle_type or vehicle_type in requirement_type:
            return True

        # Aliase und Abkürzungen
        aliases = {
            'RTW': ['RETTUNGSWAGEN', 'RTW'],
            'NEF': ['NOTARZTEINSATZFAHRZEUG', 'NEF'],
            'KTW': ['KRANKENTRANSPORTWAGEN', 'KTW'],
            'LF': ['LÖSCHFAHRZEUG', 'LF', 'LÖSCHGRUPPENFAHRZEUG', 'LGF'],
            'DLK': ['DREHLEITER', 'DLK', 'DL'],
            'RW': ['RÜSTWAGEN', 'RW'],
            'GW': ['GERÄTEWAGEN', 'GW'],
            'FUSTW': ['FUNKSTREIFENWAGEN', 'FUSTW'],
            'MTW': ['MANNSCHAFTSTRANSPORTWAGEN', 'MTW'],
            'ELW': ['EINSATZLEITWAGEN', 'ELW'],
            'GKW': ['GERÄTEKRAFTWAGEN', 'GKW'],
            'SW': ['SCHLAUCHWAGEN', 'SW'],
            'TLF': ['TANKLÖSCHFAHRZEUG', 'TLF'],
        }

        for key, values in aliases.items():
            if requirement_type in values or requirement_type == key:
                for value in values:
                    if value in vehicle_type:
                        return True

        return False

    def parse_missing_text(self, missing_text):
        """Parst missing_text und extrahiert Fahrzeuganforderungen"""
        if not missing_text:
            return {}

        import re
        requirements = {}

        # Bekannte Fahrzeugtypen und ihre Patterns (mit Plural-Unterstützung)
        # Pattern: Optional Zahl, dann Fahrzeugtyp (wenn keine Zahl, dann 1)
        vehicle_patterns = {
            'RTW': [r'(?:(\d+)\s*(?:x\s*)?\s*)?(?:Rettungswagen?|RTW)'],
            'NEF': [r'(?:(\d+)\s*(?:x\s*)?\s*)?(?:Notarzteinsatzfahrzeuge?|NEF)'],
            'KTW': [r'(?:(\d+)\s*(?:x\s*)?\s*)?(?:Krankentransportwagen?|KTW)'],
            'NAW': [r'(?:(\d+)\s*(?:x\s*)?\s*)?(?:Notarztwagen?|NAW)'],
            'RTH': [r'(?:(\d+)\s*(?:x\s*)?\s*)?(?:Rettungshubschrauber|RTH)'],
            'ITW': [r'(?:(\d+)\s*(?:x\s*)?\s*)?(?:Intensivtransportwagen?|ITW)'],
            'LF': [r'(?:(\d+)\s*(?:x\s*)?\s*)?(?:Löschfahrzeuge?|LF)'],
            'DLK': [r'(?:(\d+)\s*(?:x\s*)?\s*)?(?:Drehleitern?|DLK)'],
            'TLF': [r'(?:(\d+)\s*(?:x\s*)?\s*)?(?:Tanklöschfahrzeuge?|TLF)'],
            'RW': [r'(?:(\d+)\s*(?:x\s*)?\s*)?(?:Rüstwagen?|RW)'],
            'GW': [r'(?:(\d+)\s*(?:x\s*)?\s*)?(?:Gerätewagen?|GW)(?!\-)'],  # Nicht GW-A, GW-L etc.
            'ELW': [r'(?:(\d+)\s*(?:x\s*)?\s*)?(?:Einsatzleitwagen?|ELW)'],
            'MTW': [r'(?:(\d+)\s*(?:x\s*)?\s*)?(?:Mannschaftstransportwagen?|MTW)'],
            'FuStW': [r'(?:(\d+)\s*(?:x\s*)?\s*)?(?:Funkstreifenwagen?|FuStW|Polizeimotorr.der)'],
            'GW-A': [r'(?:(\d+)\s*(?:x\s*)?\s*)?(?:GW-A|GW\s*A)'],
            'GW-L': [r'(?:(\d+)\s*(?:x\s*)?\s*)?(?:GW-L|GW\s*L)'],
            'GW-Öl': [r'(?:(\d+)\s*(?:x\s*)?\s*)?(?:GW-Öl|GW\s*Öl)'],
        }

        for vehicle_type, patterns in vehicle_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, missing_text, re.IGNORECASE)
                if matches:
                    # Wenn Zahl gefunden, summiere sie; wenn leer (keine Zahl), zähle als 1
                    count = sum(int(m) if m else 1 for m in matches)
                    if vehicle_type in requirements:
                        requirements[vehicle_type] = max(requirements[vehicle_type], count)
                    else:
                        requirements[vehicle_type] = count

        return requirements

    def select_vehicles_intelligently(self, available_vehicles, requirements, soup, mission_id, mission_title=""):
        """Wählt intelligent Fahrzeuge basierend auf Anforderungen aus"""
        try:
            mission_requirements = {}

            # STRATEGIE 1 (PRIORITÄT): Parse missing_text - das ist was JETZT fehlt!
            missing_texts = requirements.get('missing', [])
            self.logger.debug(f"Missing texts: {missing_texts}")

            for missing_text in missing_texts:
                if missing_text:  # Nur wenn nicht leer
                    parsed = self.parse_missing_text(missing_text)
                    for vtype, count in parsed.items():
                        if vtype in mission_requirements:
                            mission_requirements[vtype] = max(mission_requirements[vtype], count)
                        else:
                            mission_requirements[vtype] = count

            if mission_requirements:
                self.logger.info(f"{Fore.CYAN}🔍 Anforderungen aus missing_text geparst: {mission_requirements}")

            # STRATEGIE 2 (FALLBACK): Wenn missing_text leer, nutze Cache
            if not mission_requirements:
                mission_type_id = self.get_mission_type_from_help(mission_id, soup)
                if mission_type_id:
                    mission_requirements = self.get_mission_requirements_from_cache(mission_type_id)
                    if mission_requirements:
                        self.logger.info(f"{Fore.CYAN}📦 Anforderungen aus Cache geladen (Type-ID: {mission_type_id})")

            # STRATEGIE 3 (FALLBACK): Wenn nicht im Cache, parse Hilfe-Seite
            if not mission_requirements:
                mission_requirements = self.get_mission_requirements_from_help(mission_id, soup)
                if mission_requirements:
                    self.logger.info(f"{Fore.CYAN}📄 Anforderungen aus Hilfe-Seite geparst")

            # Berücksichtige bereits unterwegs befindliche Fahrzeuge
            en_route_vehicles = requirements.get('en_route', [])
            on_scene_vehicles = requirements.get('on_scene', [])

            # Wenn immer noch keine Anforderungen gefunden wurden
            if not mission_requirements:
                # Prüfe ob bereits Fahrzeuge unterwegs sind
                if en_route_vehicles or on_scene_vehicles:
                    self.logger.info(f"{Fore.GREEN}Keine Anforderungen gefunden, aber Fahrzeuge bereits unterwegs/vor Ort")
                    return []
                else:
                    # NEUE STRATEGIE: Schicke mindestens 1 Fahrzeug als Vorhut
                    # Versuche anhand des Einsatznamens zu erraten, welcher Typ benötigt wird
                    mission_name = mission_title if mission_title else ""

                    self.logger.info(f"{Fore.CYAN}🔍 Mission Name für Keyword-Erkennung: '{mission_name}'")

                    # Rettungsdienst-Keywords
                    rettungsdienst_keywords = [
                        'sturz', 'patient', 'person', 'verletz', 'unfall', 'notfall',
                        'bewusstlos', 'schmerz', 'atemnot', 'herzinfarkt', 'schlaganfall',
                        'vergiftung', 'unterkühlung', 'überhitzung', 'krampf', 'blutung',
                        'geburt', 'reanimation', 'ertrinken', 'erstick', 'verbrennung',
                        'verätzung', 'amputation', 'quetsch', 'einklemm'
                    ]

                    # Feuerwehr-Keywords
                    feuerwehr_keywords = [
                        'brand', 'feuer', 'rauch', 'explosion', 'gas', 'öl',
                        'wasser', 'überschwemmung', 'unwetter', 'baum', 'tier'
                    ]

                    # Polizei-Keywords
                    polizei_keywords = [
                        'randal', 'einbruch', 'diebstahl', 'raub', 'schlägerei',
                        'bedrohung', 'verdächtig', 'vermisst', 'gefahr'
                    ]

                    mission_name_lower = mission_name.lower()

                    if any(keyword in mission_name_lower for keyword in rettungsdienst_keywords):
                        self.logger.info(f"{Fore.YELLOW}⚠️ Keine Anforderungen gefunden - schicke RTW+NEF (Rettungsdienst-Einsatz)")
                        mission_requirements = {'RTW': 1, 'NEF': 1}
                    elif any(keyword in mission_name_lower for keyword in polizei_keywords):
                        self.logger.info(f"{Fore.YELLOW}⚠️ Keine Anforderungen gefunden - schicke FuStW (Polizei-Einsatz)")
                        mission_requirements = {'FuStW': 1}
                    elif any(keyword in mission_name_lower for keyword in feuerwehr_keywords):
                        self.logger.info(f"{Fore.YELLOW}⚠️ Keine Anforderungen gefunden - schicke LF (Feuerwehr-Einsatz)")
                        mission_requirements = {'LF': 1}
                    else:
                        # Standard: LF als Vorhut
                        self.logger.info(f"{Fore.YELLOW}⚠️ Keine Anforderungen gefunden - schicke LF als Vorhut (unbekannter Typ)")
                        mission_requirements = {'LF': 1}

            # Zähle bereits unterwegs befindliche Fahrzeuge nach Typ
            dispatched_by_type = {}
            for vehicle in en_route_vehicles + on_scene_vehicles:
                vtype = vehicle.get_text(strip=True).upper()
                # Prüfe gegen alle Anforderungen
                for req_type in mission_requirements.keys():
                    if req_type.upper() in vtype or vtype in req_type.upper():
                        dispatched_by_type[req_type] = dispatched_by_type.get(req_type, 0) + 1
                        break

            # Wähle Fahrzeuge basierend auf Anforderungen
            selected_vehicles = []

            for req_type, req_count in mission_requirements.items():
                # Zähle bereits unterwegs befindliche Fahrzeuge dieses Typs
                already_sent = dispatched_by_type.get(req_type, 0)

                # Berechne wie viele noch benötigt werden
                still_needed = max(0, req_count - already_sent)

                if still_needed > 0:
                    self.logger.info(f"{Fore.CYAN}Benötige noch {still_needed}x {req_type} (bereits {already_sent} unterwegs)")

                    # Finde passende Fahrzeuge für diesen Typ
                    found_for_this_type = 0
                    for vehicle in available_vehicles:
                        if found_for_this_type >= still_needed:
                            break

                        # Prüfe ob Fahrzeug zum Typ passt
                        vehicle_label = vehicle.find_next('label', class_='mission_vehicle_label')
                        if vehicle_label and self.match_vehicle_to_requirement(vehicle_label, req_type):
                            if vehicle not in selected_vehicles:
                                selected_vehicles.append(vehicle)
                                found_for_this_type += 1
                                self.logger.info(f"{Fore.GREEN}  ✓ Wähle {vehicle_label.get_text(strip=True)}")

                    # Warnung wenn nicht genug Fahrzeuge gefunden wurden
                    if found_for_this_type < still_needed:
                        self.logger.warning(f"{Fore.YELLOW}⚠ Nur {found_for_this_type}/{still_needed} {req_type} verfügbar!")
                else:
                    self.logger.info(f"{Fore.GREEN}✓ {req_type}: Anforderung bereits erfüllt ({already_sent}/{req_count})")

            if not selected_vehicles:
                self.logger.info(f"{Fore.GREEN}Alle Anforderungen bereits erfüllt")

            return selected_vehicles

        except Exception as e:
            self.logger.error(f"{Fore.RED}Fehler bei intelligenter Fahrzeugauswahl: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return []

    def handle_follow_up(self, mission_id):
        """Behandelt Nachalarmierungen"""
        try:
            self.logger.info(f"{Fore.CYAN}Bearbeite Nachalarmierung für Einsatz {mission_id}")

            # Hole Einsatzseite
            response = self.session.get(f'{self.base_url}/missions/{mission_id}')
            soup = BeautifulSoup(response.content, 'html.parser')

            # Prüfe auf Nachalarmierungs-Button
            follow_up_button = soup.find('a', {'class': 'btn', 'href': lambda x: x and 'alarm' in x})

            if follow_up_button:
                # Alarmiere zusätzliche Fahrzeuge
                return self.dispatch_vehicles(mission_id)

            return False

        except Exception as e:
            self.logger.error(f"{Fore.RED}Fehler bei Nachalarmierung {mission_id}: {e}")
            return False

    def handle_radio_messages(self):
        """Bearbeitet Sprechwünsche (Patiententransporte) mit Selenium"""
        try:
            self.logger.info(f"{Fore.CYAN}🔍 Prüfe auf Sprechwünsche...")

            # Öffne die Einsatzliste
            self.driver.get(f'{self.base_url}/')
            time.sleep(2)

            # DEBUG: Speichere HTML
            try:
                html = self.driver.page_source
                with open('debug_sprechwunsch.html', 'w', encoding='utf-8') as f:
                    f.write(html)
                self.logger.info(f"{Fore.MAGENTA}[DEBUG] HTML gespeichert: debug_sprechwunsch.html")
            except:
                pass

            # Suche nach Sprechwunsch-Fahrzeug-Links im Funk-Panel
            vehicle_links = []

            # Die Sprechwünsche sind im Funk-Panel unter "radio_messages_important"
            try:
                # Finde alle Fahrzeug-Links (nicht die "Zum Einsatz" Buttons!)
                # Format: <a href="/vehicles/XXXXX" class="btn btn-xs btn-default lightbox-open">Fahrzeugname</a>
                vehicle_links = self.driver.find_elements(By.CSS_SELECTOR, "#radio_messages_important a[href*='/vehicles/']")
                self.logger.info(f"{Fore.YELLOW}📞 {len(vehicle_links)} Sprechwünsche im Funk-Panel gefunden")
            except Exception as e:
                self.logger.warning(f"{Fore.YELLOW}⚠ Fehler beim Suchen von Sprechwünschen: {e}")

            if not vehicle_links:
                self.logger.info(f"{Fore.CYAN}✓ Keine Sprechwünsche gefunden")
                return 0

            self.logger.info(f"{Fore.YELLOW}📞 Gefunden: {len(vehicle_links)} Sprechwünsche")

            processed = 0
            # Hole die Fahrzeug-URLs aus den Links
            vehicle_urls = []
            for link in vehicle_links[:5]:  # Max 5 pro Durchlauf
                try:
                    url = link.get_attribute('href')
                    if url:
                        vehicle_urls.append(url)
                except:
                    pass

            # Bearbeite jeden Sprechwunsch
            for url in vehicle_urls:
                try:
                    # Öffne das Fahrzeug
                    self.driver.get(url)
                    time.sleep(2)

                    # Extrahiere Fahrzeug-ID aus URL
                    import re
                    match = re.search(r'/vehicles/(\d+)', url)
                    if not match:
                        continue

                    vehicle_id = match.group(1)
                    self.logger.info(f"{Fore.CYAN}  Bearbeite Sprechwunsch (Fahrzeug {vehicle_id})...")

                    # Sprechwunsch = Patient will ins Krankenhaus
                    # Suche den ersten "Anfahren" Button (nächstes Krankenhaus)
                    try:
                        # Finde alle "Anfahren" Buttons
                        anfahren_buttons = self.driver.find_elements(By.XPATH, "//a[contains(@class, 'btn-success') and contains(text(), 'Anfahren')]")

                        if anfahren_buttons:
                            # Klicke den ersten Button (nächstes Krankenhaus)
                            anfahren_buttons[0].click()
                            time.sleep(1)

                            self.logger.info(f"{Fore.GREEN}✓ Sprechwunsch bearbeitet (Krankenhaus ausgewählt)")
                            processed += 1
                        else:
                            self.logger.warning(f"{Fore.YELLOW}⚠ Keine Krankenhäuser gefunden")
                    except Exception as e:
                        self.logger.warning(f"{Fore.YELLOW}⚠ Fehler beim Auswählen des Krankenhauses: {e}")

                    # Zurück zur Hauptseite
                    self.driver.get(f'{self.base_url}/')
                    time.sleep(1)

                except Exception as e:
                    self.logger.warning(f"{Fore.YELLOW}⚠ Fehler beim Bearbeiten eines Sprechwunsches: {e}")
                    # Zurück zur Hauptseite
                    self.driver.get(f'{self.base_url}/')
                    time.sleep(1)

            if processed > 0:
                self.logger.info(f"{Fore.GREEN}✓ {processed} Sprechwünsche bearbeitet")

            return processed

        except Exception as e:
            self.logger.error(f"{Fore.RED}Fehler beim Abrufen von Sprechwünschen: {e}")
            return 0

    def check_radio_messages(self):
        """Prüft und bearbeitet Sprechwünsche (kann nach jedem Einsatz aufgerufen werden)"""
        try:
            self.logger.info(f"{Fore.MAGENTA}🔍 Prüfe auf Sprechwünsche...")
            self.handle_radio_messages()
        except Exception as e:
            self.logger.warning(f"{Fore.YELLOW}⚠ Fehler beim Prüfen von Sprechwünschen: {e}")

    def process_missions(self):
        """Verarbeitet alle offenen Einsätze"""
        # Bearbeite Sprechwünsche vor dem Start
        try:
            self.logger.info(f"{Fore.MAGENTA}>>> Starte Sprechwunsch-Prüfung...")
            self.handle_radio_messages()
            self.logger.info(f"{Fore.MAGENTA}>>> Sprechwunsch-Prüfung abgeschlossen")
        except Exception as e:
            self.logger.error(f"{Fore.RED}Fehler beim Bearbeiten von Sprechwünschen: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

        missions = self.get_missions()

        if not missions:
            self.logger.info(f"{Fore.CYAN}Keine offenen Einsätze gefunden")
            return

        self.logger.info(f"{Fore.CYAN}Gefunden: {len(missions)} offene Einsätze")

        # Filtere nur GELBE oder ROTE Einsätze mit fehlenden Fahrzeugen
        filtered_missions = []
        for mission in missions:
            icon = mission.get('icon', '')
            missing_text_raw = mission.get('missing_text', '')

            # Parse missing_text wenn es JSON/Dict ist
            missing_text = missing_text_raw
            if isinstance(missing_text_raw, dict):
                missing_text = missing_text_raw.get('vehicles', '')
            elif isinstance(missing_text_raw, str) and missing_text_raw.strip().startswith('{'):
                try:
                    import json
                    missing_data = json.loads(missing_text_raw)
                    missing_text = missing_data.get('vehicles', '')
                except:
                    pass

            # Gelbe oder rote Einsätze (dringend)
            # Icons können _rot (deutsch) oder _red (englisch) sein
            is_urgent = '_rot' in icon.lower() or '_red' in icon.lower() or 'yellow' in icon.lower() or '_gelb' in icon.lower()

            # Nur Einsätze mit fehlenden Fahrzeugen
            has_missing = missing_text and missing_text.strip()

            if is_urgent and has_missing:
                filtered_missions.append(mission)
                color = "🔴" if '_rot' in icon.lower() or '_red' in icon.lower() else "🟡"
                self.logger.debug(f"{Fore.CYAN}  ✓ {color} {mission['title']} - Fehlend: {missing_text}")
            else:
                skip_reason = []
                if not is_urgent:
                    skip_reason.append("nicht dringend (gelb/rot)")
                if not has_missing:
                    skip_reason.append("keine fehlenden Fahrzeuge")
                self.logger.debug(f"{Fore.YELLOW}  ⊘ {mission['title']} - Übersprungen ({', '.join(skip_reason)})")

        if not filtered_missions:
            self.logger.info(f"{Fore.CYAN}Keine dringenden Einsätze mit fehlenden Fahrzeugen gefunden")
            return

        self.logger.info(f"{Fore.GREEN}✓ {len(filtered_missions)} dringende Einsätze mit fehlenden Fahrzeugen")

        max_missions = self.config.get('bot', {}).get('max_missions_per_cycle', 10)
        processed = 0

        for mission in filtered_missions[:max_missions]:
            if processed >= max_missions:
                break

            mission_id = mission['id']
            mission_title = mission['title']
            missing_text_raw = mission.get('missing_text', '')
            patients_count = mission.get('patients_count', 0)
            possible_patients_count = mission.get('possible_patients_count', 0)

            # Parse missing_text - DIREKT hier, SOFORT!
            missing_text = missing_text_raw

            # Wenn es ein Dict ist (von der API)
            if isinstance(missing_text_raw, dict):
                missing_text = missing_text_raw.get('vehicles', '')
            # Wenn es ein JSON-String ist
            elif isinstance(missing_text_raw, str) and missing_text_raw.strip().startswith('{'):
                try:
                    import json
                    missing_data = json.loads(missing_text_raw)
                    missing_text = missing_data.get('vehicles', '')
                except:
                    pass

            self.logger.info(f"{Fore.YELLOW}[{processed+1}/{min(len(filtered_missions), max_missions)}] {mission_title} (ID: {mission_id})")
            self.logger.info(f"{Fore.YELLOW}  Fehlend: {missing_text}")
            if patients_count > 0:
                self.logger.info(f"{Fore.CYAN}  👤 Patienten: {patients_count}")
            elif possible_patients_count > 0:
                self.logger.info(f"{Fore.CYAN}  👤 Mögliche Patienten: {possible_patients_count}")

            # Hole Einsatzdetails
            details = self.get_mission_details(mission_id)

            if details:
                # Alarmiere Fahrzeuge
                if self.config.get('bot', {}).get('auto_dispatch', True):
                    self.dispatch_vehicles(mission_id, mission_title, missing_text_from_api=missing_text,
                                         patients_count=patients_count, possible_patients_count=possible_patients_count)
                    time.sleep(self.config.get('bot', {}).get('delay_between_actions', 2))

                # Behandle Nachalarmierung
                if details['has_follow_up'] and self.config.get('bot', {}).get('auto_follow_up', True):
                    self.handle_follow_up(mission_id)
                    time.sleep(self.config.get('bot', {}).get('delay_between_actions', 2))

                # Prüfe nach jedem Einsatz auf neue Sprechwünsche
                self.check_radio_messages()

            processed += 1

        self.logger.info(f"{Fore.GREEN}✓ {processed} Einsätze bearbeitet")

    def run(self):
        """Hauptschleife des Bots"""
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}  Leitstellenspiel.de Bot (Selenium)")
        print(f"{Fore.CYAN}{'='*60}\n")

        # Initialisiere Browser
        headless = self.config.get('bot', {}).get('headless_browser', True)
        if not self.init_browser(headless=headless):
            return

        try:
            # Login
            if not self.login():
                self.close_browser()
                return

            print(f"\n{Fore.GREEN}Bot läuft... (Strg+C zum Beenden)\n")

            cycle = 0
            while True:
                cycle += 1
                self.logger.info(f"{Fore.MAGENTA}{'='*60}")
                self.logger.info(f"{Fore.MAGENTA}Zyklus #{cycle} - {datetime.now().strftime('%H:%M:%S')}")
                self.logger.info(f"{Fore.MAGENTA}{'='*60}")

                # Verarbeite Einsätze
                self.process_missions()

                # Warte bis zum nächsten Durchlauf
                wait_time = self.config.get('bot', {}).get('check_interval', 30)
                self.logger.info(f"{Fore.CYAN}Warte {wait_time} Sekunden bis zum nächsten Durchlauf...\n")
                time.sleep(wait_time)

        except KeyboardInterrupt:
            print(f"\n\n{Fore.YELLOW}Bot wird beendet...")
            self.logger.info("Bot wurde vom Benutzer beendet")
        except Exception as e:
            self.logger.error(f"{Fore.RED}Unerwarteter Fehler: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
        finally:
            self.close_browser()


class BotGUI:
    def __init__(self):
        # Erstelle Cache-Ordner
        self.cache_dir = 'cache'
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

        self.settings_file = os.path.join(self.cache_dir, 'settings.json')

        self.root = ctk.CTk()
        self.root.title("Leitstellenspiel Bot - Professional Edition")
        self.root.geometry("1400x900")

        # Bot-Instanz
        self.bot = None
        self.bot_thread = None
        self.running = False
        self.start_time = None

        # Einstellungen (werden im GUI gespeichert)
        self.settings = self.load_settings()

        # Statistiken
        self.stats = {
            'missions_processed': 0,
            'vehicles_dispatched': 0,
            'runtime': 0,
            'credits_earned': 0
        }

        # Log-Queue
        self.log_queue = queue.Queue()

        self.setup_ui()
        self.update_log_display()
        self.update_stats_display()

    def load_settings(self):
        """Lädt Einstellungen aus cache/settings.json oder gibt Defaults zurück"""
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {
                'email': '',
                'password': '',
                'check_interval': 30,
                'max_missions': 10,
                'headless': True,
                'auto_dispatch': True,
                'auto_follow_up': True
            }

    def save_settings(self):
        """Speichert Einstellungen in cache/settings.json"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            self.add_log(f"FEHLER beim Speichern: {e}")

    def save_settings_from_ui(self):
        """Speichert Einstellungen aus dem UI"""
        self.settings['email'] = self.email_entry.get()
        self.settings['password'] = self.password_entry.get()

        try:
            self.settings['check_interval'] = int(self.interval_entry.get())
        except:
            self.settings['check_interval'] = 30

        try:
            self.settings['max_missions'] = int(self.max_missions_entry.get())
        except:
            self.settings['max_missions'] = 10

        self.settings['headless'] = self.headless_var.get()
        self.settings['auto_dispatch'] = self.auto_dispatch_var.get()
        self.settings['auto_follow_up'] = self.auto_follow_up_var.get()
        self.settings['alliance_missions'] = self.alliance_missions_var.get()
        self.settings['auto_expand'] = self.auto_expand_var.get()
        self.settings['auto_update'] = self.auto_update_var.get()

        self.save_settings()
        self.add_log("Einstellungen gespeichert!")

        # Zeige Bestätigung
        self.show_notification("Einstellungen erfolgreich gespeichert!")

    def show_notification(self, message):
        """Zeigt eine Benachrichtigung"""
        # Erstelle Notification-Label
        notif = ctk.CTkLabel(
            self.root,
            text=message,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2ecc71",
            text_color="white",
            corner_radius=10
        )
        notif.place(relx=0.5, rely=0.95, anchor="center")

        # Entferne nach 2 Sekunden
        self.root.after(2000, notif.destroy)

    def setup_ui(self):
        """Erstellt das UI"""

        # Header
        header_frame = ctk.CTkFrame(self.root, height=80, corner_radius=0, fg_color="#1a1a1a")
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)

        title_label = ctk.CTkLabel(
            header_frame,
            text="LEITSTELLENSPIEL BOT",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color="#3498db"
        )
        title_label.pack(side="left", padx=30, pady=20)

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Professional Edition v2.0",
            font=ctk.CTkFont(size=14),
            text_color="#7f8c8d"
        )
        subtitle_label.pack(side="left", padx=10, pady=20)

        # Tab-System
        self.tabview = ctk.CTkTabview(self.root)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)

        # Tabs erstellen
        self.tabview.add("Dashboard")
        self.tabview.add("Einstellungen")

        # Dashboard Tab
        self.setup_dashboard_tab()

        # Einstellungen Tab
        self.setup_settings_tab()

    def setup_dashboard_tab(self):
        """Erstellt das Dashboard"""
        dashboard = self.tabview.tab("Dashboard")

        # Container
        main_container = ctk.CTkFrame(dashboard, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Linke Seite - Steuerung & Statistiken
        left_panel = ctk.CTkFrame(main_container, width=400)
        left_panel.pack(side="left", fill="both", padx=(0, 10))
        left_panel.pack_propagate(False)

        # Steuerung
        control_frame = ctk.CTkFrame(left_panel)
        control_frame.pack(fill="x", padx=20, pady=20)

        control_label = ctk.CTkLabel(
            control_frame,
            text="STEUERUNG",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        control_label.pack(pady=(10, 20))

        # Start/Stop Button
        self.start_button = ctk.CTkButton(
            control_frame,
            text="BOT STARTEN",
            command=self.toggle_bot,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#2ecc71",
            hover_color="#27ae60"
        )
        self.start_button.pack(fill="x", padx=20, pady=10)

        # Status
        self.status_label = ctk.CTkLabel(
            control_frame,
            text="Status: Gestoppt",
            font=ctk.CTkFont(size=14),
            text_color="#95a5a6"
        )
        self.status_label.pack(pady=(10, 15))

        # Statistiken
        stats_frame = ctk.CTkFrame(left_panel)
        stats_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        stats_label = ctk.CTkLabel(
            stats_frame,
            text="STATISTIKEN",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        stats_label.pack(pady=(10, 20))

        # Statistik-Karten
        self.stats_cards = {}

        stats_data = [
            ("missions", "Einsaetze bearbeitet", "0", "#e74c3c"),
            ("vehicles", "Fahrzeuge alarmiert", "0", "#3498db"),
            ("runtime", "Laufzeit", "00:00:00", "#9b59b6"),
            ("credits", "Credits verdient", "0", "#f39c12")
        ]

        for key, label, value, color in stats_data:
            card = self.create_stat_card(stats_frame, label, value, color)
            self.stats_cards[key] = card
            card.pack(fill="x", padx=20, pady=5)

        # Rechte Seite - Logs
        right_panel = ctk.CTkFrame(main_container)
        right_panel.pack(side="right", fill="both", expand=True)

        log_label = ctk.CTkLabel(
            right_panel,
            text="LIVE LOGS",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        log_label.pack(pady=(10, 10), padx=20, anchor="w")

        # Log-Textfeld
        self.log_text = ctk.CTkTextbox(
            right_panel,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="word"
        )
        self.log_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def setup_settings_tab(self):
        """Erstellt die Einstellungen-Seite"""
        settings_tab = self.tabview.tab("Einstellungen")

        # Container
        container = ctk.CTkFrame(settings_tab, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=50, pady=30)

        # Titel
        title = ctk.CTkLabel(
            container,
            text="EINSTELLUNGEN",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#3498db"
        )
        title.pack(pady=(0, 30))

        # Login-Bereich
        login_frame = ctk.CTkFrame(container)
        login_frame.pack(fill="x", pady=(0, 20))

        login_label = ctk.CTkLabel(
            login_frame,
            text="Login-Daten",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        login_label.pack(pady=(20, 20), padx=20, anchor="w")

        # Email
        email_frame = ctk.CTkFrame(login_frame, fg_color="transparent")
        email_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(email_frame, text="Email:", font=ctk.CTkFont(size=14), width=150, anchor="w").pack(side="left", padx=(0, 10))
        self.email_entry = ctk.CTkEntry(email_frame, placeholder_text="deine@email.de", height=40, font=ctk.CTkFont(size=14))
        self.email_entry.pack(side="left", fill="x", expand=True)
        self.email_entry.insert(0, self.settings.get('email', ''))

        # Passwort
        password_frame = ctk.CTkFrame(login_frame, fg_color="transparent")
        password_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(password_frame, text="Passwort:", font=ctk.CTkFont(size=14), width=150, anchor="w").pack(side="left", padx=(0, 10))
        self.password_entry = ctk.CTkEntry(password_frame, placeholder_text="Passwort", show="*", height=40, font=ctk.CTkFont(size=14))
        self.password_entry.pack(side="left", fill="x", expand=True, pady=(0, 20))
        self.password_entry.insert(0, self.settings.get('password', ''))

        # Bot-Einstellungen
        bot_frame = ctk.CTkFrame(container)
        bot_frame.pack(fill="x", pady=(0, 20))

        bot_label = ctk.CTkLabel(
            bot_frame,
            text="Bot-Einstellungen",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        bot_label.pack(pady=(20, 20), padx=20, anchor="w")

        # Check Interval
        interval_frame = ctk.CTkFrame(bot_frame, fg_color="transparent")
        interval_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(interval_frame, text="Check-Intervall (Sekunden):", font=ctk.CTkFont(size=14), width=250, anchor="w").pack(side="left", padx=(0, 10))
        self.interval_entry = ctk.CTkEntry(interval_frame, width=100, height=40, font=ctk.CTkFont(size=14))
        self.interval_entry.pack(side="left")
        self.interval_entry.insert(0, str(self.settings.get('check_interval', 30)))

        # Max Missions
        missions_frame = ctk.CTkFrame(bot_frame, fg_color="transparent")
        missions_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(missions_frame, text="Max. Einsätze pro Durchlauf:", font=ctk.CTkFont(size=14), width=250, anchor="w").pack(side="left", padx=(0, 10))
        self.max_missions_entry = ctk.CTkEntry(missions_frame, width=100, height=40, font=ctk.CTkFont(size=14))
        self.max_missions_entry.pack(side="left")
        self.max_missions_entry.insert(0, str(self.settings.get('max_missions', 10)))

        # Checkboxen
        check_frame = ctk.CTkFrame(bot_frame, fg_color="transparent")
        check_frame.pack(fill="x", padx=20, pady=20)

        self.headless_var = ctk.BooleanVar(value=self.settings.get('headless', True))
        self.headless_check = ctk.CTkCheckBox(
            check_frame,
            text="Headless Mode (Browser unsichtbar)",
            variable=self.headless_var,
            font=ctk.CTkFont(size=14)
        )
        self.headless_check.pack(anchor="w", pady=5)

        self.auto_dispatch_var = ctk.BooleanVar(value=self.settings.get('auto_dispatch', True))
        self.auto_dispatch_check = ctk.CTkCheckBox(
            check_frame,
            text="Automatische Alarmierung",
            variable=self.auto_dispatch_var,
            font=ctk.CTkFont(size=14)
        )
        self.auto_dispatch_check.pack(anchor="w", pady=5)

        self.auto_follow_up_var = ctk.BooleanVar(value=self.settings.get('auto_follow_up', True))
        self.auto_follow_up_check = ctk.CTkCheckBox(
            check_frame,
            text="Automatische Nachalarmierung",
            variable=self.auto_follow_up_var,
            font=ctk.CTkFont(size=14)
        )
        self.auto_follow_up_check.pack(anchor="w", pady=5)

        self.alliance_missions_var = ctk.BooleanVar(value=self.settings.get('alliance_missions', False))
        self.alliance_missions_check = ctk.CTkCheckBox(
            check_frame,
            text="Verbandseinsätze bearbeiten",
            variable=self.alliance_missions_var,
            font=ctk.CTkFont(size=14)
        )
        self.alliance_missions_check.pack(anchor="w", pady=5)

        self.auto_expand_var = ctk.BooleanVar(value=self.settings.get('auto_expand', False))
        self.auto_expand_check = ctk.CTkCheckBox(
            check_frame,
            text="Automatischer Gebäude-Ausbau",
            variable=self.auto_expand_var,
            font=ctk.CTkFont(size=14)
        )
        self.auto_expand_check.pack(anchor="w", pady=5)

        self.auto_update_var = ctk.BooleanVar(value=self.settings.get('auto_update', True))
        self.auto_update_check = ctk.CTkCheckBox(
            check_frame,
            text="Automatische Updates",
            variable=self.auto_update_var,
            font=ctk.CTkFont(size=14)
        )
        self.auto_update_check.pack(anchor="w", pady=(5, 20))

        # Speichern Button
        save_button = ctk.CTkButton(
            container,
            text="EINSTELLUNGEN SPEICHERN",
            command=self.save_settings_from_ui,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#2ecc71",
            hover_color="#27ae60"
        )
        save_button.pack(fill="x", pady=20)

    def create_stat_card(self, parent, label, value, color):
        """Erstellt eine Statistik-Karte"""
        card_frame = ctk.CTkFrame(parent, fg_color=color, corner_radius=10)

        value_label = ctk.CTkLabel(
            card_frame,
            text=value,
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="white"
        )
        value_label.pack(pady=(15, 5))

        label_label = ctk.CTkLabel(
            card_frame,
            text=label,
            font=ctk.CTkFont(size=12),
            text_color="white"
        )
        label_label.pack(pady=(0, 15))

        # Speichere die Labels für Updates
        card_frame.value_label = value_label
        card_frame.label_label = label_label

        return card_frame

    def toggle_bot(self):
        """Startet oder stoppt den Bot"""
        if not self.running:
            self.start_bot()
        else:
            self.stop_bot()

    def start_bot(self):
        """Startet den Bot"""
        # Validiere Eingaben
        if not self.email_entry.get() or not self.password_entry.get():
            self.add_log("FEHLER: Bitte Email und Passwort eingeben!")
            return

        # Speichere Einstellungen
        self.save_settings_from_ui()

        self.running = True
        self.start_time = datetime.now()

        # Update UI
        self.start_button.configure(
            text="BOT STOPPEN",
            fg_color="#e74c3c",
            hover_color="#c0392b"
        )
        self.status_label.configure(
            text="Status: Laeuft",
            text_color="#2ecc71"
        )

        # Starte Bot in separatem Thread
        self.bot_thread = threading.Thread(target=self.run_bot, daemon=True)
        self.bot_thread.start()

        self.add_log("Bot gestartet!")

    def stop_bot(self):
        """Stoppt den Bot"""
        self.running = False

        # Update UI
        self.start_button.configure(
            text="BOT STARTEN",
            fg_color="#2ecc71",
            hover_color="#27ae60"
        )
        self.status_label.configure(
            text="Status: Gestoppt",
            text_color="#95a5a6"
        )

        self.add_log("Bot gestoppt!")

    def run_bot(self):
        """Führt den Bot aus"""
        try:
            # Erstelle Bot-Instanz
            self.add_log("Initialisiere Bot...")

            # Lade gespeicherte Einstellungen
            settings = self.load_settings()

            # Erstelle temporäre config.json mit GUI-Einstellungen
            temp_config = {
                "credentials": {
                    "email": settings.get('email', ''),
                    "password": settings.get('password', '')
                },
                "headless": settings.get('headless', True),
                "bot": {
                    "check_interval": settings.get('check_interval', 30),
                    "max_missions_per_cycle": settings.get('max_missions', 10),
                    "auto_dispatch": settings.get('auto_dispatch', True),
                    "auto_backup": settings.get('auto_backup', True)
                },
                "logging": {
                    "level": "INFO",
                    "file": "bot.log"
                },
                "cache": {
                    "mission_cache_file": "mission_cache.json",
                    "cache_expiry_hours": 24
                },
                "features": {
                    "alliance_mission": settings.get('alliance_missions', False)
                }
            }

            # Speichere temporär in config.json
            import json
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(temp_config, f, indent=4, ensure_ascii=False)

            self.bot = LeitstellenspielBot()

            # Füge GUI-Logger-Handler hinzu
            import logging
            class GUILogHandler(logging.Handler):
                def __init__(self, gui_callback):
                    super().__init__()
                    self.gui_callback = gui_callback

                def emit(self, record):
                    try:
                        msg = self.format(record)
                        # Entferne ANSI-Farbcodes
                        import re
                        msg = re.sub(r'\x1b\[[0-9;]*m', '', msg)
                        self.gui_callback(msg)
                    except:
                        pass

            gui_handler = GUILogHandler(self.add_log)
            gui_handler.setFormatter(logging.Formatter('%(message)s'))
            self.bot.logger.addHandler(gui_handler)

            self.add_log(f"Email: {settings.get('email', 'Nicht gesetzt')}")
            self.add_log(f"Headless: {'Ja' if settings.get('headless', True) else 'Nein'}")
            self.add_log(f"Intervall: {settings.get('check_interval', 30)}s")

            # Initialisiere Browser
            self.add_log("Starte Browser...")
            headless = settings.get('headless', True)

            try:
                if not self.bot.init_browser(headless=headless):
                    self.add_log("FEHLER: Browser konnte nicht gestartet werden!")
                    self.add_log("Tipp: Installiere Chrome oder Firefox")
                    self.stop_bot()
                    return
            except Exception as e:
                self.add_log(f"FEHLER beim Browser-Start: {str(e)}")
                self.stop_bot()
                return

            self.add_log("Browser gestartet!")

            # Login
            self.add_log("Versuche Login...")
            try:
                if not self.bot.login():
                    self.add_log("FEHLER: Login fehlgeschlagen!")
                    self.add_log("Prüfe Email und Passwort in den Einstellungen!")
                    self.stop_bot()
                    return
            except Exception as e:
                self.add_log(f"FEHLER beim Login: {str(e)}")
                self.stop_bot()
                return

            self.add_log("Login erfolgreich!")

            # Update-Check
            if settings.get('auto_update', True):
                try:
                    self.add_log("Prüfe auf Updates...")
                    has_update, version, release_data = self.bot.check_for_updates()
                    if has_update:
                        self.add_log(f"🆕 Update verfügbar: Version {version}")
                        self.add_log("🔄 Starte automatisches Update...")

                        # Führe Update durch
                        if self.bot.auto_update(release_data):
                            self.add_log("✓ Update erfolgreich - Bot wird neu gestartet...")
                            # Der Bot wird automatisch neu gestartet
                        else:
                            self.add_log("⚠ Update fehlgeschlagen - fahre mit alter Version fort")
                except Exception as e:
                    self.add_log(f"⚠ Update-Check Fehler: {e}")
                    pass  # Ignoriere Update-Check-Fehler

            # Lade API-Daten
            self.add_log("Lade Fahrzeuge und Gebaeude...")
            try:
                self.bot.get_api_vehicles()
                self.bot.get_api_buildings()
                self.add_log(f"Geladen: {len(self.bot.api_vehicles)} Fahrzeuge, {len(self.bot.api_buildings)} Gebaeude")
            except Exception as e:
                self.add_log(f"FEHLER beim Laden der API-Daten: {str(e)}")
                # Weiter machen, auch wenn API-Daten nicht geladen werden konnten

            # Hole Start-Credits
            start_credits = self.bot.get_credits()
            if start_credits is not None:
                self.add_log(f"Start-Credits: {start_credits:,}")
                self.stats['start_credits'] = start_credits
            else:
                self.stats['start_credits'] = 0

            # Hauptschleife
            cycle = 0
            while self.running:
                cycle += 1
                self.add_log(f"\n=== Zyklus #{cycle} ===")

                try:
                    # Session-Check (alle 5 Zyklen)
                    if cycle % 5 == 0:
                        if not self.bot.ensure_logged_in():
                            self.add_log("⚠ Session-Check fehlgeschlagen - stoppe Bot")
                            self.stop_bot()
                            break

                    # SPRECHWUNSCH-PRÜFUNG VOR EINSÄTZEN
                    try:
                        self.add_log(">>> Starte Sprechwunsch-Prüfung...")
                        self.bot.handle_radio_messages()
                        self.add_log(">>> Sprechwunsch-Prüfung abgeschlossen")
                    except Exception as e:
                        self.add_log(f"FEHLER beim Bearbeiten von Sprechwünschen: {e}")

                    # Hole Einsätze
                    missions = self.bot.get_missions()
                    self.add_log(f"Gefunden: {len(missions)} offene Einsätze")

                    if len(missions) == 0:
                        self.add_log("Keine Einsaetze vorhanden")
                    else:
                        # Bearbeite Einsätze
                        max_missions = self.bot.config.get('bot', {}).get('max_missions_per_cycle', 10)

                        for i, mission in enumerate(missions[:max_missions], 1):
                            if not self.running:
                                break

                            title = mission.get('title', 'Unbekannt')
                            mission_id = mission.get('id')

                            self.add_log(f"[{i}/{min(len(missions), max_missions)}] {title} (ID: {mission_id})")

                            # Prüfe ob Einsatz Fahrzeuge braucht
                            missing_text = mission.get('missing_text')
                            if missing_text:
                                self.add_log(f"  Fehlend: {missing_text}")

                            # Bearbeite Einsatz
                            try:
                                # Hole Einsatzdetails
                                details = self.bot.get_mission_details(mission_id)

                                if details:
                                    # Alarmiere Fahrzeuge
                                    if self.bot.config.get('bot', {}).get('auto_dispatch', True):
                                        self.add_log(f"  Alarmiere Fahrzeuge...")
                                        self.bot.dispatch_vehicles(mission_id, title)
                                        self.stats['missions_processed'] += 1
                                        time.sleep(self.bot.config.get('bot', {}).get('delay_between_actions', 2))

                                    # Behandle Nachalarmierung
                                    if details.get('has_follow_up') and self.bot.config.get('bot', {}).get('auto_follow_up', True):
                                        self.add_log(f"  Behandle Nachalarmierung...")
                                        self.bot.handle_follow_up(mission_id)
                                        time.sleep(self.bot.config.get('bot', {}).get('delay_between_actions', 2))

                                    self.add_log(f"  OK Einsatz bearbeitet")

                                    # Update Credits
                                    try:
                                        current_credits = self.bot.get_credits()
                                        if current_credits is not None and 'start_credits' in self.stats:
                                            earned = current_credits - self.stats['start_credits']
                                            self.stats['credits_earned'] = earned
                                    except Exception as e:
                                        pass  # Ignoriere Fehler beim Credits-Update

                                    # SPRECHWUNSCH-PRÜFUNG NACH JEDEM EINSATZ
                                    try:
                                        self.add_log("  🔍 Prüfe auf Sprechwünsche...")
                                        self.bot.handle_radio_messages()
                                    except Exception as e:
                                        self.add_log(f"  ⚠ Fehler bei Sprechwunsch-Prüfung: {e}")
                                else:
                                    self.add_log(f"  SKIP Keine Details verfuegbar")

                            except Exception as e:
                                self.add_log(f"  FEHLER: {str(e)}")

                            # Kurze Pause zwischen Einsätzen
                            time.sleep(2)

                    # Gebäude-Ausbau (alle 10 Zyklen)
                    if settings.get('auto_expand', False) and (cycle % 10 == 0):
                        try:
                            self.add_log("🏗️ Prüfe Gebäude-Ausbau...")
                            self.bot.auto_expand_buildings()
                        except Exception as e:
                            self.add_log(f"⚠ Fehler beim Gebäude-Ausbau: {e}")

                    # Warte bis zum nächsten Durchlauf
                    wait_time = self.bot.config.get('check_interval', 30)
                    self.add_log(f"Warte {wait_time} Sekunden bis zum naechsten Durchlauf...")

                    for i in range(wait_time):
                        if not self.running:
                            break
                        time.sleep(1)

                except Exception as e:
                    self.add_log(f"FEHLER im Zyklus: {str(e)}")
                    import traceback
                    self.add_log(traceback.format_exc())
                    time.sleep(10)

        except Exception as e:
            self.add_log(f"KRITISCHER FEHLER: {str(e)}")
            import traceback
            self.add_log(traceback.format_exc())
            self.stop_bot()
        finally:
            if self.bot and self.bot.driver:
                try:
                    self.bot.driver.quit()
                    self.add_log("Browser geschlossen")
                except:
                    pass

    def add_log(self, message):
        """Fügt eine Log-Nachricht hinzu"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.log_queue.put(log_message)

    def update_log_display(self):
        """Aktualisiert die Log-Anzeige"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.insert("end", message)
                self.log_text.see("end")
        except queue.Empty:
            pass

        # Wiederhole alle 100ms
        self.root.after(100, self.update_log_display)

    def update_stats_display(self):
        """Aktualisiert die Statistik-Anzeige"""
        # Einsätze
        self.stats_cards['missions'].value_label.configure(
            text=str(self.stats['missions_processed'])
        )

        # Fahrzeuge
        self.stats_cards['vehicles'].value_label.configure(
            text=str(self.stats['vehicles_dispatched'])
        )

        # Laufzeit
        if self.start_time and self.running:
            runtime = datetime.now() - self.start_time
            hours = int(runtime.total_seconds() // 3600)
            minutes = int((runtime.total_seconds() % 3600) // 60)
            seconds = int(runtime.total_seconds() % 60)
            runtime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            runtime_str = "00:00:00"

        self.stats_cards['runtime'].value_label.configure(text=runtime_str)

        # Credits
        self.stats_cards['credits'].value_label.configure(
            text=f"{self.stats['credits_earned']:,}"
        )

        # Wiederhole alle 1000ms
        self.root.after(1000, self.update_stats_display)

    def run(self):
        """Startet die GUI"""
        self.root.mainloop()


def main():
    """Hauptfunktion"""
    # Log: Main startet
    with open("main_start.log", "w", encoding="utf-8") as f:
        f.write("main() wurde aufgerufen\n")

    try:
        # Prüfe ob customtkinter installiert ist
        import customtkinter
        with open("main_start.log", "a", encoding="utf-8") as f:
            f.write("customtkinter importiert\n")
    except ImportError as e:
        with open("main_start.log", "a", encoding="utf-8") as f:
            f.write(f"customtkinter FEHLER: {e}\n")
        print("FEHLER: customtkinter ist nicht installiert!")
        print("Bitte installieren Sie es mit: pip install customtkinter")
        input("Druecken Sie Enter zum Beenden...")
        return

    # Starte GUI
    with open("main_start.log", "a", encoding="utf-8") as f:
        f.write("Starte BotGUI...\n")

    app = BotGUI()

    with open("main_start.log", "a", encoding="utf-8") as f:
        f.write("BotGUI erstellt, starte run()...\n")

    app.run()

    with open("main_start.log", "a", encoding="utf-8") as f:
        f.write("GUI beendet\n")


if __name__ == "__main__":
    try:
        # Schreibe Start-Log
        with open("startup.log", "w", encoding="utf-8") as f:
            f.write("Bot startet...\n")

        main()

    except Exception as e:
        # Schreibe Fehler in Log
        import traceback
        with open("error.log", "w", encoding="utf-8") as f:
            f.write("FEHLER beim Start:\n")
            f.write(f"{e}\n\n")
            f.write(traceback.format_exc())

        # Zeige Fehler in Console (falls vorhanden)
        print("\n" + "="*60)
        print("FEHLER beim Start:")
        print("="*60)
        print(f"{e}\n")
        print(traceback.format_exc())
        print("="*60)
        input("\nDruecke Enter zum Beenden...")