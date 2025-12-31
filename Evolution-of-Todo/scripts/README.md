# Development Scripts

This directory contains automated scripts for managing the Evolution of Todo development environment.

## Available Scripts

### 1. Environment Initialization

#### `init-dev-env.sh` (Linux/macOS)
Automated setup script for PostgreSQL development environment.

**Usage:**
```bash
# Make executable
chmod +x scripts/init-dev-env.sh

# Full setup
./scripts/init-dev-env.sh setup

# Verify database connection
./scripts/init-dev-env.sh verify

# Cleanup environment
./scripts/init-dev-env.sh cleanup
```

**What it does:**
- Checks prerequisites (Docker, Docker Compose)
- Creates `.env` from `.env.example`
- Generates secure random secrets (JWT, passwords)
- Starts PostgreSQL container
- Waits for database health check
- Verifies database connectivity

#### `init-dev-env.ps1` (Windows PowerShell)
Windows-compatible version of the initialization script.

**Usage:**
```powershell
# Full setup
.\scripts\init-dev-env.ps1 setup

# Verify database connection
.\scripts\init-dev-env.ps1 verify

# Cleanup environment
.\scripts\init-dev-env.ps1 cleanup
```

**Requirements:**
- PowerShell 5.1+
- Docker Desktop for Windows

### 2. Database Verification

#### `verify-db-setup.sh`
Comprehensive test suite to validate database configuration and connectivity.

**Usage:**
```bash
# Make executable
chmod +x scripts/verify-db-setup.sh

# Run all tests
./scripts/verify-db-setup.sh
```

**Tests performed:**
1. Configuration validation
   - docker-compose.yml exists
   - .env file exists
   - Required environment variables set
   - DATABASE_URL format valid

2. Docker infrastructure
   - Docker daemon running
   - Container running
   - Container healthy
   - Port exposed correctly
   - Volume exists
   - Network exists

3. Database connectivity
   - Connection successful
   - PostgreSQL version correct (16.x)

4. Database operations
   - Create table
   - Insert data
   - Query data
   - Cleanup test data

**Exit codes:**
- `0`: All tests passed
- `1`: One or more tests failed

## Quick Start Guide

### First Time Setup

**Windows:**
```powershell
# 1. Run setup
.\scripts\init-dev-env.ps1 setup

# 2. Verify installation
docker-compose ps

# 3. Check logs
docker-compose logs -f postgres
```

**macOS/Linux:**
```bash
# 1. Make scripts executable
chmod +x scripts/*.sh

# 2. Run setup
./scripts/init-dev-env.sh setup

# 3. Run verification tests
./scripts/verify-db-setup.sh

# 4. Check logs
docker-compose logs -f postgres
```

### Daily Workflow

```bash
# Start database
docker-compose up -d postgres

# Verify connection
./scripts/verify-db-setup.sh  # Or: .\scripts\init-dev-env.ps1 verify

# Work on your code...

# Stop database
docker-compose down
```

### Troubleshooting

```bash
# View logs
docker-compose logs -f postgres

# Restart database
docker-compose restart postgres

# Complete reset (WARNING: Deletes all data)
./scripts/init-dev-env.sh cleanup
./scripts/init-dev-env.sh setup
```

## Script Details

### Secret Generation

Both initialization scripts generate secure secrets using:
- **Linux/macOS**: OpenSSL random byte generation
- **Windows**: .NET RandomNumberGenerator

Generated secrets:
- `JWT_SECRET`: 32-byte base64 (for JWT token signing)
- `BETTER_AUTH_SECRET`: 32-byte base64 (for Better Auth)
- `POSTGRES_PASSWORD`: 24-character random string

### Health Check Logic

The scripts wait for PostgreSQL to be healthy before proceeding:
- Max wait time: 30 seconds
- Check interval: 1 second
- Health check: `pg_isready` command

If health check fails, the script will:
1. Display error message
2. Show container logs
3. Exit with error code

### Idempotency

