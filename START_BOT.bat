@echo off
chcp 65001 >nul
title Leitstellenspiel Bot
color 0A

REM Prüfe ob Setup durchgeführt wurde
if not exist "venv" (
    echo.
    echo ❌ FEHLER: Setup wurde noch nicht durchgeführt!
    echo.
    echo Bitte führen Sie zuerst SETUP.bat aus.
    echo.
    pause
    exit /b 1
)

if not exist "config.json" (
    echo.
    echo ❌ FEHLER: config.json nicht gefunden!
    echo.
    echo Bitte führen Sie zuerst SETUP.bat aus.
    echo.
    pause
    exit /b 1
)

REM Aktiviere virtuelle Umgebung
call venv\Scripts\activate.bat

REM Starte Bot
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║          Leitstellenspiel.de Bot wird gestartet...        ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo Zum Beenden drücken Sie Strg+C
echo.

python bot.py

REM Falls Bot beendet wurde
echo.
echo Bot wurde beendet.
pause

