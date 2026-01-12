#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extrahiere version.txt aus einer PyInstaller EXE"""

import sys
import subprocess
import tempfile
import os
import shutil

exe_path = sys.argv[1] if len(sys.argv) > 1 else "test_download_v3.1.0.exe"

print(f"📦 Analysiere: {exe_path}")
print(f"📏 Größe: {os.path.getsize(exe_path):,} Bytes")

# Erstelle temporären Ordner
temp_dir = tempfile.mkdtemp()
print(f"📁 Temp-Ordner: {temp_dir}")

try:
    # Extrahiere mit PyInstaller Archive Viewer
    print(f"\n🔍 Extrahiere Inhalte...")
    
    # Nutze pyi-archive_viewer im non-interactive mode
    result = subprocess.run(
        ['pyi-archive_viewer', exe_path],
        input=b'x version.txt\nq\n',
        capture_output=True,
        timeout=10
    )
    
    print(f"Output: {result.stdout.decode('utf-8', errors='ignore')}")
    print(f"Error: {result.stderr.decode('utf-8', errors='ignore')}")
    
except Exception as e:
    print(f"❌ Fehler: {e}")
finally:
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)

print("\n✅ Fertig!")

