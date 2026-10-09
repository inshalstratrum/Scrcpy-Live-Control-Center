# Scrcpy Live Control Center - Automatic Setup & Environment Installer
# Downloads official Genymobile Scrcpy + ADB binaries and installs Python dependencies

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   Scrcpy Live Control Center - Setup & Binary Installer  " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Check Python and dependencies
Write-Host "`n[*] Step 1: Checking Python environment..." -ForegroundColor Yellow
try {
    $pyVersion = python --version 2>&1
    Write-Host "    Found Python: $pyVersion" -ForegroundColor Green
    
    $reqFile = Join-Path $ScriptDir "requirements.txt"
    if (Test-Path $reqFile) {
        Write-Host "    Installing Python requirements (PyQt6)..." -ForegroundColor Yellow
        python -m pip install -r $reqFile
        Write-Host "    Dependencies installed successfully." -ForegroundColor Green
    }
} catch {
    Write-Host "    [!] Warning: Python not found on PATH. Please install Python 3.10+ and add it to PATH." -ForegroundColor Red
}

# 2. Check for existing Scrcpy and ADB binaries
Write-Host "`n[*] Step 2: Checking for Scrcpy & ADB binaries..." -ForegroundColor Yellow
$localScrcpy = Join-Path $ScriptDir "scrcpy.exe"
$localAdb = Join-Path $ScriptDir "adb.exe"

$hasScrcpy = (Test-Path $localScrcpy) -or (Get-Command "scrcpy" -ErrorAction SilentlyContinue)
$hasAdb = (Test-Path $localAdb) -or (Get-Command "adb" -ErrorAction SilentlyContinue)

if ($hasScrcpy -and $hasAdb) {
    Write-Host "    [OK] Scrcpy and ADB binaries are already available!" -ForegroundColor Green
    if (Test-Path $localScrcpy) {
        & $localScrcpy --version | Select-Object -First 1 | ForEach-Object { Write-Host "    $($_)" -ForegroundColor Gray }
    }
} else {
    Write-Host "    Binaries missing. Downloading official Scrcpy release package from GitHub..." -ForegroundColor Yellow
    $zipUrl = "https://github.com/Genymobile/scrcpy/releases/download/v3.1/scrcpy-win64-v3.1.zip"
    $zipPath = Join-Path $ScriptDir "scrcpy-download.zip"
    $extractPath = Join-Path $ScriptDir "scrcpy_temp"

    try {
        Write-Host "    Downloading from: $zipUrl" -ForegroundColor Cyan
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13
        Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing

        Write-Host "    Extracting archive..." -ForegroundColor Yellow
        if (Test-Path $extractPath) { Remove-Item -Recurse -Force $extractPath }
        Expand-Archive -Path $zipPath -DestinationPath $extractPath -Force

        $innerFolder = Get-ChildItem -Directory -Path $extractPath | Select-Object -First 1
        if ($innerFolder) {
            Get-ChildItem -Path $innerFolder.FullName | ForEach-Object {
                Copy-Item -Path $_.FullName -Destination $ScriptDir -Force -Recurse
            }
        }

        # Cleanup temporary files
        Remove-Item -Force $zipPath -ErrorAction SilentlyContinue
        Remove-Item -Recurse -Force $extractPath -ErrorAction SilentlyContinue

        Write-Host "    [OK] Scrcpy & ADB successfully installed into $ScriptDir!" -ForegroundColor Green
    } catch {
        Write-Host "    [ERROR] Automatic download failed: $_" -ForegroundColor Red
        Write-Host "    You can manually download 'scrcpy-win64-v3.1.zip' from https://github.com/Genymobile/scrcpy/releases" -ForegroundColor Gray
        Write-Host "    and extract the files into this directory." -ForegroundColor Gray
    }
}

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "   Setup complete! Launch using Start_Control_Center.bat " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
