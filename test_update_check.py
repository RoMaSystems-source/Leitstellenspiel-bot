#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Auto-Update Check"""

import requests
import sys
import os

print("=" * 60)
print("🔍 AUTO-UPDATE DEBUG TEST")
print("=" * 60)

# 1. Aktuelle Version ermitteln
print("\n📌 SCHRITT 1: Aktuelle Version ermitteln")
print("-" * 60)

current_version = "3.2.0"  # Fallback

try:
    if getattr(sys, 'frozen', False):
        # Wir laufen als EXE
        base_path = sys._MEIPASS
        print(f"✅ Läuft als EXE")
        print(f"📁 Base Path: {base_path}")
    else:
        # Wir laufen als Python-Script
        base_path = os.path.dirname(__file__)
        print(f"✅ Läuft als Python-Script")
        print(f"📁 Base Path: {base_path}")
    
    version_file = os.path.join(base_path, 'version.txt')
    print(f"📄 Version File: {version_file}")
    print(f"📄 Existiert: {os.path.exists(version_file)}")
    
    if os.path.exists(version_file):
        with open(version_file, 'r') as f:
            current_version = f.read().strip()
        print(f"✅ VERSION: {current_version}")
    else:
        print(f"⚠ version.txt nicht gefunden - nutze Fallback: {current_version}")
except Exception as e:
    print(f"❌ FEHLER: {e}")
    import traceback
    traceback.print_exc()

# 2. GitHub API abfragen
print("\n📌 SCHRITT 2: GitHub API abfragen")
print("-" * 60)

update_url = "https://api.github.com/repos/RoMaSystems-source/Leitstellenspiel-bot/releases/latest"
print(f"🌐 URL: {update_url}")

try:
    response = requests.get(update_url, timeout=10)
    print(f"📊 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        latest_version = data.get('tag_name', '').replace('v', '')
        
        print(f"✅ Latest Version: {latest_version}")
        print(f"📅 Published: {data.get('published_at')}")
        print(f"🔗 URL: {data.get('html_url')}")
        
        # Assets
        print(f"\n📦 Assets:")
        assets = data.get('assets', [])
        for asset in assets:
            print(f"  - {asset.get('name')} ({asset.get('size')} bytes)")
            print(f"    Download: {asset.get('browser_download_url')}")
        
        # Vergleich
        print(f"\n🔍 VERGLEICH:")
        print(f"  Aktuelle Version: {current_version}")
        print(f"  Neueste Version:  {latest_version}")
        print(f"  Gleich? {current_version == latest_version}")
        
        if latest_version != current_version:
            print(f"\n✅ UPDATE VERFÜGBAR: {current_version} → {latest_version}")
        else:
            print(f"\n✅ BOT IST AKTUELL")
    else:
        print(f"❌ GitHub API Fehler: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
except Exception as e:
    print(f"❌ FEHLER: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("✅ TEST ABGESCHLOSSEN")
print("=" * 60)

