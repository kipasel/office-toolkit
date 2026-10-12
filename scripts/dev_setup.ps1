# Office Toolkit - Development Setup
# Requires Python 3.12 via py launcher

$ErrorActionPreference = "Stop"

Write-Host "Setting up Office Toolkit development environment..." -ForegroundColor Cyan

# Create virtual environment
Write-Host "Creating virtual environment (.venv)..." -ForegroundColor Yellow
py -3.12 -m venv .venv
if (-not $?) { throw "Failed to create venv" }

# Activate and upgrade pip
$python = ".\.venv\Scripts\python.exe"
Write-Host "Upgrading pip..." -ForegroundColor Yellow
& $python -m pip install --upgrade pip

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
& $python -m pip install -r requirements.txt -r requirements-dev.txt

Write-Host "Development environment ready!" -ForegroundColor Green
Write-Host "Run: .\.venv\Scripts\python -m office_toolkit" -ForegroundColor Cyan
Write-Host "Test: .\.venv\Scripts\python -m pytest" -ForegroundColor Cyan
Write-Host "Build: .\scripts\build_windows.ps1" -ForegroundColor Cyan
