# dev.ps1 — lance le backend (FastAPI) et le frontend (Vite) en parallele.
# Usage : ./dev.ps1   (depuis la racine du projet)
#
# Encode les deux pieges documentes dans CLAUDE.md :
#   1. on utilise le Python du venv du projet (les autres n'ont pas FastAPI) ;
#   2. on lance le backend EN MODULE depuis la racine (sinon ImportError sur les imports relatifs).

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$python = Join-Path $root "venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Error "Python du venv introuvable : $python. Cree le venv et installe web/backend/requirements.txt."
    exit 1
}

Write-Host "Backend (FastAPI)  -> http://localhost:8000" -ForegroundColor Cyan
$backend = Start-Process -FilePath $python `
    -ArgumentList "-m", "uvicorn", "web.backend.main:app", "--host", "0.0.0.0", "--port", "8000" `
    -WorkingDirectory $root -PassThru -NoNewWindow

Write-Host "Frontend (Vite)    -> http://localhost:5173" -ForegroundColor Cyan
$frontend = Start-Process -FilePath "npm" `
    -ArgumentList "--prefix", "web/frontend", "run", "dev" `
    -WorkingDirectory $root -PassThru -NoNewWindow

Write-Host "Les deux serveurs tournent. Ctrl+C pour tout arreter." -ForegroundColor Green
try {
    Wait-Process -Id $backend.Id, $frontend.Id
} finally {
    Stop-Process -Id $backend.Id, $frontend.Id -ErrorAction SilentlyContinue
}
