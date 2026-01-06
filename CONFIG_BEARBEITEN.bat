@echo off
chcp 65001 >nul
title Konfiguration bearbeiten
color 0E

if not exist "config.json" (
    echo.
    echo ❌ FEHLER: config.json nicht gefunden!
    echo.
    echo Bitte führen Sie zuerst SETUP.bat aus.
    echo.
    pause
    exit /b 1
)

echo.
echo Öffne config.json zum Bearbeiten...
echo.
notepad config.json

echo.
echo Konfiguration gespeichert!
echo.
pause

