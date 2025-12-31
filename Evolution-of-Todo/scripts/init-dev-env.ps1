# =============================================================================
# Evolution of Todo - Development Environment Initialization Script (Windows)
# =============================================================================
# Purpose: Automated setup of local development environment for Windows
# Author: DevOps RAG Engineer
# =============================================================================

#Requires -Version 5.1

$ErrorActionPreference = "Stop"

# Script directory and project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Log-Info {
    param([string]$Message)
    Write-ColorOutput "[INFO] $Message" -Color Cyan
}

function Log-Success {
    param([string]$Message)
    Write-ColorOutput "[SUCCESS] $Message" -Color Green
}

function Log-Warning {
    param([string]$Message)
    Write-ColorOutput "[WARNING] $Message" -Color Yellow
}

function Log-Error {
    param([string]$Message)
    Write-ColorOutput "[ERROR] $Message" -Color Red
}

function Test-Command {
    param([string]$Command)

    $exists = $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
    if ($exists) {
        Log-Success "$Command is installed"
    } else {
        Log-Error "$Command is not installed or not in PATH"
    }
    return $exists
}

# -----------------------------------------------------------------------------
# Prerequisite Checks
# -----------------------------------------------------------------------------

function Test-Prerequisites {
    Log-Info "Checking prerequisites..."

    $prerequisitesMet = $true

    if (-not (Test-Command "docker")) {
        Log-Error "Docker is required. Install Docker Desktop from: https://www.docker.com/products/docker-desktop"
        $prerequisitesMet = $false
    }

    # Check for docker-compose or docker compose plugin
    $hasDockerCompose = Test-Command "docker-compose"
    if (-not $hasDockerCompose) {
        Log-Warning "docker-compose not found, checking for 'docker compose' plugin..."
        try {
            docker compose version 2>&1 | Out-Null
            Log-Success "Docker Compose plugin is available"
            $global:ComposeCommand = "docker compose"
        } catch {
            Log-Error "Docker Compose is required"
            $prerequisitesMet = $false
        }
    } else {
        $global:ComposeCommand = "docker-compose"
    }

    if (-not $prerequisitesMet) {
        Log-Error "Prerequisite checks failed. Please install missing dependencies."
        exit 1
    }

    Log-Success "All prerequisites satisfied"
}

# -----------------------------------------------------------------------------
# Environment Configuration
# -----------------------------------------------------------------------------

function Initialize-EnvFile {
    Log-Info "Setting up environment configuration..."

    Set-Location $ProjectRoot

    if (Test-Path ".env") {
        Log-Warning ".env file already exists"
        $overwrite = Read-Host "Overwrite existing .env file? (y/N)"
        if ($overwrite -ne "y" -and $overwrite -ne "Y") {
            Log-Info "Keeping existing .env file"
            return
        }
    }

    if (-not (Test-Path ".env.example")) {
        Log-Error ".env.example not found in $ProjectRoot"
        exit 1
    }

    Copy-Item ".env.example" ".env"
    Log-Success "Created .env from .env.example"

    # Generate secure random secrets
    Log-Info "Generating secure secrets..."

    function Get-RandomBase64 {
        param([int]$Length)
        $bytes = New-Object byte[] $Length
        $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
        $rng.GetBytes($bytes)
        return [Convert]::ToBase64String($bytes)
    }

    $jwtSecret = Get-RandomBase64 32
    $betterAuthSecret = Get-RandomBase64 32
    $postgresPassword = Get-RandomBase64 16 -replace '[/+=]', '' | ForEach-Object { $_.Substring(0, 24) }

    # Update .env with generated secrets
    $envContent = Get-Content ".env" -Raw
    $envContent = $envContent -replace 'JWT_SECRET=.*', "JWT_SECRET=$jwtSecret"
    $envContent = $envContent -replace 'BETTER_AUTH_SECRET=.*', "BETTER_AUTH_SECRET=$betterAuthSecret"
    $envContent = $envContent -replace 'POSTGRES_PASSWORD=.*', "POSTGRES_PASSWORD=$postgresPassword"
    $envContent = $envContent -replace 'todo_user:dev_password_change_me_in_production@', "todo_user:$postgresPassword@"

    Set-Content ".env" $envContent

    Log-Success "Generated secure secrets and updated .env"
}