All scripts are idempotent:
- Running setup multiple times is safe
- Existing `.env` file prompts for confirmation
- Docker Compose handles existing containers gracefully

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `POSTGRES_DB` | Database name | `todo_db` |
| `POSTGRES_USER` | Database user | `todo_user` |
| `POSTGRES_PASSWORD` | User password | `secure_password` |
| `DATABASE_URL` | Full connection string | `postgresql://...` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_HOST` | Database host | `localhost` |
| `POSTGRES_PORT` | Database port | `5432` |
| `POSTGRES_MAX_CONNECTIONS` | Max connections | `100` |
| `POSTGRES_SHARED_BUFFERS` | Shared memory | `128MB` |

## File Structure

```
scripts/
├── README.md                  # This file
├── init-dev-env.sh            # Setup script (Bash)
├── init-dev-env.ps1           # Setup script (PowerShell)
└── verify-db-setup.sh         # Verification tests (Bash)
```

## Common Issues

### Issue: "Docker is not running"
**Solution:**
```bash
# Windows/macOS: Start Docker Desktop
# Linux: sudo systemctl start docker
```

### Issue: "Container failed to become healthy"
**Diagnosis:**
```bash
# Check logs
docker-compose logs postgres

# Common causes:
# - Port 5432 already in use
# - Insufficient disk space
# - Invalid environment variables
```

**Solution:**
```bash
# Stop conflicting PostgreSQL
sudo systemctl stop postgresql  # Linux
brew services stop postgresql   # macOS

# Or change port in .env
POSTGRES_PORT=5433
```

### Issue: "Permission denied" (Linux)
**Solution:**
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Run with correct permissions
./scripts/init-dev-env.sh setup
```

### Issue: "Cannot connect to database"
**Diagnosis:**
```bash
# Check container status
docker ps | grep postgres

# Check health
docker inspect todo_postgres_dev --format='{{.State.Health.Status}}'

# Test connection manually
docker exec -it todo_postgres_dev psql -U todo_user -d todo_db
```

## Best Practices

1. **Always run verification tests** after setup
   ```bash
   ./scripts/verify-db-setup.sh
   ```

2. **Check logs regularly** during development
   ```bash
   docker-compose logs -f postgres
   ```

3. **Backup data before cleanup**
   ```bash
   docker exec todo_postgres_dev pg_dump -U todo_user todo_db > backup.sql
   ```

4. **Keep secrets secure**
   - Never commit `.env` to Git
   - Regenerate secrets regularly
   - Use different secrets for each environment

## Advanced Usage

### Custom PostgreSQL Configuration

Create `docker-compose.override.yml`:
```yaml
version: '3.9'

services:
  postgres:
    environment:
      POSTGRES_MAX_CONNECTIONS: 200
      POSTGRES_SHARED_BUFFERS: 256MB
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
```

### Database Initialization Scripts

Place SQL files in `scripts/sql/`:
```sql
-- scripts/sql/init.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```

Update `docker-compose.yml`:
```yaml
volumes:
  - ./scripts/sql/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
```

### Remote Database Access

To connect from outside Docker network:
```bash
# Use host port directly
psql -h localhost -p 5432 -U todo_user -d todo_db

# Or via DATABASE_URL
psql $DATABASE_URL
```

## Migration to Production

When moving to Neon in production:

1. **Export schema:**
   ```bash
   docker exec todo_postgres_dev pg_dump -U todo_user --schema-only todo_db > schema.sql
   ```

2. **Update `.env.production`:**
   ```env
   DATABASE_URL=postgresql://user:pass@endpoint.neon.tech/db?sslmode=require
   ```

3. **Run migrations** (Alembic, Phase IV)

4. **Verify connectivity:**
   ```bash
   psql $DATABASE_URL -c "SELECT version();"
   ```

## Support

For issues or questions:
1. Check documentation in `docs/database-setup.md`
2. Review quick reference in `docs/database-quick-reference.md`
3. View container logs: `docker-compose logs postgres`
4. Consult PostgreSQL docs: https://www.postgresql.org/docs/16/

---

**Last Updated**: 2025-12-29
**Maintained by**: DevOps RAG Engineer
