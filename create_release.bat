@echo off
echo ========================================
echo   GitHub Release v3.0.0 erstellen
echo ========================================
echo.

REM Pruefe ob GitHub CLI installiert ist
where gh >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [FEHLER] GitHub CLI ist nicht installiert!
    echo.
    echo Bitte installiere GitHub CLI:
    echo https://cli.github.com/
    echo.
    echo Oder erstelle den Release manuell auf GitHub.
    pause
    exit /b 1
)

echo [INFO] GitHub CLI gefunden!
echo.

REM Pruefe ob eingeloggt
gh auth status >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Nicht bei GitHub eingeloggt. Starte Login...
    gh auth login
    if %ERRORLEVEL% NEQ 0 (
        echo [FEHLER] Login fehlgeschlagen!
        pause
        exit /b 1
    )
)

echo [INFO] Bei GitHub eingeloggt!
echo.

REM Erstelle Release
echo [INFO] Erstelle Release v3.0.0...
echo.

gh release create v3.0.0 ^
    --title "🎉 Leitstellenspiel Bot v3.0.0 - MAJOR UPDATE" ^
    --notes-file "RELEASE_NOTES_v3.0.0.md" ^
    --repo RoMaSystems-source/Leitstellenspiel-bot ^
    "Leitstellenspiel-Bot-GUI-v3.0.0.zip#Standalone EXE (Empfohlen)" ^
    "Leitstellenspiel-Bot-v3.0.0-Release.zip#Komplettes Release-Paket"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo   RELEASE ERFOLGREICH ERSTELLT!
    echo ========================================
    echo.
    echo Release verfuegbar unter:
    echo https://github.com/RoMaSystems-source/Leitstellenspiel-bot/releases/tag/v3.0.0
    echo.
) else (
    echo.
    echo [FEHLER] Release konnte nicht erstellt werden!
    echo.
    echo Bitte erstelle den Release manuell auf GitHub.
    echo Siehe: GITHUB_RELEASE_ANLEITUNG.md
    echo.
)

pause

