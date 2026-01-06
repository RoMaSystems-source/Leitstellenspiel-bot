@echo off
chcp 65001 >nul
title Bot Logs anzeigen
color 0F

if not exist "bot.log" (
    echo.
    echo ⚠ Keine Log-Datei gefunden!
    echo.
    echo Der Bot wurde noch nicht gestartet oder hat noch keine Logs erstellt.
    echo.
    pause
    exit /b 1
)

echo.
echo Öffne bot.log...
echo.
notepad bot.log

pause

