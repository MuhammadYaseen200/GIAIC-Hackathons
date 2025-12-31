#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Automated Vercel deployment script for Evolution-of-Todo Phase 2
.DESCRIPTION
    This script automates the full deployment workflow:
    - Generates secure JWT secrets
    - Sets environment variables via Vercel CLI
    - Deploys both backend and frontend to production
.PARAMETER DatabaseUrl
    Neon PostgreSQL connection string (required)
.PARAMETER FrontendUrl
    Custom frontend URL (optional, auto-detected from Vercel)
.PARAMETER BackendUrl
    Custom backend URL (optional, auto-detected from Vercel)
.PARAMETER SkipDeploy
    Only set environment variables without deploying
.EXAMPLE
    .\deploy-to-vercel.ps1 -DatabaseUrl "postgresql+asyncpg://user:pass@host/db"
#>

param(
    [Parameter(Mandatory=$true, HelpMessage="Neon PostgreSQL connection string")]
    [string]$DatabaseUrl,

    [Parameter(Mandatory=$false)]
    [string]$FrontendUrl,

    [Parameter(Mandatory=$false)]
    [string]$BackendUrl,

    [Parameter(Mandatory=$false)]
    [switch]$SkipDeploy
)

# Color output functions
function Write-Header { param([string]$Message) Write-Host "`n=== $Message ===" -ForegroundColor Cyan }
function Write-Success { param([string]$Message) Write-Host "[OK] $Message" -ForegroundColor Green }
function Write-Error-Custom { param([string]$Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }
function Write-Warning-Custom { param([string]$Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Info { param([string]$Message) Write-Host "[INFO] $Message" -ForegroundColor Blue }

# Get script directory
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$BACKEND_DIR = Join-Path $SCRIPT_DIR "backend"
$FRONTEND_DIR = Join-Path $SCRIPT_DIR "frontend"

Write-Header "Evolution-of-Todo Vercel Deployment Automation"
Write-Info "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

# Prerequisite checks
Write-Header "Checking Prerequisites"

# Check Vercel CLI
if (-not (Get-Command vercel -ErrorAction SilentlyContinue)) {
    Write-Error-Custom "Vercel CLI not found. Install with: npm install -g vercel"
    exit 1
}
Write-Success "Vercel CLI found: $(vercel --version)"

# Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error-Custom "Python not found. Install Python 3.13+ from python.org"
    exit 1
}
Write-Success "Python found: $(python --version)"

# Verify directory structure
if (-not (Test-Path $BACKEND_DIR)) {
    Write-Error-Custom "Backend directory not found: $BACKEND_DIR"
    exit 1
}
if (-not (Test-Path $FRONTEND_DIR)) {
    Write-Error-Custom "Frontend directory not found: $FRONTEND_DIR"
    exit 1
}
Write-Success "Project structure verified"

# Verify Vercel authentication
Write-Header "Verifying Vercel Authentication"
$whoami = vercel whoami 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error-Custom "Not logged into Vercel. Run: vercel login"
    exit 1
}
Write-Success "Logged in as: $whoami"

# Generate secure JWT secret
Write-Header "Generating Secure JWT Secret"
$SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(32))" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error-Custom "Failed to generate secret key"
    exit 1
}
Write-Success "Generated 256-bit JWT secret"

# Get Vercel project URLs if not provided
Write-Header "Resolving Deployment URLs"

if (-not $BackendUrl) {
    Push-Location $BACKEND_DIR
    $backendInspect = vercel inspect --token $env:VERCEL_TOKEN 2>&1 | Out-String
    if ($backendInspect -match 'https://[^\s]+\.vercel\.app') {
        $BackendUrl = $Matches[0]
        Write-Success "Auto-detected backend URL: $BackendUrl"
    } else {
        Write-Warning-Custom "Could not auto-detect backend URL. You may need to deploy first or provide -BackendUrl"
        $BackendUrl = Read-Host "Enter backend production URL (e.g., https://backend-xyz.vercel.app)"
    }
    Pop-Location
}

if (-not $FrontendUrl) {
    Push-Location $FRONTEND_DIR
    $frontendInspect = vercel inspect --token $env:VERCEL_TOKEN 2>&1 | Out-String
    if ($frontendInspect -match 'https://[^\s]+\.vercel\.app') {
        $FrontendUrl = $Matches[0]
        Write-Success "Auto-detected frontend URL: $FrontendUrl"
    } else {
        Write-Warning-Custom "Could not auto-detect frontend URL. You may need to deploy first or provide -FrontendUrl"
        $FrontendUrl = Read-Host "Enter frontend production URL (e.g., https://frontend-xyz.vercel.app)"
    }
    Pop-Location
}

