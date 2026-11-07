# Curio - Local Quality Verification Pipeline
$ErrorActionPreference = "Stop"
Write-Host "`n=== Curio Local Verification Pipeline ===" -ForegroundColor Cyan

$backendDir = Join-Path $PSScriptRoot "..\backend"
Set-Location $backendDir

Write-Host "`n[1/4] Formatting Code (Ruff)..." -ForegroundColor Yellow
uv run ruff format app tests
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "`n[2/4] Linting & Auto-fixing (Ruff)..." -ForegroundColor Yellow
uv run ruff check --fix app tests
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "`n[3/4] Mypy Static Type Checking..." -ForegroundColor Yellow
uv run mypy app
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "`n[4/4] Pytest Test Suite..." -ForegroundColor Yellow
uv run pytest --cov=app --cov-report=term-missing tests
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "`n=== All Quality Checks Passed! Ready to commit and push. ===`n" -ForegroundColor Green
