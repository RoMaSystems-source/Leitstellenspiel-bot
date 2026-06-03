@echo off
chcp 65001 >nul
echo ========================================
echo  Leitstellenspiel Bot GUI - EXE Builder
echo  Version 3.7.3
echo ========================================
echo.

echo [1/4] Installiere/Aktualisiere PyInstaller...
.\.venv\Scripts\python -m pip install pyinstaller --quiet
if errorlevel 1 (
    echo FEHLER: Konnte PyInstaller nicht installieren!
    pause
    exit /b 1
)
echo OK PyInstaller installiert

echo.
echo [+] Erstelle Platzhalter fuer db.dat falls nicht vorhanden...
if not exist "db.dat" echo. > db.dat

echo.
echo [2/4] Bereinige alte Build-Dateien...
if exist "dist\Leitstellenspiel-Bot-GUI.exe" del /Q "dist\Leitstellenspiel-Bot-GUI.exe"
if exist "build\Leitstellenspiel-Bot-GUI" rmdir /S /Q "build\Leitstellenspiel-Bot-GUI"

echo.
echo [3/4] Erstelle EXE mit PyInstaller...
.\.venv\Scripts\python -m PyInstaller ^
    --name="Leitstellenspiel-Bot-GUI" ^
    --onefile ^
    --windowed ^
    --add-data="version.txt;." ^
    --add-data="db.dat;." ^
    --add-data="config.json.example;." ^
    --collect-all=selenium ^
    --collect-all=customtkinter ^
    --collect-all=darkdetect ^
    --collect-all=webdriver_manager ^
    --hidden-import=pymysql ^
    --hidden-import=colorama ^
    --hidden-import=bs4 ^
    --hidden-import=requests ^
    --hidden-import=lxml ^
    --hidden-import=urllib3 ^
    --hidden-import=certifi ^
    --hidden-import=charset_normalizer ^
    --hidden-import=idna ^
    bot_gui_new.py

if errorlevel 1 (
    echo.
    echo FEHLER: Konnte EXE nicht erstellen!
    echo Tipp: Stelle sicher dass .venv existiert und alle Pakete installiert sind.
    echo       Fuehre zuerst: .\.venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo [4/4] Kopiere Zusatzdateien nach dist\...
if not exist "dist" mkdir dist
copy /Y "config.json.example" "dist\" >nul
copy /Y "version.txt" "dist\" >nul
copy /Y "version.json" "dist\" >nul

echo.
echo ========================================
echo  FERTIG! EXE erfolgreich erstellt.
echo ========================================
echo.
echo Ausgabe: dist\Leitstellenspiel-Bot-GUI.exe
echo.
echo Naechste Schritte:
echo  1. EXE testen: dist\Leitstellenspiel-Bot-GUI.exe
echo  2. Als GitHub Release hochladen (Tag: v3.7.3)
echo  3. version.json im Repo pushen (fuer Update-System)
echo.
pause