# -----------------------------------------------------------------------------
# Docker Compose Operations
# -----------------------------------------------------------------------------

function Start-Database {
    Log-Info "Starting PostgreSQL database..."

    Set-Location $ProjectRoot

    # Start PostgreSQL service
    Invoke-Expression "$global:ComposeCommand up -d postgres"

    Log-Info "Waiting for PostgreSQL to be healthy..."

    # Wait for health check (max 30 seconds)
    $maxAttempts = 30
    $attempt = 0

    while ($attempt -lt $maxAttempts) {
        try {
            $healthStatus = docker inspect todo_postgres_dev --format='{{.State.Health.Status}}' 2>$null
            if ($healthStatus -eq "healthy") {
                Log-Success "PostgreSQL is healthy and ready"
                return
            }
        } catch {
            # Container might not be running yet
        }

        $attempt++
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 1
    }

    Write-Host ""
    Log-Error "PostgreSQL failed to become healthy within $maxAttempts seconds"
    Log-Info "Checking logs..."
    Invoke-Expression "$global:ComposeCommand logs postgres"
    exit 1
}

# -----------------------------------------------------------------------------
# Database Verification
# -----------------------------------------------------------------------------

function Test-Database {
    Log-Info "Verifying database connection..."

    # Load environment variables
    Get-Content "$ProjectRoot\.env" | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
        }
    }

    $postgresUser = $env:POSTGRES_USER
    $postgresDb = $env:POSTGRES_DB

    # Test connection using docker exec
    try {
        docker exec todo_postgres_dev psql -U $postgresUser -d $postgresDb -c "SELECT version();" 2>&1 | Out-Null
        Log-Success "Database connection verified"

        # Show database version
        $dbVersion = docker exec todo_postgres_dev psql -U $postgresUser -d $postgresDb -t -c "SELECT version();"
        Log-Info "PostgreSQL Version: $($dbVersion.Trim())"
    } catch {
        Log-Error "Failed to connect to database"
        exit 1
    }
}

# -----------------------------------------------------------------------------
# Cleanup Function
# -----------------------------------------------------------------------------

function Remove-Environment {
    Log-Warning "Cleaning up development environment..."

    Set-Location $ProjectRoot

    $confirm = Read-Host "This will remove containers and volumes. Continue? (y/N)"
    if ($confirm -eq "y" -or $confirm -eq "Y") {
        Invoke-Expression "$global:ComposeCommand down -v"
        Log-Success "Environment cleaned up"
    } else {
        Log-Info "Cleanup cancelled"
    }
}

# -----------------------------------------------------------------------------
# Main Execution
# -----------------------------------------------------------------------------

function Main {
    param([string]$Command = "setup")

    Write-ColorOutput "==============================================" -Color Cyan
    Write-ColorOutput "  Evolution of Todo - Dev Environment Setup  " -Color Cyan
    Write-ColorOutput "==============================================" -Color Cyan
    Write-Host ""

    switch ($Command.ToLower()) {
        "setup" {
            Test-Prerequisites
            Initialize-EnvFile
            Start-Database
            Test-Database

            Write-Host ""
            Log-Success "Development environment setup complete!"
            Write-Host ""
            Log-Info "Next steps:"
            Write-Host "  1. Review and update .env file if needed"
            Write-Host "  2. Start backend: cd phase-2-web\backend; uvicorn app.main:app --reload"
            Write-Host "  3. Start frontend: cd phase-2-web\frontend; npm run dev"
            Write-Host ""
            Log-Info "Database management:"
            Write-Host "  - View logs: docker-compose logs -f postgres"
            Write-Host "  - Connect to DB: docker exec -it todo_postgres_dev psql -U todo_user -d todo_db"
            Write-Host "  - Stop services: docker-compose down"
            Write-Host "  - Cleanup all: .\scripts\init-dev-env.ps1 cleanup"
        }

        "cleanup" {
            Remove-Environment
        }

        "verify" {
            Test-Database
        }

        default {
            Log-Error "Unknown command: $Command"
            Write-Host "Usage: .\scripts\init-dev-env.ps1 {setup|cleanup|verify}"
            exit 1
        }
    }
}

# Execute main function
Main -Command $args[0]
