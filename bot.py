#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Leitstellenspiel.de Bot
Automatisiert das Abarbeiten von Einsätzen und Nachalarmierungen
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import logging
from datetime import datetime
from colorama import init, Fore, Style
import sys
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, NoAlertPresentException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import random
from vehicle_types import VEHICLE_TYPES, CATEGORY_TO_TYPES

# Colorama initialisieren
init(autoreset=True)

class LeitstellenspielBot:
    def __init__(self, config_path='config.json'):
        """Initialisiert den Bot mit der Konfiguration"""
        # Erstelle Cache-Ordner
        self.cache_dir = 'cache'
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

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
                    self.logger.error(f"{Fore.RED}Session abgelaufen! Bitte neu einloggen.")
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
                    selected_count = self.select_vehicles_by_checkboxes(mission_requirements)
                    if selected_count > 0:
                        self.logger.info(f"{Fore.GREEN}✓ {selected_count} Fahrzeuge ausgewählt")
                    else:
                        self.logger.warning(f"{Fore.YELLOW}⚠ Keine Fahrzeuge ausgewählt")
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
        """Wählt Fahrzeuge über Checkboxen aus basierend auf Anforderungen"""
        try:
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
                # Hole alle Checkboxen
                checkboxes = self.driver.find_elements(By.CLASS_NAME, "vehicle_checkbox")

                # Finde passende Checkboxen für diesen Fahrzeugtyp
                matching_checkboxes = []
                attr_names = vehicle_type_mapping.get(vehicle_type, [vehicle_type.lower()])

                for checkbox in checkboxes:
                    # Prüfe ob Checkbox bereits ausgewählt ist
                    if checkbox.is_selected():
                        continue

                    # Prüfe alle möglichen Attributnamen
                    for attr_name in attr_names:
                        try:
                            attr_value = checkbox.get_attribute(attr_name)
                            if attr_value == "1":
                                matching_checkboxes.append(checkbox)
                                break
                        except:
                            pass

                # Wähle die benötigte Anzahl aus
                selected_for_this_type = 0
                for i in range(min(count_needed, len(matching_checkboxes))):
                    try:
                        # Scrolle zur Checkbox damit sie sichtbar ist
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", matching_checkboxes[i])
                        time.sleep(0.2)

                        # Klicke die Checkbox
                        self.driver.execute_script("arguments[0].click();", matching_checkboxes[i])
                        selected_count += 1
                        selected_for_this_type += 1
                        self.logger.info(f"{Fore.GREEN}✓ {vehicle_type} #{i+1} ausgewählt")
                        time.sleep(0.3)
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

            return selected_count

        except Exception as e:
            self.logger.error(f"{Fore.RED}Fehler beim Auswählen von Fahrzeugen: {e}")
            return 0

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
            is_urgent = 'red' in icon.lower() or 'yellow' in icon.lower()

            # Nur Einsätze mit fehlenden Fahrzeugen
            has_missing = missing_text and missing_text.strip()

            if is_urgent and has_missing:
                filtered_missions.append(mission)
                color = "🔴" if 'red' in icon.lower() else "🟡"
                self.logger.info(f"{Fore.GREEN}>>> NEUE VERSION LÄUFT! Fehlend: {missing_text} <<<")
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
            self.logger.info(f"{Fore.RED}>>> VERSION 2.0 AKTIV <<<")
            self.logger.info(f"{Fore.CYAN}  RAW: {repr(missing_text_raw)[:100]}")
            self.logger.info(f"{Fore.GREEN}  GEPARST: {missing_text}")
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


if __name__ == '__main__':
    bot = LeitstellenspielBot()
    bot.run()

