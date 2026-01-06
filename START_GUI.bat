@echo off
chcp 65001 >nul
echo ========================================
echo  Leitstellenspiel Bot - GUI Starter
echo ========================================
echo.

echo Starte GUI...
py bot_gui_new.py

if errorlevel 1 (
    echo.
    echo FEHLER beim Starten!
    echo.
    echo Mögliche Ursachen:
    echo - Python ist nicht installiert
    echo - customtkinter ist nicht installiert
    echo.
    echo Installiere Abhängigkeiten mit:
    echo py -m pip install -r requirements.txt
    echo.
    pause
)

