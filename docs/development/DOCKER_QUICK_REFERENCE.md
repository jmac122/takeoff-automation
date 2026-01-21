# Docker Quick Reference Card

## 🎯 Your Development Setup

✅ **Cursor IDE** - Write code (local files)  
✅ **Docker** - Run everything (containers)  
✅ **Git** - Version control (local)

**Rule:** All execution commands use `docker compose exec` from the `docker/` directory

---

## 📂 Important: Working Directory & Environment

**All docker commands must be run from the `docker/` folder:**

```bash
cd docker                    # ALWAYS do this first!
docker compose up -d         # Now this works
```

**Environment file location:**
- ✅ `docker/.env` - Correct location
- ❌ `.env` in project root - Won't work!

```bash
# Create .env file
cp docker-env.example docker/.env
# Edit with your API keys
nano docker/.env
```

---

## 🚀 Essential Commands

### Start/Stop

```bash
cd docker                    # Navigate to docker folder first!

# Start all services
docker compose up -d

# Stop all services
docker compose down

# Restart a service
docker compose restart api

# View running services
docker compose ps
```

### Logs

```bash
# Follow all logs
docker compose logs -f

# Follow specific service
docker compose logs -f api
docker compose logs -f worker

# Last 100 lines
docker compose logs --tail=100 api
```

### Execute Commands

```bash
# Run Python script
docker compose exec api python script.py

# Run tests
docker compose exec api pytest

# Run migrations
docker compose exec api alembic upgrade head

# Get shell
docker compose exec api bash
```

---

## 🧪 Testing

```bash
# Run all tests
docker compose exec api pytest

# Run specific test file
docker compose exec api pytest tests/test_ocr_service.py

# Run with coverage
docker compose exec api pytest --cov=app tests/

# Run verification script
docker compose exec api python test_ocr_verification.py
```

---

## 🗄️ Database

```bash
# Check migration status
docker compose exec api alembic current

# Create migration
docker compose exec api alembic revision --autogenerate -m "description"

# Apply migrations
docker compose exec api alembic upgrade head

# ⚠️ CRITICAL: Always restart worker after migrations!
docker compose restart worker

# Rollback
docker compose exec api alembic downgrade -1

# Connect to PostgreSQL
docker compose exec db psql -U forgex -d forgex
```

**⚠️ IMPORTANT:** After running migrations, **always restart the worker**:
- Worker maintains long-lived DB connections
- Old connections don't know about new schema changes
- Causes errors like "column does not exist" or "operation in progress"
- Restarting clears the connection pool

---

## 📦 Package Management

```bash
# 1. Add to requirements.txt
echo "new-package==1.0.0" >> backend/requirements.txt

# 2. Rebuild container
docker compose build api

# 3. Restart
docker compose up -d api
```

---

## 🔧 Debugging

```bash
# Get shell in API container
docker compose exec api bash

# Check environment variables
docker compose exec api env

# Check if file exists
docker compose exec api ls -la /app

# Test import
docker compose exec api python -c "from app.services.ocr_service import OCRService"
```

---

## 🌐 Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| API | http://localhost:8000 | Backend |
| API Docs | http://localhost:8000/api/docs | Swagger |
| Frontend | http://localhost:5173 | React app |
| MinIO | http://localhost:9001 | Storage UI |

---

## ⚡ Daily Workflow

```bash
# Morning
cd docker                               # Navigate to docker folder
docker compose up -d                    # Start services
docker compose logs -f api              # Check logs

# During development
# Edit code in Cursor IDE (from project root)
# Save file (auto-syncs to Docker)
cd docker                               # Back to docker folder
docker compose exec api pytest          # Test changes

# Check something
docker compose logs --tail=50 api       # Recent logs
docker compose exec api bash            # Get shell

# Evening
docker compose down                     # Stop services
```

---

## 🚨 Troubleshooting

### Container won't start
```bash
docker compose logs api                 # Check error
docker compose down                     # Stop all
docker compose up -d                    # Restart
```

### Code changes not reflected
```bash
docker compose restart api              # Restart service
docker compose logs -f api              # Check reload
```

### Database issues
```bash
docker compose down -v                  # Remove volumes
docker compose up -d db                 # Start DB
docker compose exec api alembic upgrade head  # Migrate
```

### Clean slate
```bash
docker compose down -v                  # Remove everything
docker compose build --no-cache         # Rebuild from scratch
docker compose up -d                    # Start fresh
```

---

## ❌ Common Mistakes

### DON'T DO THIS:
```bash
# ❌ Running Python locally
python script.py
pip install package

# ❌ Running Node locally
npm install
npm run dev

# ❌ Direct docker commands
docker exec container_id python script.py
```

### DO THIS INSTEAD:
```bash
# ✅ Run in Docker
docker compose exec api python script.py
docker compose exec api pip install package

# ✅ Use docker compose
docker compose exec frontend npm install
docker compose exec frontend npm run dev

# ✅ Use docker compose exec
docker compose exec api python script.py
```

---

## 📚 Full Documentation

- **[Docker Workflow Guide](docs/development/DOCKER_WORKFLOW.md)** - Complete guide
- **[Phase 1B Deployment](PHASE_1B_DEPLOYMENT_NOTES.md)** - Deployment steps
- **[Main README](README.md)** - Project overview

---

## 💡 Pro Tips

1. **Alias for speed:**
   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   alias dce='cd /d/Repos/takeoff-automation/docker && docker compose exec'
   alias dcl='cd /d/Repos/takeoff-automation/docker && docker compose logs -f'
   alias dcd='cd /d/Repos/takeoff-automation/docker'
   
   # Now you can from anywhere:
   dce api pytest
   dcl api
   dcd  # Jump to docker folder
   ```

2. **Keep containers running:**
   - Don't stop containers between coding sessions
   - They use minimal resources when idle
   - Faster to restart than rebuild

3. **Check logs often:**
   ```bash
   docker compose logs -f api worker
   ```

4. **Use VS Code / Cursor terminal:**
   - Run docker commands from IDE terminal
   - No need to switch windows

---

**Remember:** Code in Cursor, Run in Docker! 🐳

**Last Updated:** January 19, 2026
