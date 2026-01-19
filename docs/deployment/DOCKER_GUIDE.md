# Docker Guide - ForgeX Takeoffs

Complete guide for Docker operations and troubleshooting.

---

## 🚀 Quick Commands

### Start All Services
```bash
cd docker
docker compose up -d
```

### Check Status
```bash
docker compose ps
docker ps
```

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api
docker compose logs -f worker
docker compose logs -f db
```

### Stop Services
```bash
docker compose down
```

### Rebuild After Changes
```bash
# Rebuild specific service
docker compose build api

# Rebuild all with no cache
docker compose build --no-cache

# Rebuild and restart
docker compose up -d --build
```

---

## 📦 Container Details

### forgex-api (FastAPI Application)
- **Port:** 8000
- **Image:** Built from `Dockerfile.api`
- **Dependencies:** `requirements-base.txt` (500MB)
- **Volume:** Hot-reload enabled (`../backend:/app`)
- **Health:** http://localhost:8000/api/v1/health

**Access:**
```bash
# Shell access
docker exec -it forgex-api bash

# Run migrations
docker exec -e DATABASE_URL=postgresql+psycopg2://forgex:forgex@db:5432/forgex forgex-api alembic upgrade head

# Check logs
docker logs forgex-api -f
```

### forgex-worker (Celery Worker)
- **Image:** Built from `Dockerfile.worker`
- **Dependencies:** Same as API
- **Volume:** Hot-reload enabled
- **Tasks:** Document processing, OCR, AI operations

**Access:**
```bash
# Shell access
docker exec -it forgex-worker bash

# Check worker status
docker exec forgex-worker celery -A app.workers.celery_app inspect active

# Monitor tasks
docker logs forgex-worker -f
```

### forgex-db (PostgreSQL 15)
- **Port:** 5432
- **Database:** forgex
- **User/Pass:** forgex/forgex
- **Volume:** `postgres_data` (persistent)

**Access:**
```bash
# psql shell
docker exec -it forgex-db psql -U forgex -d forgex

# List tables
docker exec forgex-db psql -U forgex -d forgex -c "\dt"

# Backup database
docker exec forgex-db pg_dump -U forgex forgex > backup.sql

# Restore database
cat backup.sql | docker exec -i forgex-db psql -U forgex -d forgex
```

### forgex-redis (Redis 7)
- **Port:** 6379
- **Volume:** `redis_data` (persistent)
- **Usage:** Celery broker/backend, caching

**Access:**
```bash
# Redis CLI
docker exec -it forgex-redis redis-cli

# Check keys
docker exec forgex-redis redis-cli KEYS "*"

# Monitor commands
docker exec forgex-redis redis-cli MONITOR

# Flush all (careful!)
docker exec forgex-redis redis-cli FLUSHALL
```

### forgex-minio (S3-Compatible Storage)
- **API Port:** 9000
- **Console Port:** 9001
- **User/Pass:** minioadmin/minioadmin
- **Volume:** `minio_data` (persistent)
- **Bucket:** takeoff-documents

**Access:**
- Console: http://localhost:9001
- API: http://localhost:9000

**CLI:**
```bash
# List buckets
docker exec forgex-minio mc ls local

# List files
docker exec forgex-minio mc ls local/takeoff-documents
```

---

## 🔧 Common Operations

### Database Migrations
```bash
# Run migrations
docker exec -e DATABASE_URL=postgresql+psycopg2://forgex:forgex@db:5432/forgex forgex-api alembic upgrade head

# Check current version
docker exec forgex-api alembic current

# Create new migration
docker exec forgex-api alembic revision --autogenerate -m "description"

# Rollback one version
docker exec forgex-api alembic downgrade -1
```

### Celery Task Management
```bash
# Active tasks
docker exec forgex-worker celery -A app.workers.celery_app inspect active

# Registered tasks
docker exec forgex-worker celery -A app.workers.celery_app inspect registered

# Worker stats
docker exec forgex-worker celery -A app.workers.celery_app inspect stats

# Purge all tasks
docker exec forgex-worker celery -A app.workers.celery_app purge
```

### Data Management
```bash
# Full backup
docker compose down
tar -czf backup.tar.gz docker/postgres_data docker/minio_data docker/redis_data

# Full restore
tar -xzf backup.tar.gz
docker compose up -d

# Reset everything (WARNING: Deletes all data!)
docker compose down -v
docker compose up -d
```

---

## 🐛 Troubleshooting

### Container Won't Start
```bash
# Check logs
docker compose logs servicename

# Rebuild container
docker compose build --no-cache servicename
docker compose up -d servicename

# Remove and recreate
docker compose rm -f servicename
docker compose up -d servicename
```

### Database Connection Issues
```bash
# Check if database is healthy
docker exec forgex-db pg_isready -U forgex

# Check connections
docker exec forgex-db psql -U forgex -d forgex -c "SELECT count(*) FROM pg_stat_activity;"

# Restart database
docker compose restart db
```

### Out of Disk Space
```bash
# Check Docker disk usage
docker system df

# Clean up
docker system prune -a --volumes

# Remove unused images
docker image prune -a

# Remove old build cache
docker builder prune -a
```

### Port Already in Use
```bash
# Find what's using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill /PID <pid> /F

# Or change port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead
```

### Hot Reload Not Working
```bash
# Check volume mount
docker inspect forgex-api | grep -A 10 Mounts

# Restart with fresh mount
docker compose down
docker compose up -d
```

---

## 📊 Performance Optimization

### Image Size Optimization
Current setup uses `requirements-base.txt` (500MB) instead of full ML packages (2.5GB).

**Add ML packages later** (Phase 4A):
```dockerfile
# In Dockerfile.api or Dockerfile.worker
RUN pip install -r requirements-ml.txt
```

### Build Caching
Docker caches layers. To maximize cache:
1. Dependencies change less than code
2. COPY requirements before COPY code
3. Use `--build-arg CACHEBUST=$(date +%s)` to force rebuild

### Resource Limits
Add to `docker-compose.yml`:
```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 512M
```

---

## 🔐 Security Best Practices

### Production Checklist
- [ ] Change default passwords (PostgreSQL, MinIO, Redis)
- [ ] Use Docker secrets for sensitive data
- [ ] Run containers as non-root user (already done)
- [ ] Enable TLS for external connections
- [ ] Restrict network access
- [ ] Regular security updates

### Environment Variables
Never commit `.env` files! Use `.env.example` as template.

**Production:**
```yaml
env_file:
  - .env.production
```

---

## 📈 Monitoring

### Health Checks
All services have health checks defined in `docker-compose.yml`:
```bash
# Check health status
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### Resource Usage
```bash
# Real-time stats
docker stats

# Specific container
docker stats forgex-api
```

### Logs Management
```bash
# Limit log size in docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

---

## 🚀 Next Steps

- See [DEPLOYMENT_SETUP.md](./DEPLOYMENT_SETUP.md) for production deployment
- See [../plans/SETUP_COMPLETE.md](../plans/SETUP_COMPLETE.md) for current system status
- See [../README.md](../README.md) for project overview

---

**Last Updated:** January 19, 2026
