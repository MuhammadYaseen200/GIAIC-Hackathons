#!/usr/bin/env bash
################################################################################
# Automated Vercel Deployment Script for Evolution-of-Todo Phase 2
################################################################################
# This script automates the full deployment workflow:
# - Generates secure JWT secrets
# - Sets environment variables via Vercel CLI
# - Deploys both backend and frontend to production
#
# Usage:
#   ./deploy-to-vercel.sh --database-url "postgresql+asyncpg://..."
#
# Options:
#   --database-url URL       Neon PostgreSQL connection string (required)
#   --frontend-url URL       Custom frontend URL (optional)
#   --backend-url URL        Custom backend URL (optional)
#   --skip-deploy            Only set environment variables, don't deploy
#   --help                   Show this help message
################################################################################

set -euo pipefail

# Color output functions
header() { echo -e "\n\033[1;36m=== $1 ===\033[0m"; }
success() { echo -e "\033[1;32m[OK] $1\033[0m"; }
error() { echo -e "\033[1;31m[ERROR] $1\033[0m"; exit 1; }
warning() { echo -e "\033[1;33m[WARN] $1\033[0m"; }
info() { echo -e "\033[1;34m[INFO] $1\033[0m"; }

# Parse command-line arguments
DATABASE_URL=""
FRONTEND_URL=""
BACKEND_URL=""
SKIP_DEPLOY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --database-url)
            DATABASE_URL="$2"
            shift 2
            ;;
        --frontend-url)
            FRONTEND_URL="$2"
            shift 2
            ;;
        --backend-url)
            BACKEND_URL="$2"
            shift 2
            ;;
        --skip-deploy)
            SKIP_DEPLOY=true
            shift
            ;;
        --help)
            grep '^#' "$0" | tail -n +2 | sed 's/^# *//'
            exit 0
            ;;
        *)
            error "Unknown option: $1 (use --help for usage)"
            ;;
    esac
done

# Validate required arguments
if [[ -z "$DATABASE_URL" ]]; then
    error "Missing required argument: --database-url"
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

header "Evolution-of-Todo Vercel Deployment Automation"
info "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"

################################################################################
# Prerequisite Checks
################################################################################
header "Checking Prerequisites"

# Check Vercel CLI
if ! command -v vercel &> /dev/null; then
    error "Vercel CLI not found. Install with: npm install -g vercel"
fi
success "Vercel CLI found: $(vercel --version)"

# Check Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    error "Python not found. Install Python 3.13+ from python.org"
fi
PYTHON_CMD=$(command -v python3 || command -v python)
success "Python found: $($PYTHON_CMD --version)"

# Verify directory structure
if [[ ! -d "$BACKEND_DIR" ]]; then
    error "Backend directory not found: $BACKEND_DIR"
fi
if [[ ! -d "$FRONTEND_DIR" ]]; then
    error "Frontend directory not found: $FRONTEND_DIR"
fi
success "Project structure verified"

# Verify Vercel authentication
header "Verifying Vercel Authentication"
if ! WHOAMI=$(vercel whoami 2>&1); then
    error "Not logged into Vercel. Run: vercel login"
fi
success "Logged in as: $WHOAMI"

################################################################################
# Generate Secure JWT Secret
################################################################################
header "Generating Secure JWT Secret"
SECRET_KEY=$($PYTHON_CMD -c "import secrets; print(secrets.token_urlsafe(32))")
if [[ -z "$SECRET_KEY" ]]; then
    error "Failed to generate secret key"
fi
success "Generated 256-bit JWT secret"

################################################################################
# Resolve Deployment URLs
################################################################################
header "Resolving Deployment URLs"

# Auto-detect backend URL if not provided
if [[ -z "$BACKEND_URL" ]]; then
    pushd "$BACKEND_DIR" > /dev/null
    if BACKEND_INSPECT=$(vercel inspect 2>&1); then
        BACKEND_URL=$(echo "$BACKEND_INSPECT" | grep -oP 'https://[^\s]+\.vercel\.app' | head -1)
        if [[ -n "$BACKEND_URL" ]]; then
            success "Auto-detected backend URL: $BACKEND_URL"
        else
            warning "Could not auto-detect backend URL"
            read -p "Enter backend production URL (e.g., https://backend-xyz.vercel.app): " BACKEND_URL
        fi
    else
        warning "Could not inspect backend project. You may need to deploy first."
        read -p "Enter backend production URL: " BACKEND_URL
    fi
    popd > /dev/null
fi

# Auto-detect frontend URL if not provided
if [[ -z "$FRONTEND_URL" ]]; then
    pushd "$FRONTEND_DIR" > /dev/null
    if FRONTEND_INSPECT=$(vercel inspect 2>&1); then
        FRONTEND_URL=$(echo "$FRONTEND_INSPECT" | grep -oP 'https://[^\s]+\.vercel\.app' | head -1)
        if [[ -n "$FRONTEND_URL" ]]; then
            success "Auto-detected frontend URL: $FRONTEND_URL"
        else
            warning "Could not auto-detect frontend URL"
            read -p "Enter frontend production URL (e.g., https://frontend-xyz.vercel.app): " FRONTEND_URL
        fi
    else
        warning "Could not inspect frontend project. You may need to deploy first."
        read -p "Enter frontend production URL: " FRONTEND_URL
    fi
    popd > /dev/null
