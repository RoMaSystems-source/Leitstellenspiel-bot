"""
Lizenz-Dialog für GUI
"""

import customtkinter as ctk
from license_manager import LicenseManager
from colorama import Fore

class LicenseDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.license_manager = LicenseManager()
        self.license_valid = False
        self.license_key = None
        
        # Fenster-Konfiguration
        self.title("🔐 Lizenz-Aktivierung")
        self.geometry("500x400")
        self.resizable(False, False)
        
        # Zentriere Fenster
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.winfo_screenheight() // 2) - (400 // 2)
        self.geometry(f"500x400+{x}+{y}")
        
        # Modal
        self.transient(parent)
        self.grab_set()
        
        self.create_widgets()
        
        # Prüfe ob bereits Lizenz vorhanden
        self.check_existing_license()
    
    def create_widgets(self):
        """Erstellt GUI-Elemente"""
        # Header
        header = ctk.CTkLabel(
            self,
            text="🔐 Lizenz-Aktivierung",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.pack(pady=20)
        
        # Info-Text
        info = ctk.CTkLabel(
            self,
            text="Bitte geben Sie Ihren Lizenzschlüssel ein,\num den Bot zu aktivieren.",
            font=ctk.CTkFont(size=12)
        )
        info.pack(pady=10)
        
        # Lizenz-Eingabe Frame
        input_frame = ctk.CTkFrame(self)
        input_frame.pack(pady=20, padx=40, fill="x")
        
        # Label
        label = ctk.CTkLabel(
            input_frame,
            text="Lizenzschlüssel:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        label.pack(pady=(10, 5))
        
        # Entry
        self.license_entry = ctk.CTkEntry(
            input_frame,
            width=400,
            height=40,
            font=ctk.CTkFont(size=14),
            placeholder_text="XXXX-XXXX-XXXX-XXXX"
        )
        self.license_entry.pack(pady=(0, 10), padx=10)
        
        # Status-Label
        self.status_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11)
        )
        self.status_label.pack(pady=10)
        
        # Hardware-ID anzeigen
        hw_frame = ctk.CTkFrame(self)
        hw_frame.pack(pady=10, padx=40, fill="x")
        
        hw_label = ctk.CTkLabel(
            hw_frame,
            text=f"Hardware-ID: {self.license_manager.hardware_id}",
            font=ctk.CTkFont(size=9),
            text_color="gray"
        )
        hw_label.pack(pady=5)
        
        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=20)
        
        self.activate_button = ctk.CTkButton(
            button_frame,
            text="Aktivieren",
            width=150,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.activate_license
        )
        self.activate_button.pack(side="left", padx=10)
        
        self.cancel_button = ctk.CTkButton(
            button_frame,
            text="Abbrechen",
            width=150,
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color="gray",
            hover_color="darkgray",
            command=self.cancel
        )
        self.cancel_button.pack(side="left", padx=10)
    
    def check_existing_license(self):
        """Prüft ob bereits eine Lizenz vorhanden ist"""
        valid, message = self.license_manager.check_license()
        
        if valid:
            self.status_label.configure(
                text=f"✓ {message}",
                text_color="green"
            )
            self.license_valid = True
            self.license_key = self.license_manager.license_key
            
            # Zeige Lizenz-Info
            info = self.license_manager.get_license_info()
            if info:
                self.license_entry.insert(0, self.license_key)
                self.license_entry.configure(state="disabled")
                self.activate_button.configure(text="OK", command=self.accept)
    
    def activate_license(self):
        """Aktiviert Lizenz"""
        license_key = self.license_entry.get().strip()
        
        if not license_key:
            self.status_label.configure(
                text="⚠ Bitte Lizenzschlüssel eingeben",
                text_color="orange"
            )
            return
        
        # Validiere Lizenz
        self.status_label.configure(
            text="🔄 Validiere Lizenz...",
            text_color="blue"
        )
        self.update()
        
        valid, message = self.license_manager.check_license(license_key, force_online=True)
        
        if valid:
            self.status_label.configure(
                text=f"✓ {message}",
                text_color="green"
            )
            self.license_valid = True
            self.license_key = license_key
            
            # Warte kurz und schließe
            self.after(1000, self.accept)
        else:
            self.status_label.configure(
                text=f"✗ {message}",
                text_color="red"
            )
    
    def accept(self):
        """Akzeptiert und schließt Dialog"""
        self.destroy()
    
    def cancel(self):
        """Bricht ab"""
        self.license_valid = False
        self.destroy()