# Prepare CORS origins (JSON array)
$CORS_ORIGINS = "[`"$FrontendUrl`"]"

# Display configuration summary
Write-Header "Deployment Configuration"
Write-Host "Backend URL:      $BackendUrl" -ForegroundColor White
Write-Host "Frontend URL:     $FrontendUrl" -ForegroundColor White
Write-Host "Database:         $(($DatabaseUrl -split '@')[1] -split '/')[0]" -ForegroundColor White
Write-Host "JWT Secret:       ***$(($SECRET_KEY[-8..-1]) -join '')" -ForegroundColor White
Write-Host "CORS Origins:     $CORS_ORIGINS" -ForegroundColor White

Write-Host "`nPress any key to continue or Ctrl+C to abort..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Set backend environment variables
Write-Header "Configuring Backend Environment"
Push-Location $BACKEND_DIR

$backendEnvVars = @{
    "DATABASE_URL" = $DatabaseUrl
    "SECRET_KEY" = $SECRET_KEY
    "CORS_ORIGINS" = $CORS_ORIGINS
    "ALGORITHM" = "HS256"
    "ACCESS_TOKEN_EXPIRE_MINUTES" = "1440"
}

foreach ($key in $backendEnvVars.Keys) {
    Write-Info "Setting $key..."
    $value = $backendEnvVars[$key]

    # Remove existing variable first (ignore errors)
    vercel env rm $key production --yes 2>$null

    # Add new variable
    $result = Write-Output $value | vercel env add $key production 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "$key configured"
    } else {
        Write-Warning-Custom "Failed to set $key (may already exist)"
    }
}

Pop-Location

# Set frontend environment variables
Write-Header "Configuring Frontend Environment"
Push-Location $FRONTEND_DIR

$frontendEnvVars = @{
    "NEXT_PUBLIC_API_URL" = $BackendUrl
    "BACKEND_URL" = $BackendUrl
}

foreach ($key in $frontendEnvVars.Keys) {
    Write-Info "Setting $key..."
    $value = $frontendEnvVars[$key]

    # Remove existing variable first (ignore errors)
    vercel env rm $key production --yes 2>$null

    # Add new variable
    $result = Write-Output $value | vercel env add $key production 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "$key configured"
    } else {
        Write-Warning-Custom "Failed to set $key (may already exist)"
    }
}

Pop-Location

if ($SkipDeploy) {
    Write-Header "Deployment Skipped"
    Write-Info "Environment variables configured. Deploy manually with:"
    Write-Info "  cd backend && vercel --prod"
    Write-Info "  cd frontend && vercel --prod"
    exit 0
}

# Deploy backend
Write-Header "Deploying Backend to Production"
Push-Location $BACKEND_DIR
vercel --prod --yes
if ($LASTEXITCODE -eq 0) {
    Write-Success "Backend deployed successfully"
} else {
    Write-Error-Custom "Backend deployment failed"
    Pop-Location
    exit 1
}
Pop-Location

# Deploy frontend
Write-Header "Deploying Frontend to Production"
Push-Location $FRONTEND_DIR
vercel --prod --yes
if ($LASTEXITCODE -eq 0) {
    Write-Success "Frontend deployed successfully"
} else {
    Write-Error-Custom "Frontend deployment failed"
    Pop-Location
    exit 1
}
Pop-Location

# Database migration reminder
Write-Header "Post-Deployment Actions Required"
Write-Warning-Custom "Database migrations must be run manually!"
Write-Info "Run migrations with:"
Write-Info "  cd backend"
Write-Info "  `$env:DATABASE_URL='$DatabaseUrl'"
Write-Info "  uv run alembic upgrade head"

# Verification steps
Write-Header "Deployment Verification"
Write-Info "Test your deployment:"
Write-Info "  1. Backend health: curl $BackendUrl/health"
Write-Info "  2. Frontend: Open $FrontendUrl in browser"
Write-Info "  3. Register test user via frontend UI"
Write-Info "  4. Test task CRUD operations"

# Write deployment record
Write-Header "Saving Deployment Record"
$deploymentRecord = @"
================================================================================
VERCEL DEPLOYMENT RECORD
================================================================================
Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Deployed by: $whoami

URLs:
  Frontend: $FrontendUrl
  Backend:  $BackendUrl

Backend Environment:
  DATABASE_URL: $(($DatabaseUrl -split '@')[1] -split '/')[0]
  SECRET_KEY: ***$(($SECRET_KEY[-8..-1]) -join '')
  CORS_ORIGINS: $CORS_ORIGINS

Frontend Environment:
  NEXT_PUBLIC_API_URL: $BackendUrl
  BACKEND_URL: $BackendUrl

================================================================================
NEXT STEPS:
1. Run database migrations (see command above)
2. Test endpoints (curl commands above)
3. Monitor Vercel deployment logs
================================================================================
"@

$recordFile = Join-Path $SCRIPT_DIR "vercel-deployment-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
$deploymentRecord | Out-File -FilePath $recordFile -Encoding utf8
Write-Success "Deployment record saved: $recordFile"

Write-Header "Deployment Complete"
Write-Success "All services deployed successfully!"
