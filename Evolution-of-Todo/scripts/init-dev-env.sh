#!/usr/bin/env bash
# =============================================================================
# Evolution of Todo - Development Environment Initialization Script
# =============================================================================
# Purpose: Automated setup of local development environment
# Author: DevOps RAG Engineer
# =============================================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is not installed or not in PATH"
        return 1
    fi
    log_success "$1 is installed"
    return 0
}

# -----------------------------------------------------------------------------
# Prerequisite Checks
# -----------------------------------------------------------------------------

check_prerequisites() {
    log_info "Checking prerequisites..."

    local prerequisites_met=true

    if ! check_command "docker"; then
        log_error "Docker is required. Install from: https://docs.docker.com/get-docker/"
        prerequisites_met=false
    fi

    if ! check_command "docker-compose"; then
        log_warning "docker-compose not found, checking for 'docker compose' plugin..."
        if docker compose version &> /dev/null; then
            log_success "Docker Compose plugin is available"
        else
            log_error "Docker Compose is required"
            prerequisites_met=false
        fi
    fi

    if [[ "$prerequisites_met" == false ]]; then
        log_error "Prerequisite checks failed. Please install missing dependencies."
        exit 1
    fi

    log_success "All prerequisites satisfied"
}

# -----------------------------------------------------------------------------
# Environment Configuration
# -----------------------------------------------------------------------------

setup_env_file() {
    log_info "Setting up environment configuration..."

    cd "$PROJECT_ROOT"

    if [[ -f ".env" ]]; then
        log_warning ".env file already exists"
        read -p "Overwrite existing .env file? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Keeping existing .env file"
            return 0
        fi
    fi

    if [[ ! -f ".env.example" ]]; then
        log_error ".env.example not found in $PROJECT_ROOT"
        exit 1
    fi

    cp .env.example .env
    log_success "Created .env from .env.example"

    # Generate secure random secrets
    log_info "Generating secure secrets..."

    if command -v openssl &> /dev/null; then
        JWT_SECRET=$(openssl rand -base64 32)
        BETTER_AUTH_SECRET=$(openssl rand -base64 32)
        POSTGRES_PASSWORD=$(openssl rand -base64 16 | tr -d '/+=' | head -c 24)

        # Update .env with generated secrets (macOS/Linux compatible)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s|JWT_SECRET=.*|JWT_SECRET=${JWT_SECRET}|" .env
            sed -i '' "s|BETTER_AUTH_SECRET=.*|BETTER_AUTH_SECRET=${BETTER_AUTH_SECRET}|" .env
            sed -i '' "s|POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=${POSTGRES_PASSWORD}|" .env
            sed -i '' "s|todo_user:dev_password_change_me_in_production@|todo_user:${POSTGRES_PASSWORD}@|" .env
        else
            sed -i "s|JWT_SECRET=.*|JWT_SECRET=${JWT_SECRET}|" .env
            sed -i "s|BETTER_AUTH_SECRET=.*|BETTER_AUTH_SECRET=${BETTER_AUTH_SECRET}|" .env
            sed -i "s|POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=${POSTGRES_PASSWORD}|" .env
            sed -i "s|todo_user:dev_password_change_me_in_production@|todo_user:${POSTGRES_PASSWORD}@|" .env
        fi

        log_success "Generated secure secrets and updated .env"
    else
        log_warning "OpenSSL not found. Please manually update secrets in .env"
    fi
}

# -----------------------------------------------------------------------------
# Docker Compose Operations
# -----------------------------------------------------------------------------

start_database() {
    log_info "Starting PostgreSQL database..."

    cd "$PROJECT_ROOT"

    # Determine Docker Compose command
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi

    # Start PostgreSQL service
    $COMPOSE_CMD up -d postgres

    log_info "Waiting for PostgreSQL to be healthy..."

    # Wait for health check (max 30 seconds)
    local max_attempts=30
    local attempt=0

    while [[ $attempt -lt $max_attempts ]]; do
        if docker inspect todo_postgres_dev --format='{{.State.Health.Status}}' 2>/dev/null | grep -q "healthy"; then
            log_success "PostgreSQL is healthy and ready"
            return 0
        fi

        attempt=$((attempt + 1))
        echo -n "."
        sleep 1
    done

    echo
    log_error "PostgreSQL failed to become healthy within ${max_attempts} seconds"
    log_info "Checking logs..."
    $COMPOSE_CMD logs postgres
    exit 1
}

# -----------------------------------------------------------------------------
# Database Verification
# -----------------------------------------------------------------------------

verify_database() {
    log_info "Verifying database connection..."

    # Source environment variables
    source "$PROJECT_ROOT/.env"

    # Test connection using docker exec
    if docker exec todo_postgres_dev psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT version();" &> /dev/null; then
        log_success "Database connection verified"

        # Show database version
        DB_VERSION=$(docker exec todo_postgres_dev psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT version();" | head -n1)
        log_info "PostgreSQL Version: $DB_VERSION"
    else
        log_error "Failed to connect to database"
        exit 1
    fi
}

# -----------------------------------------------------------------------------
# Cleanup Function
# -----------------------------------------------------------------------------

cleanup() {
    log_warning "Cleaning up development environment..."

    cd "$PROJECT_ROOT"

    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi

    read -p "This will remove containers and volumes. Continue? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        $COMPOSE_CMD down -v
        log_success "Environment cleaned up"
    else
        log_info "Cleanup cancelled"
    fi
}

# -----------------------------------------------------------------------------
# Main Execution
# -----------------------------------------------------------------------------

main() {
    echo -e "${BLUE}"
    echo "=============================================="
    echo "  Evolution of Todo - Dev Environment Setup  "
    echo "=============================================="
    echo -e "${NC}"

    # Parse command line arguments
    case "${1:-setup}" in
        setup)
            check_prerequisites
            setup_env_file
            start_database
            verify_database

            echo
            log_success "Development environment setup complete!"
            echo
            log_info "Next steps:"
            echo "  1. Review and update .env file if needed"
            echo "  2. Start backend: cd phase-2-web/backend && uvicorn app.main:app --reload"
            echo "  3. Start frontend: cd phase-2-web/frontend && npm run dev"
            echo
            log_info "Database management:"
            echo "  - View logs: docker-compose logs -f postgres"
            echo "  - Connect to DB: docker exec -it todo_postgres_dev psql -U todo_user -d todo_db"
            echo "  - Stop services: docker-compose down"
            echo "  - Cleanup all: ./scripts/init-dev-env.sh cleanup"
            ;;

        cleanup)
            cleanup
            ;;

        verify)
            verify_database
            ;;

        *)
            log_error "Unknown command: $1"
            echo "Usage: $0 {setup|cleanup|verify}"
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"
