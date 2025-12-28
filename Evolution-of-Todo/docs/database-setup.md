# Database Setup Guide

## Overview

This project uses **PostgreSQL 16** as the database layer, with support for both local development (Docker) and production deployment (Neon Serverless PostgreSQL).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Development Environment                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │   Frontend   │         │   Backend    │                  │
│  │  (Next.js)   │────────▶│  (FastAPI)   │                  │
│  │  Port 3000   │  REST   │  Port 8000   │                  │
│  └──────────────┘         └──────┬───────┘                  │
│                                   │                           │
│                                   │ SQLModel/SQLAlchemy      │
│                                   ▼                           │
│                          ┌─────────────────┐                 │
│                          │   PostgreSQL    │                 │
│                          │  (Docker 16)    │                 │
│                          │   Port 5432     │                 │
│                          └─────────────────┘                 │
│                                   │                           │
│                                   ▼                           │
│                          ┌─────────────────┐                 │
│                          │  Persistent     │                 │
│                          │  Volume         │                 │
│                          └─────────────────┘                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   Production Environment                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │   Frontend   │         │   Backend    │                  │
│  │   (Vercel)   │────────▶│  (Vercel)    │                  │
│  └──────────────┘         └──────┬───────┘                  │
│                                   │                           │
│                                   │ TLS/SSL                   │
│                                   ▼                           │
│                          ┌─────────────────┐                 │
│                          │  Neon Serverless│                 │
│                          │   PostgreSQL    │                 │
│                          │   (Managed)     │                 │
│                          └─────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
- **Git** for version control

### Automated Setup (Recommended)

#### Windows (PowerShell)

```powershell
# Run the setup script
.\scripts\init-dev-env.ps1 setup
```

#### macOS/Linux (Bash)

```bash
# Make script executable
chmod +x scripts/init-dev-env.sh

# Run the setup script
./scripts/init-dev-env.sh setup
```

This will:
1. Check prerequisites (Docker, Docker Compose)
2. Create `.env` file from `.env.example`
3. Generate secure random secrets
4. Start PostgreSQL container
5. Verify database health

### Manual Setup

If you prefer manual setup or need troubleshooting:

1. **Create Environment File**

```bash
# Copy the example file
cp .env.example .env
```

2. **Generate Secure Secrets**

```bash
# Generate JWT secret (Linux/Mac)
openssl rand -base64 32

# Generate passwords
openssl rand -base64 16 | tr -d '/+='
```

Update `.env` with generated values:
```env
POSTGRES_PASSWORD=your_secure_password_here
JWT_SECRET=your_jwt_secret_here
BETTER_AUTH_SECRET=your_auth_secret_here
```

3. **Start PostgreSQL**

```bash
# Start database service
docker-compose up -d postgres

# View logs
docker-compose logs -f postgres
```

4. **Verify Database**

```bash
# Check container health
docker inspect todo_postgres_dev --format='{{.State.Health.Status}}'

# Connect to database
docker exec -it todo_postgres_dev psql -U todo_user -d todo_db
```

## Environment Variables

### Local Development

```env
# Database configuration
POSTGRES_DB=todo_db
POSTGRES_USER=todo_user
POSTGRES_PASSWORD=secure_password_here

# Connection settings
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Full connection string (auto-constructed)
DATABASE_URL=postgresql://todo_user:secure_password_here@localhost:5432/todo_db
```

### Production (Neon)

Replace `DATABASE_URL` with your Neon connection string:

```env
# Option 1: Direct connection
DATABASE_URL=postgresql://username:password@ep-cool-name-123456.us-east-2.aws.neon.tech/neondb?sslmode=require

# Option 2: Connection pooling (recommended for serverless)
DATABASE_URL=postgresql://username:password@ep-cool-name-123456-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require
```

## Docker Compose Configuration

### Services

#### PostgreSQL
- **Image**: `postgres:16-alpine`
- **Container Name**: `todo_postgres_dev`
- **Port**: `5432`
- **Health Check**: `pg_isready` every 5 seconds
- **Data Persistence**: Named volume `todo_postgres_data`

#### Optional: pgAdmin (Uncomment in docker-compose.yml)
- **Image**: `dpage/pgadmin4:latest`
- **Container Name**: `todo_pgadmin`
- **Port**: `5050`
- **Access**: `http://localhost:5050`

### Resource Limits

The PostgreSQL container has default resource limits:
- **CPU**: 1 core (limit), 0.5 core (reservation)
- **Memory**: 512MB (limit), 256MB (reservation)

