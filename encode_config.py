# -*- coding: utf-8 -*-
import json
import base64
import os

print("==================================================")
print("  Datenbank-Konfiguration verschleiern")
print("==================================================")
print("\nDieses Skript liest 'db_config.json', verschleiert den Inhalt")
print("und speichert ihn in 'db.dat', damit er in die .exe kompiliert werden kann.\n")

config_file = 'db_config.json'
output_file = 'db.dat'

if not os.path.exists(config_file):
    print(f"FEHLER: Die Datei '{config_file}' wurde nicht gefunden.")
    print("Bitte stelle sicher, dass du die 'db_config.example.json' zu 'db_config.json'")
    print("kopiert und deine echten Datenbank-Zugangsdaten eingetragen hast.")
    input("\nDrücke Enter zum Beenden...")
    exit()

try:
    with open(config_file, 'r', encoding='utf-8') as f:
        config_data = json.load(f)

    if 'DEIN_PASSWORT_HIER' in config_data.get('password', ''):
        print("WARNUNG: Du scheinst das Standard-Passwort 'DEIN_PASSWORT_HIER' zu verwenden.")
        print("Bitte bearbeite zuerst die 'db_config.json' mit deinem echten Passwort.\n")
        input("Drücke Enter zum Beenden...")
        exit()

    json_string = json.dumps(config_data)
    encoded_bytes = base64.b64encode(json_string.encode('utf-8'))
    encoded_string = encoded_bytes.decode('utf-8')

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(encoded_string)
    
    print(f"ERFOLG: Die verschleierte Konfiguration wurde in '{output_file}' gespeichert.")
    print("Du kannst jetzt die 'BUILD_GUI_EXE.bat' ausführen, um die .exe zu erstellen.")

except Exception as e:
    print(f"\nEin Fehler ist aufgetreten: {e}")

input("\nDrücke Enter zum Beenden...")