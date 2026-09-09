# run.ps1 - PowerShell launcher for AI Financial Platform
$Host.UI.RawUI.WindowTitle = "AI Financial & Investment Intelligence Platform"
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "  AI FINANCIAL PLATFORM — KHOI DONG HE THONG TRONG 1 LENH" -ForegroundColor Yellow
Write-Host "========================================================================" -ForegroundColor Cyan

$pyExe = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }

& $pyExe run.py $args

