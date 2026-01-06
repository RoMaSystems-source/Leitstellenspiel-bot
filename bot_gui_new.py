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
import random
from vehicle_types import VEHICLE_TYPES, CATEGORY_TO_TYPES
from bot_standalone import LeitstellenspielBot

# Colorama initialisieren
init(autoreset=True)

# CustomTkinter Einstellungen
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

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
                'auto_follow_up': True,
                'alliance_missions': False,
                'auto_expand': False,
                'auto_update': True
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
                "features": {
                    "alliance_mission": settings.get('alliance_missions', False),
                    "auto_expand": settings.get('auto_expand', False),
                    "auto_update": settings.get('auto_update', True)
                },
                "logging": {
                    "level": "INFO",
                    "file": "bot.log"
                },
                "cache": {
                    "mission_cache_file": "mission_cache.json",
                    "cache_expiry_hours": 24
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

            # Lade API-Daten
            self.add_log("Lade Fahrzeuge und Gebaeude...")
            try:
                self.bot.load_api_data()
                self.add_log(f"Geladen: {len(self.bot.api_vehicles)} Fahrzeuge, {len(self.bot.api_buildings)} Gebaeude")
            except Exception as e:
                self.add_log(f"FEHLER beim Laden der API-Daten: {str(e)}")
                # Weiter machen, auch wenn API-Daten nicht geladen werden konnten

            # Hauptschleife
            cycle = 0
            while self.running:
                cycle += 1
                self.add_log(f"\n=== Zyklus #{cycle} ===")

                try:
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
    try:
        # Prüfe ob customtkinter installiert ist
        import customtkinter
    except ImportError:
        print("FEHLER: customtkinter ist nicht installiert!")
        print("Bitte installieren Sie es mit: pip install customtkinter")
        input("Druecken Sie Enter zum Beenden...")
        return

    # Starte GUI
    app = BotGUI()
    app.run()


if __name__ == "__main__":
    main()