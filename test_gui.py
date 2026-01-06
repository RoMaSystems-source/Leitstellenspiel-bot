#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test-Skript für das GUI
Zeigt das GUI für 5 Sekunden an
"""

import customtkinter as ctk
import time
import threading

def test_gui():
    """Testet das GUI"""
    
    # Erstelle Fenster
    root = ctk.CTk()
    root.title("Leitstellenspiel Bot - Professional Edition")
    root.geometry("1400x900")
    
    # Header
    header_frame = ctk.CTkFrame(root, height=80, corner_radius=0, fg_color="#1a1a1a")
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
    
    # Main Container
    main_container = ctk.CTkFrame(root, fg_color="transparent")
    main_container.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Linke Seite
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
    
    start_button = ctk.CTkButton(
        control_frame,
        text="BOT STARTEN",
        height=50,
        font=ctk.CTkFont(size=16, weight="bold"),
        fg_color="#2ecc71",
        hover_color="#27ae60"
    )
    start_button.pack(fill="x", padx=20, pady=10)
    
    status_label = ctk.CTkLabel(
        control_frame,
        text="Status: Gestoppt",
        font=ctk.CTkFont(size=14),
        text_color="#95a5a6"
    )
    status_label.pack(pady=10)
    
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
    stats_data = [
        ("Einsaetze bearbeitet", "42", "#e74c3c"),
        ("Fahrzeuge alarmiert", "156", "#3498db"),
        ("Laufzeit", "02:34:56", "#9b59b6"),
        ("Credits verdient", "21,000", "#f39c12")
    ]
    
    for label, value, color in stats_data:
        card = ctk.CTkFrame(stats_frame, fg_color=color, corner_radius=10)
        
        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="white"
        )
        value_label.pack(pady=(15, 5))
        
        label_label = ctk.CTkLabel(
            card,
            text=label,
            font=ctk.CTkFont(size=12),
            text_color="white"
        )
        label_label.pack(pady=(0, 15))
        
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
    
    log_text = ctk.CTkTextbox(
        right_panel,
        font=ctk.CTkFont(family="Consolas", size=11),
        wrap="word"
    )
    log_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))
    
    # Füge Demo-Logs hinzu
    demo_logs = [
        "[12:34:56] Bot gestartet!",
        "[12:34:57] Initialisiere Bot...",
        "[12:34:58] Starte Browser...",
        "[12:35:00] Versuche Login...",
        "[12:35:02] Login erfolgreich!",
        "[12:35:03] Lade Fahrzeuge und Gebaeude...",
        "[12:35:05] Geladen: 156 Fahrzeuge, 42 Gebaeude",
        "",
        "=== Zyklus #1 ===",
        "[12:35:06] Gefunden: 5 Einsaetze",
        "[12:35:07] [1/5] Brand in Wohnhaus (ID: 12345)",
        "[12:35:07]   Fehlend: 2x LF, 1x DLK",
        "[12:35:08]   Alarmiere Fahrzeuge...",
        "[12:35:10]   OK Einsatz bearbeitet",
    ]
    
    for log in demo_logs:
        log_text.insert("end", log + "\n")
    
    # Schließe nach 10 Sekunden
    def close_after_delay():
        time.sleep(10)
        root.quit()
    
    threading.Thread(target=close_after_delay, daemon=True).start()
    
    print("GUI wird für 10 Sekunden angezeigt...")
    root.mainloop()
    print("GUI geschlossen")

if __name__ == "__main__":
    test_gui()

