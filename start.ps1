# start.ps1 — lance ChessEngine en MONO-PROCESS (un seul serveur) et ouvre le navigateur.
# Le backend FastAPI sert l'API ET le frontend buildé. Pour l'usage : double-clique start.bat.
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$python = Join-Path $root "venv\Scripts\python.exe"
$dist = Join-Path $root "web\frontend\dist\index.html"
$url = "http://127.0.0.1:8000"

if (-not (Test-Path $python)) {
    Write-Error "Python du venv introuvable : $python (cree le venv et installe web/backend/requirements.txt)"
    exit 1
}

# Build le frontend au premier lancement (ou si dist a ete nettoye).
# Apres une modif d'UI, relance 'npm --prefix web/frontend run build' pour la refleter.
if (-not (Test-Path $dist)) {
    Write-Host "Build du frontend (premier lancement)..." -ForegroundColor Cyan
    npm --prefix web/frontend run build
}

Write-Host "ChessEngine -> $url   (Ctrl+C pour arreter)" -ForegroundColor Green

# Ouvre le navigateur des que le serveur repond (poll en arriere-plan).
Start-Job -ScriptBlock {
    param($u)
    for ($i = 0; $i -lt 40; $i++) {
        try { Invoke-WebRequest "$u/api/health" -UseBasicParsing -TimeoutSec 2 | Out-Null; break }
        catch { Start-Sleep -Milliseconds 500 }
    }
    Start-Process $u
} -ArgumentList $url | Out-Null

# Un seul uvicorn (API + UI), lance EN MODULE depuis la racine avec le Python du venv.
& $python -m uvicorn web.backend.main:app --host 127.0.0.1 --port 8000
