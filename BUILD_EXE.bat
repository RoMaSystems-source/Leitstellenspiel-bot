@echo off
chcp 65001 >nul
echo ========================================
echo  Leitstellenspiel Bot - EXE Builder
echo ========================================
echo.

echo [1/3] Installiere PyInstaller...
python -m pip install pyinstaller --quiet
if errorlevel 1 (
    echo FEHLER: Konnte PyInstaller nicht installieren!
    pause
    exit /b 1
)
echo OK PyInstaller installiert

echo.
echo [2/3] Erstelle Bot-EXE (Konsole)...
python -m PyInstaller --name="Leitstellenspiel-Bot" ^
    --onefile ^
    --console ^
    --add-data="config.json.example;." ^
    --hidden-import=selenium ^
    --hidden-import=requests ^
    --hidden-import=bs4 ^
    --hidden-import=lxml ^
    --hidden-import=colorama ^
    bot.py

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
echo dist\Leitstellenspiel-Bot.exe
echo.
echo Kopiere config.json.example zu config.json
echo und trage deine Zugangsdaten ein!
echo.
pause

