#!/usr/bin/env bash
# =============================================================================
# Database Setup Verification Script
# =============================================================================
# Purpose: Validate that PostgreSQL setup is correct and operational
# Author: DevOps RAG Engineer
# =============================================================================

set -euo pipefail

# Colors for output
readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# -----------------------------------------------------------------------------
# Test Framework
# -----------------------------------------------------------------------------

test_start() {
    echo -e "${BLUE}[TEST]${NC} $1"
    TESTS_RUN=$((TESTS_RUN + 1))
}

test_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

test_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

# -----------------------------------------------------------------------------
# Test Suite
# -----------------------------------------------------------------------------

test_docker_running() {
    test_start "Docker daemon is running"
    if docker info &> /dev/null; then
        test_pass "Docker is running"
        return 0
    else
        test_fail "Docker is not running"
        return 1
    fi
}

test_compose_file_exists() {
    test_start "docker-compose.yml exists"
    if [[ -f "$PROJECT_ROOT/docker-compose.yml" ]]; then
        test_pass "docker-compose.yml found"
        return 0
    else
        test_fail "docker-compose.yml not found"
        return 1
    fi
}

test_env_file_exists() {
    test_start ".env file exists"
    if [[ -f "$PROJECT_ROOT/.env" ]]; then
        test_pass ".env file found"
        return 0
    else
        test_fail ".env file not found (run init-dev-env.sh first)"
        return 1
    fi
}

