import os
import subprocess
import sys
import shutil

def main():
    """Builds the EXE using PyInstaller."""
    print("========================================")
    print(" Leitstellenspiel Bot GUI - EXE Builder (Python)")
    print("========================================")
    print()

    # Create a dummy db.dat file to prevent build errors
    print("[1/4] Erstelle Platzhalter für db.dat...")
    try:
        with open("db.dat", "w", encoding="utf-8") as f:
            f.write("\n")
        print("OK db.dat erstellt.")
    except Exception as e:
        print(f"FEHLER: Konnte db.dat nicht erstellen: {e}")
        sys.exit(1)
    print()

    # Install PyInstaller
    print("[2/4] Installiere PyInstaller...")
    try:
        # Use sys.executable to ensure we're using the same python that is running the script
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pyinstaller"], 
            check=True, capture_output=True, text=True, encoding='utf-8'
        )
        print("OK PyInstaller installiert.")
    except subprocess.CalledProcessError as e:
        print("FEHLER: Konnte PyInstaller nicht installieren!")
        print(e.stdout)
        print(e.stderr)
        sys.exit(1)
    print()

    # Build the EXE
    print("[3/4] Erstelle EXE mit PyInstaller...")
    pyinstaller_command = [
        sys.executable, "-m", "PyInstaller",
        "--name=Leitstellenspiel-Bot-GUI",
        "--onefile",
        "--windowed",
        "--add-data=version.txt;.",
        "--add-data=db.dat;.",
        "--add-data=config.json.example;.",
        "--hidden-import=selenium",
        "--hidden-import=webdriver_manager",
        "--hidden-import=customtkinter",
        "--hidden-import=PIL",
        "--hidden-import=PIL._tkinter_finder",
        "--collect-all=customtkinter",
        "bot_gui_new.py"
    ]
    
    try:
        # We print stdout from PyInstaller to show progress
        process = subprocess.run(
            pyinstaller_command, check=True, capture_output=True, text=True, encoding='utf-8'
        )
        print(process.stdout)
        print("OK EXE erstellt.")
    except subprocess.CalledProcessError as e:
        print("FEHLER: Konnte EXE nicht erstellen!")
        print("--- PyInstaller Output ---")
        print(e.stdout)
        print("--- PyInstaller Error ---")
        print(e.stderr)
        print("--------------------------")
        sys.exit(1)
    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
        sys.exit(1)
    print()

    # Copy files
    print("[4/4] Kopiere Dateien...")
    try:
        if not os.path.exists("dist"):
            os.makedirs("dist")
        shutil.copy("config.json.example", "dist/")
        print("OK Konfigurationsdatei kopiert.")
    except Exception as e:
        print(f"FEHLER: Konnte config.json.example nicht kopieren: {e}")

    print()
    print("========================================")
    print("  FERTIG!")
    print("========================================")
    print()
    print("Die EXE wurde erstellt in: dist\\Leitstellenspiel-Bot-GUI.exe")
    print()

if __name__ == "__main__":
    main()
