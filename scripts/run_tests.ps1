# Activate the project's .venv (PowerShell) and run pytest
# Usage: Open PowerShell in repo root and run: .\scripts\run_tests.ps1

$venvPath = Join-Path $PSScriptRoot "..\.venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    Write-Host "Activating virtualenv at $venvPath"
    . $venvPath
} else {
    Write-Host "No .venv found. Creating virtualenv..."
    python -m venv .venv
    . .\.venv\Scripts\Activate.ps1
    Write-Host "Installing dev requirements (this may take a while)..."
    pip install -r requirements-dev.txt
}

Write-Host "Running pytest..."
pytest -q
