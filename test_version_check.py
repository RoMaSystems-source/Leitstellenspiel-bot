#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test: Prüfe welche Version die EXE hat"""

import sys
import os

# PyInstaller-kompatibel: Prüfe ob wir in einer EXE laufen
if getattr(sys, 'frozen', False):
    # Wir laufen als EXE - nutze sys._MEIPASS
    base_path = sys._MEIPASS
    print(f"✅ Läuft als EXE")
    print(f"📁 Base Path: {base_path}")
else:
    # Wir laufen als Python-Script
    base_path = os.path.dirname(__file__)
    print(f"⚠️ Läuft als Python-Script")
    print(f"📁 Base Path: {base_path}")

# Versuche version.txt zu lesen
version_file = os.path.join(base_path, 'version.txt')
print(f"📄 Version File: {version_file}")
print(f"📄 Existiert: {os.path.exists(version_file)}")

if os.path.exists(version_file):
    with open(version_file, 'r') as f:
        version = f.read().strip()
    print(f"✅ VERSION: {version}")
else:
    print(f"❌ version.txt NICHT GEFUNDEN!")
    print(f"📂 Dateien in {base_path}:")
    try:
        for file in os.listdir(base_path):
            print(f"   - {file}")
    except:
        print("   Kann Ordner nicht lesen")

# # # # input("\nDrücke ENTER zum Beenden...")

