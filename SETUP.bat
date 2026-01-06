@echo off
chcp 65001 >nul
title Leitstellenspiel Bot - Ersteinrichtung
color 0B

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║     Leitstellenspiel.de Bot - Ersteinrichtung             ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Prüfe ob Python installiert ist
echo [1/4] Prüfe Python-Installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ FEHLER: Python ist nicht installiert!
    echo.
    echo Bitte installieren Sie Python von: https://www.python.org/downloads/
    echo Wichtig: Aktivieren Sie "Add Python to PATH" während der Installation!
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✓ Python %PYTHON_VERSION% gefunden
echo.

REM Erstelle virtuelle Umgebung
echo [2/4] Erstelle virtuelle Umgebung...
if exist "venv" (
    echo ⚠ Virtuelle Umgebung existiert bereits, wird übersprungen
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Fehler beim Erstellen der virtuellen Umgebung
        pause
        exit /b 1
    )
    echo ✓ Virtuelle Umgebung erstellt
)
echo.

REM Aktiviere virtuelle Umgebung und installiere Abhängigkeiten
echo [3/4] Installiere Abhängigkeiten...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ❌ Fehler beim Installieren der Abhängigkeiten
    pause
    exit /b 1
)
echo ✓ Abhängigkeiten installiert
echo.

REM Erstelle config.json falls nicht vorhanden
echo [4/4] Erstelle Konfigurationsdatei...
if exist "config.json" (
    echo ⚠ config.json existiert bereits, wird nicht überschrieben
) else (
    copy config.json.example config.json >nul
    echo ✓ config.json erstellt
    echo.
    echo ⚠ WICHTIG: Bitte bearbeiten Sie jetzt die config.json und tragen Sie
    echo    Ihre Leitstellenspiel.de Zugangsdaten ein!
    echo.
    echo Möchten Sie die config.json jetzt bearbeiten? (J/N)
    set /p EDIT_CONFIG=
    if /i "%EDIT_CONFIG%"=="J" (
        notepad config.json
    )
)
echo.

echo ╔════════════════════════════════════════════════════════════╗
echo ║                  ✓ Setup abgeschlossen!                    ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo Sie können den Bot jetzt mit START_BOT.bat starten!
echo.
pause

