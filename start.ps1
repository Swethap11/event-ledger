# Check uv is available
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv not found — installing..."
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    $env:PATH += ";$env:USERPROFILE\.local\bin"
}

Write-Host "Installing dependencies..."
uv sync

Write-Host "Starting Event Ledger API..."
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