Adjust in `docker-compose.yml` if needed for your workload.

## Database Operations

### Common Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f postgres

# Restart database
docker-compose restart postgres

# Complete cleanup (removes volumes)
docker-compose down -v
```

### Database Access

```bash
# Connect to database via psql
docker exec -it todo_postgres_dev psql -U todo_user -d todo_db

# Execute SQL file
docker exec -i todo_postgres_dev psql -U todo_user -d todo_db < schema.sql

# Backup database
docker exec todo_postgres_dev pg_dump -U todo_user todo_db > backup.sql

# Restore database
docker exec -i todo_postgres_dev psql -U todo_user -d todo_db < backup.sql
```

### SQL Queries (Example)

```sql
-- List all tables
\dt

-- Describe a table
\d tasks

-- Show database size
SELECT pg_size_pretty(pg_database_size('todo_db'));

-- Show active connections
SELECT * FROM pg_stat_activity;
```

## Migration Strategy

### Phase I → Phase II

Phase I used in-memory storage. Phase II introduces PostgreSQL.

**Migration Path**: No data migration needed (Phase I was ephemeral).

### Development → Production

When deploying to production:

1. **Create Neon Database**
   - Sign up at [neon.tech](https://neon.tech)
   - Create new project
   - Copy connection string

2. **Update Environment Variables**
   ```bash
   # In production .env (Vercel, etc.)
   DATABASE_URL=postgresql://user:pass@endpoint.neon.tech/db?sslmode=require
   ```

3. **Run Migrations**
   ```bash
   # Using Alembic (Phase IV+)
   alembic upgrade head
   ```

## Troubleshooting

### Container Won't Start

```bash
# Check Docker is running
docker ps

# View container logs
docker-compose logs postgres

# Remove and recreate
docker-compose down -v
docker-compose up -d postgres
```

### Connection Refused

```bash
# Verify container is healthy
docker inspect todo_postgres_dev --format='{{.State.Health.Status}}'

# Check port binding
docker port todo_postgres_dev

# Test connection from host
psql -h localhost -U todo_user -d todo_db
```

### Permission Denied

```bash
# Check volume permissions
docker volume inspect todo_postgres_data

# Recreate volume
docker-compose down -v
docker-compose up -d
```

### Slow Performance

```bash
# Check resource usage
docker stats todo_postgres_dev

# Increase shared buffers in docker-compose.yml
POSTGRES_SHARED_BUFFERS=256MB

# Restart container
docker-compose restart postgres
```

## Security Best Practices

### Local Development

1. **Never commit `.env` file** - It's in `.gitignore` for a reason
2. **Use strong passwords** - Even in development
3. **Rotate secrets regularly** - Regenerate after each team member change

### Production

1. **Use Neon connection pooling** - Better for serverless workloads
2. **Enable SSL/TLS** - `sslmode=require` in connection string
3. **Restrict network access** - Configure Neon IP allowlist
4. **Use read-only replicas** - For reporting/analytics queries
5. **Enable audit logging** - Track database access patterns

## Health Monitoring

### Health Check Endpoint

The PostgreSQL container includes a built-in health check:

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U todo_user -d todo_db"]
  interval: 5s
  timeout: 5s
  retries: 5
  start_period: 10s
```

### Manual Health Check

```bash
# Check container health
docker inspect todo_postgres_dev --format='{{.State.Health.Status}}'

# Check database connectivity
docker exec todo_postgres_dev pg_isready -U todo_user -d todo_db
```

## Performance Tuning

### Local Development

Default settings are optimized for development workloads. For larger datasets:

```env
# In .env
POSTGRES_MAX_CONNECTIONS=200
POSTGRES_SHARED_BUFFERS=256MB
```

### Production (Neon)

Neon handles performance tuning automatically, but you can:
- Use connection pooling endpoints
- Enable autoscaling (paid plans)
- Monitor query performance in Neon dashboard

## Next Steps

1. **Backend Integration**: Configure FastAPI with SQLModel
2. **Schema Design**: Define database models in `backend/app/models/`
3. **Migrations**: Set up Alembic for schema versioning (Phase IV)
4. **Testing**: Write database integration tests

## References

- [PostgreSQL Documentation](https://www.postgresql.org/docs/16/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Neon Documentation](https://neon.tech/docs)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)

---

**Last Updated**: 2025-12-29
**Author**: DevOps RAG Engineer
