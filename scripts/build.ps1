# Curio - Local Build & Format Script
$ErrorActionPreference = "Stop"
Write-Host "`n=== [1/3] Curio Build: Auto-Formatting Code ===" -ForegroundColor Cyan

$backendDir = Join-Path $PSScriptRoot "..\backend"
Set-Location $backendDir

# Step 1: Format code
Write-Host "Running Ruff Code Formatter..." -ForegroundColor Yellow
uv run ruff format app tests
if ($LASTEXITCODE -ne 0) { exit 1 }

# Step 2: Auto-fix linting issues
Write-Host "`n=== [2/3] Curio Build: Checking & Fixing Lint ===" -ForegroundColor Cyan
uv run ruff check --fix app tests
if ($LASTEXITCODE -ne 0) { exit 1 }

# Step 3: Build & start Docker containers
Write-Host "`n=== [3/3] Curio Build: Starting Docker Compose Stack ===" -ForegroundColor Cyan
Set-Location (Join-Path $PSScriptRoot "..")
docker compose build
docker compose up -d

Write-Host "`n=== Build Complete & Stack Running! ===`n" -ForegroundColor Green
