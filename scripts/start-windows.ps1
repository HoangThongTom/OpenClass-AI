# Run from repo root: .\scripts\start-windows.ps1
# Starts PostgreSQL, then explains which local dev processes to launch.
Set-Location (Split-Path -Parent $PSScriptRoot)
docker compose up -d db
Write-Host "PostgreSQL: localhost:5434" -ForegroundColor Green
Write-Host "Next, open TWO new PowerShell windows:" -ForegroundColor Cyan
Write-Host 'Terminal 1: cd backend; .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000'
Write-Host 'Terminal 2: cd frontend; npm run dev'
Write-Host 'Website: http://localhost:3002 | API docs: http://localhost:8000/docs'