fi

# Prepare CORS origins (JSON array)
CORS_ORIGINS="[\"$FRONTEND_URL\"]"

################################################################################
# Display Configuration Summary
################################################################################
header "Deployment Configuration"
echo "Backend URL:      $BACKEND_URL"
echo "Frontend URL:     $FRONTEND_URL"
echo "Database:         $(echo "$DATABASE_URL" | sed -E 's|.*@([^/]+)/.*|\1|')"
echo "JWT Secret:       ***${SECRET_KEY: -8}"
echo "CORS Origins:     $CORS_ORIGINS"

echo ""
warning "Press ENTER to continue or Ctrl+C to abort..."
read -r

################################################################################
# Configure Backend Environment
################################################################################
header "Configuring Backend Environment"
pushd "$BACKEND_DIR" > /dev/null

declare -A BACKEND_ENV_VARS=(
    ["DATABASE_URL"]="$DATABASE_URL"
    ["SECRET_KEY"]="$SECRET_KEY"
    ["CORS_ORIGINS"]="$CORS_ORIGINS"
    ["ALGORITHM"]="HS256"
    ["ACCESS_TOKEN_EXPIRE_MINUTES"]="1440"
)

for key in "${!BACKEND_ENV_VARS[@]}"; do
    info "Setting $key..."
    value="${BACKEND_ENV_VARS[$key]}"

    # Remove existing variable first (ignore errors)
    vercel env rm "$key" production --yes 2>/dev/null || true

    # Add new variable
    if echo "$value" | vercel env add "$key" production > /dev/null 2>&1; then
        success "$key configured"
    else
        warning "Failed to set $key (may already exist)"
    fi
done

popd > /dev/null

################################################################################
# Configure Frontend Environment
################################################################################
header "Configuring Frontend Environment"
pushd "$FRONTEND_DIR" > /dev/null

declare -A FRONTEND_ENV_VARS=(
    ["NEXT_PUBLIC_API_URL"]="$BACKEND_URL"
    ["BACKEND_URL"]="$BACKEND_URL"
)

for key in "${!FRONTEND_ENV_VARS[@]}"; do
    info "Setting $key..."
    value="${FRONTEND_ENV_VARS[$key]}"

    # Remove existing variable first (ignore errors)
    vercel env rm "$key" production --yes 2>/dev/null || true

    # Add new variable
    if echo "$value" | vercel env add "$key" production > /dev/null 2>&1; then
        success "$key configured"
    else
        warning "Failed to set $key (may already exist)"
    fi
done

popd > /dev/null

################################################################################
# Deploy Services
################################################################################
if [[ "$SKIP_DEPLOY" == true ]]; then
    header "Deployment Skipped"
    info "Environment variables configured. Deploy manually with:"
    info "  cd backend && vercel --prod"
    info "  cd frontend && vercel --prod"
    exit 0
fi

# Deploy backend
header "Deploying Backend to Production"
pushd "$BACKEND_DIR" > /dev/null
if vercel --prod --yes; then
    success "Backend deployed successfully"
else
    error "Backend deployment failed"
fi
popd > /dev/null

# Deploy frontend
header "Deploying Frontend to Production"
pushd "$FRONTEND_DIR" > /dev/null
if vercel --prod --yes; then
    success "Frontend deployed successfully"
else
    error "Frontend deployment failed"
fi
popd > /dev/null

################################################################################
# Post-Deployment Reminders
################################################################################
header "Post-Deployment Actions Required"
warning "Database migrations must be run manually!"
info "Run migrations with:"
info "  cd backend"
info "  export DATABASE_URL='$DATABASE_URL'"
info "  uv run alembic upgrade head"

################################################################################
# Verification Steps
################################################################################
header "Deployment Verification"
info "Test your deployment:"
info "  1. Backend health: curl $BACKEND_URL/health"
info "  2. Frontend: Open $FRONTEND_URL in browser"
info "  3. Register test user via frontend UI"
info "  4. Test task CRUD operations"

################################################################################
# Save Deployment Record
################################################################################
header "Saving Deployment Record"
DEPLOYMENT_RECORD="$SCRIPT_DIR/vercel-deployment-$(date '+%Y%m%d-%H%M%S').txt"

cat > "$DEPLOYMENT_RECORD" <<EOF
================================================================================
VERCEL DEPLOYMENT RECORD
================================================================================
Timestamp: $(date '+%Y-%m-%d %H:%M:%S')
Deployed by: $WHOAMI

URLs:
  Frontend: $FRONTEND_URL
  Backend:  $BACKEND_URL

Backend Environment:
  DATABASE_URL: $(echo "$DATABASE_URL" | sed -E 's|.*@([^/]+)/.*|\1|')
  SECRET_KEY: ***${SECRET_KEY: -8}
  CORS_ORIGINS: $CORS_ORIGINS

Frontend Environment:
  NEXT_PUBLIC_API_URL: $BACKEND_URL
  BACKEND_URL: $BACKEND_URL

================================================================================
NEXT STEPS:
1. Run database migrations (see command above)
2. Test endpoints (curl commands above)
3. Monitor Vercel deployment logs
================================================================================
EOF

success "Deployment record saved: $DEPLOYMENT_RECORD"

header "Deployment Complete"
success "All services deployed successfully!"
