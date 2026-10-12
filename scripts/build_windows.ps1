# Office Toolkit - Build Windows Executable (onedir)
$ErrorActionPreference = "Stop"

$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "Virtual environment not found. Run dev_setup.ps1 first." -ForegroundColor Red
    exit 1
}

Write-Host "Building Office Toolkit (onedir)..." -ForegroundColor Cyan
& $python -m PyInstaller app.spec --noconfirm --clean

if ($LASTEXITCODE -eq 0) {
    Write-Host "Build completed successfully!" -ForegroundColor Green
    Write-Host "Executable: dist\OfficeToolkit\OfficeToolkit.exe" -ForegroundColor Cyan
} else {
    Write-Host "Build failed!" -ForegroundColor Red
    exit $LASTEXITCODE
}
