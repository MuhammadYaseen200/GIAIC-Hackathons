# Database Quick Reference Card

## Setup Commands

### Automated Setup
```bash
# Windows
.\scripts\init-dev-env.ps1 setup

# macOS/Linux
./scripts/init-dev-env.sh setup
```

### Manual Setup
```bash
# 1. Create environment file
cp .env.example .env

# 2. Generate secrets (macOS/Linux)
openssl rand -base64 32  # For JWT_SECRET
openssl rand -base64 32  # For BETTER_AUTH_SECRET
openssl rand -base64 16  # For POSTGRES_PASSWORD

# 3. Start database
docker-compose up -d postgres

# 4. Verify health
docker inspect todo_postgres_dev --format='{{.State.Health.Status}}'
```

## Daily Operations

### Start/Stop
```bash
docker-compose up -d postgres      # Start
docker-compose down                 # Stop
docker-compose restart postgres     # Restart
docker-compose logs -f postgres     # View logs
```

### Database Access
```bash
# Connect to database
docker exec -it todo_postgres_dev psql -U todo_user -d todo_db

# Quick query
docker exec todo_postgres_dev psql -U todo_user -d todo_db -c "SELECT COUNT(*) FROM tasks;"
```

### Backup/Restore
```bash
# Backup
docker exec todo_postgres_dev pg_dump -U todo_user todo_db > backup_$(date +%Y%m%d).sql

# Restore
docker exec -i todo_postgres_dev psql -U todo_user -d todo_db < backup_20251229.sql
```

## Environment Variables

### Local Development
```env
DATABASE_URL=postgresql://todo_user:password@localhost:5432/todo_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=todo_db
POSTGRES_USER=todo_user
POSTGRES_PASSWORD=your_secure_password
```

### Production (Neon)
```env
DATABASE_URL=postgresql://user:pass@ep-name.region.aws.neon.tech/db?sslmode=require
```

## Useful SQL Queries

### Schema Inspection
```sql
-- List tables
\dt

-- Describe table structure
\d tasks

-- Show indexes
\di
```

### Database Stats
```sql
-- Database size
SELECT pg_size_pretty(pg_database_size('todo_db'));

-- Table size
SELECT pg_size_pretty(pg_relation_size('tasks'));

-- Active connections
SELECT COUNT(*) FROM pg_stat_activity WHERE datname = 'todo_db';
```

### Data Operations
```sql
-- Count all tasks
SELECT COUNT(*) FROM tasks;

-- Recent tasks
SELECT * FROM tasks ORDER BY created_at DESC LIMIT 10;

-- Tasks by user
SELECT user_id, COUNT(*) as task_count FROM tasks GROUP BY user_id;
```

## Troubleshooting

### Connection Issues
```bash
# Check container status
docker ps | grep postgres

# View detailed logs
docker-compose logs --tail=50 postgres

# Test connectivity
docker exec todo_postgres_dev pg_isready -U todo_user -d todo_db
```

### Reset Database
```bash
# WARNING: This deletes all data
docker-compose down -v
docker-compose up -d postgres
```

### Performance Check
```bash
# Container resource usage
docker stats todo_postgres_dev

# Database cache hit ratio (should be >90%)
docker exec todo_postgres_dev psql -U todo_user -d todo_db -c \
  "SELECT sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) AS cache_hit_ratio FROM pg_statio_user_tables;"
```

## Health Checks

### Container Health
```bash
# Check health status
docker inspect todo_postgres_dev --format='{{.State.Health.Status}}'

# Manual health check
docker exec todo_postgres_dev pg_isready -U todo_user -d todo_db
```

### Database Connectivity
```bash
# From host (requires psql client)
psql -h localhost -U todo_user -d todo_db -c "SELECT version();"

# From container
docker exec todo_postgres_dev psql -U todo_user -d todo_db -c "SELECT version();"
```

## Security Checklist

- [ ] `.env` file is in `.gitignore`
- [ ] Strong passwords generated (min 16 chars)
- [ ] JWT secrets are random base64 strings (32+ bytes)
- [ ] Production uses Neon with SSL (`sslmode=require`)
- [ ] Database credentials never committed to Git
- [ ] `.env.example` contains no real secrets

## Migration Paths

### Local → Production
1. Export schema: `pg_dump --schema-only`
2. Update `DATABASE_URL` to Neon endpoint
3. Run migrations (Alembic)
4. Verify connectivity

### Development → Staging
1. Create Neon staging database
2. Copy production schema
3. Seed with test data
4. Update staging `.env`

## Container Details

| Property | Value |
|----------|-------|
| Image | `postgres:16-alpine` |
| Container Name | `todo_postgres_dev` |
| Port | `5432` |
| Volume | `todo_postgres_data` |
| Network | `todo_network` |
| Health Check | Every 5s |
| CPU Limit | 1 core |
| Memory Limit | 512MB |

## File Locations

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Service definitions |
| `.env` | Environment variables (local) |
| `.env.example` | Template with docs |
| `scripts/init-dev-env.sh` | Setup script (Bash) |
| `scripts/init-dev-env.ps1` | Setup script (PowerShell) |
| `docs/database-setup.md` | Full documentation |

## Next Steps After Setup

1. **Backend**: Configure SQLModel connection
   ```python
   from sqlmodel import create_engine
   engine = create_engine(DATABASE_URL)
   ```

2. **Schema**: Define models in `backend/app/models/`

3. **Migrations**: Initialize Alembic (Phase IV)
   ```bash
   alembic init migrations
   ```

4. **Testing**: Write integration tests
   ```python
   import pytest
   from sqlmodel import Session, create_engine
   ```

## Emergency Recovery

### Complete Reset
```bash
# Stop all services
docker-compose down -v

# Remove images (optional)
docker rmi postgres:16-alpine

# Start fresh
./scripts/init-dev-env.sh setup
```

### Data Corruption
```bash
# 1. Stop database
docker-compose stop postgres

# 2. Restore from backup
docker exec -i todo_postgres_dev psql -U todo_user -d todo_db < latest_backup.sql

# 3. Restart
docker-compose start postgres
```

---

**Quick Help**: See full documentation in `docs/database-setup.md`