test_env_variables_set() {
    test_start "Required environment variables are set"

    source "$PROJECT_ROOT/.env"

    local missing_vars=()

    [[ -z "${POSTGRES_DB:-}" ]] && missing_vars+=("POSTGRES_DB")
    [[ -z "${POSTGRES_USER:-}" ]] && missing_vars+=("POSTGRES_USER")
    [[ -z "${POSTGRES_PASSWORD:-}" ]] && missing_vars+=("POSTGRES_PASSWORD")
    [[ -z "${DATABASE_URL:-}" ]] && missing_vars+=("DATABASE_URL")

    if [[ ${#missing_vars[@]} -eq 0 ]]; then
        test_pass "All required environment variables are set"
        return 0
    else
        test_fail "Missing environment variables: ${missing_vars[*]}"
        return 1
    fi
}

test_container_running() {
    test_start "PostgreSQL container is running"

    if docker ps --filter "name=todo_postgres_dev" --format "{{.Names}}" | grep -q "todo_postgres_dev"; then
        test_pass "Container is running"
        return 0
    else
        test_fail "Container is not running (start with: docker-compose up -d postgres)"
        return 1
    fi
}

test_container_healthy() {
    test_start "PostgreSQL container is healthy"

    local health_status
    health_status=$(docker inspect todo_postgres_dev --format='{{.State.Health.Status}}' 2>/dev/null || echo "unknown")

    if [[ "$health_status" == "healthy" ]]; then
        test_pass "Container health status: healthy"
        return 0
    else
        test_fail "Container health status: $health_status"
        return 1
    fi
}

test_port_exposed() {
    test_start "PostgreSQL port is exposed"

    local port_mapping
    port_mapping=$(docker port todo_postgres_dev 5432 2>/dev/null || echo "")

    if [[ -n "$port_mapping" ]]; then
        test_pass "Port mapping: $port_mapping"
        return 0
    else
        test_fail "Port 5432 is not exposed"
        return 1
    fi
}

test_database_connection() {
    test_start "Database connection successful"

    source "$PROJECT_ROOT/.env"

    if docker exec todo_postgres_dev psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;" &> /dev/null; then
        test_pass "Successfully connected to database"
        return 0
    else
        test_fail "Failed to connect to database"
        return 1
    fi
}

test_database_version() {
    test_start "PostgreSQL version is 16.x"

    source "$PROJECT_ROOT/.env"

    local version
    version=$(docker exec todo_postgres_dev psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SHOW server_version;" | xargs)

    if [[ "$version" =~ ^16\. ]]; then
        test_pass "PostgreSQL version: $version"
        return 0
    else
        test_fail "Unexpected PostgreSQL version: $version"
        return 1
    fi
}

test_volume_exists() {
    test_start "Data volume exists"

    if docker volume ls --format "{{.Name}}" | grep -q "todo_postgres_data"; then
        test_pass "Volume 'todo_postgres_data' exists"
        return 0
    else
        test_fail "Volume 'todo_postgres_data' does not exist"
        return 1
    fi
}

test_network_exists() {
    test_start "Docker network exists"

    if docker network ls --format "{{.Name}}" | grep -q "todo_network"; then
        test_pass "Network 'todo_network' exists"
        return 0
    else
        test_fail "Network 'todo_network' does not exist"
        return 1
    fi
}

test_create_table() {
    test_start "Can create table"

    source "$PROJECT_ROOT/.env"

    local create_sql="CREATE TABLE IF NOT EXISTS test_table (id SERIAL PRIMARY KEY, name VARCHAR(100));"

    if docker exec todo_postgres_dev psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$create_sql" &> /dev/null; then
        test_pass "Successfully created test table"
        return 0
    else
        test_fail "Failed to create table"
        return 1
    fi
}

test_insert_data() {
    test_start "Can insert data"

    source "$PROJECT_ROOT/.env"

    local insert_sql="INSERT INTO test_table (name) VALUES ('test_data') RETURNING id;"

    if docker exec todo_postgres_dev psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$insert_sql" &> /dev/null; then
        test_pass "Successfully inserted data"
        return 0
    else
        test_fail "Failed to insert data"
        return 1
    fi
}

test_query_data() {
    test_start "Can query data"

    source "$PROJECT_ROOT/.env"

    local query_sql="SELECT COUNT(*) FROM test_table;"
    local count
    count=$(docker exec todo_postgres_dev psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "$query_sql" | xargs)

    if [[ "$count" -gt 0 ]]; then
        test_pass "Successfully queried data (count: $count)"
        return 0
    else
        test_fail "Query returned no data"
        return 1
    fi
}

test_cleanup_test_table() {
    test_start "Cleanup test table"

    source "$PROJECT_ROOT/.env"

    local drop_sql="DROP TABLE IF EXISTS test_table;"

    if docker exec todo_postgres_dev psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$drop_sql" &> /dev/null; then
        test_pass "Successfully cleaned up test table"
        return 0
    else
        test_fail "Failed to cleanup test table"
        return 1
    fi
}

test_connection_string_format() {
    test_start "DATABASE_URL format is valid"

    source "$PROJECT_ROOT/.env"

    if [[ "$DATABASE_URL" =~ ^postgresql:// ]]; then
        test_pass "DATABASE_URL has correct format"
        return 0
    else
        test_fail "DATABASE_URL format is invalid: $DATABASE_URL"
        return 1
    fi
}

# -----------------------------------------------------------------------------
# Main Execution
# -----------------------------------------------------------------------------

main() {
    echo -e "${BLUE}"
    echo "=============================================="
    echo "  Database Setup Verification Suite          "
    echo "=============================================="
    echo -e "${NC}"
    echo

    cd "$PROJECT_ROOT"

    # Configuration tests
    echo -e "${YELLOW}Configuration Tests${NC}"
    test_compose_file_exists
    test_env_file_exists
    test_env_variables_set || true
    test_connection_string_format || true
    echo

    # Docker tests
    echo -e "${YELLOW}Docker Tests${NC}"
    test_docker_running || { echo -e "${RED}Docker is not running. Aborting tests.${NC}"; exit 1; }
    test_container_running || { echo -e "${RED}Container is not running. Run: docker-compose up -d postgres${NC}"; exit 1; }
    test_container_healthy || true
    test_port_exposed || true
    test_volume_exists || true
    test_network_exists || true
    echo

    # Database tests
    echo -e "${YELLOW}Database Connectivity Tests${NC}"
    test_database_connection || { echo -e "${RED}Cannot connect to database. Check logs: docker-compose logs postgres${NC}"; exit 1; }
    test_database_version || true
    echo

    # Operations tests
    echo -e "${YELLOW}Database Operations Tests${NC}"
    test_create_table || true
    test_insert_data || true
    test_query_data || true
    test_cleanup_test_table || true
    echo

    # Summary
    echo -e "${BLUE}"
    echo "=============================================="
    echo "  Test Summary                                "
    echo "=============================================="
    echo -e "${NC}"
    echo "Tests Run:    $TESTS_RUN"
    echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"

    if [[ $TESTS_FAILED -gt 0 ]]; then
        echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
        echo
        echo -e "${YELLOW}Troubleshooting Tips:${NC}"
        echo "1. Ensure Docker is running: docker info"
        echo "2. Start database: docker-compose up -d postgres"
        echo "3. Check logs: docker-compose logs postgres"
        echo "4. Run setup: ./scripts/init-dev-env.sh setup"
        exit 1
    else
        echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
        echo
        echo -e "${GREEN}All tests passed! Database setup is operational.${NC}"
        exit 0
    fi
}

main "$@"
