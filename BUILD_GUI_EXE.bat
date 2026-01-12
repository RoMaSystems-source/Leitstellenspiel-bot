@echo off
chcp 65001 >nul
echo ========================================
echo  Leitstellenspiel Bot GUI - EXE Builder
echo ========================================
echo.

echo [1/3] Installiere PyInstaller...
py -m pip install pyinstaller --quiet
if errorlevel 1 (
    echo FEHLER: Konnte PyInstaller nicht installieren!
    pause
    exit /b 1
)
echo OK PyInstaller installiert

echo.
echo [+] Erstelle Platzhalter für db.dat...
echo. > db.dat
echo.
echo [2/3] Erstelle EXE mit PyInstaller...
py -m PyInstaller --name="Leitstellenspiel-Bot-GUI" --onefile --windowed --add-data="version.txt;." --add-data="db.dat;." --add-data="config.json.example;." --hidden-import=selenium --hidden-import=webdriver_manager --hidden-import=customtkinter --hidden-import=PIL --hidden-import=PIL._tkinter_finder --collect-all=customtkinter bot_gui_new.py

if errorlevel 1 (
    echo FEHLER: Konnte EXE nicht erstellen!
    pause
    exit /b 1
)

echo.
echo [3/3] Kopiere Dateien...
if not exist "dist" mkdir dist
copy /Y "config.json.example" "dist\" >nul

echo.
echo ========================================
echo  FERTIG!
echo ========================================
echo.
echo Die EXE wurde erstellt:
echo dist\Leitstellenspiel-Bot-GUI.exe
echo.

echo Starte die EXE und konfiguriere alles im GUI!
echo.
pause