# Office Toolkit - Run Tests
$ErrorActionPreference = "Stop"

$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "Virtual environment not found. Run dev_setup.ps1 first." -ForegroundColor Red
    exit 1
}

Write-Host "Running tests..." -ForegroundColor Cyan
& $python -m pytest -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "All tests passed!" -ForegroundColor Green
