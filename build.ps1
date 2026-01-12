# build.ps1
# PowerShell Build Script
# To run this script, execute: powershell.exe -ExecutionPolicy Bypass -File .\build.ps1

Write-Host "========================================" -ForegroundColor Green
Write-Host " Leitstellenspiel Bot GUI - EXE Builder (PowerShell)" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# --- Pre-Step: Terminate existing processes ---
Write-Host "[0/4] Beende alte Bot-Instanzen..."
try {
    # Terminate any running instances of the bot GUI
    Get-Process "Leitstellenspiel-Bot-GUI" -ErrorAction SilentlyContinue | Stop-Process -Force
    Write-Host "OK: Alte Bot-Instanzen beendet (falls vorhanden)." -ForegroundColor Green
} catch {
    Write-Error "FEHLER: Konnte alte Bot-Instanzen nicht beenden: $_"
    pause
    exit 1
}
Write-Host ""

# --- Step 1: Create placeholder for db.dat ---
Write-Host "[1/4] Erstelle Platzhalter für db.dat..."
$dbDatPath = (Join-Path $PSScriptRoot "db.dat") # Use $PSScriptRoot for current script directory
if (-not (Test-Path $dbDatPath)) {
    try {
        Set-Content -Path $dbDatPath -Value "" -Encoding UTF8 -ErrorAction Stop
        Write-Host "OK: db.dat erstellt." -ForegroundColor Green
    } catch {
        Write-Error "FEHLER: Konnte db.dat nicht erstellen: $_"
        pause
        exit 1
    }
} else {
    Write-Host "OK: db.dat existiert bereits." -ForegroundColor Green
}
# Verify existence immediately after creation/check
if (-not (Test-Path $dbDatPath)) {
    Write-Error "FEHLER: db.dat konnte nicht gefunden werden nach Erstellung/Prüfung!"
    pause
    exit 1
}
Write-Host ""

# --- Step 2: Install PyInstaller ---
Write-Host "[2/4] Installiere PyInstaller..."
try {
    # Using 'py.exe' which should be in the user's PATH
    py -m pip install pyinstaller --quiet
    if ($LASTEXITCODE -ne 0) {
        throw "Pip failed to install PyInstaller."
    }
    Write-Host "OK: PyInstaller installiert." -ForegroundColor Green
} catch {
    Write-Error "FEHLER: Konnte PyInstaller nicht installieren! Stellen Sie sicher, dass Python und Pip korrekt installiert sind."
    Write-Error $_ 
    pause
    exit 1
}
Write-Host ""

# --- Step 3: Build the EXE with PyInstaller ---
Write-Host "[3/4] Erstelle EXE mit PyInstaller..."
$pyInstallerArgs = @(
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
)

try {
    # Execute PyInstaller
    py -m PyInstaller $pyInstallerArgs
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller execution failed."
    }
    Write-Host "OK: EXE erstellt." -ForegroundColor Green
} catch {
    Write-Error "FEHLER: Konnte EXE nicht erstellen! Überprüfen Sie die PyInstaller-Ausgabe oben auf Fehler."
    Write-Error $_
    pause
    exit 1
}
Write-Host ""


# --- Step 4: Copy supporting files ---
Write-Host "[4/4] Kopiere Dateien..."
$destinationDir = ".\dist"
if (-not (Test-Path -Path $destinationDir -PathType Container)) {
    New-Item -Path $destinationDir -ItemType Directory -Force | Out-Null
}
try {
    Copy-Item -Path "config.json.example" -Destination $destinationDir -Force -ErrorAction Stop
    Write-Host "OK: Konfigurationsdatei kopiert." -ForegroundColor Green
} catch {
    Write-Error "FEHLER: Konnte config.json.example nicht nach 'dist' kopieren: $_"
    pause
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  FERTIG!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Die EXE wurde erstellt in: $destinationDir\Leitstellenspiel-Bot-GUI.exe"
Write-Host ""
pause
