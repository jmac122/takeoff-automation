# Deployment and Setup Guide - Phase 1A

## Overview

This guide covers the complete setup and deployment process for Phase 1A of the AI Construction Takeoff Platform. The system consists of a FastAPI backend, React frontend, PostgreSQL database, Redis queue, and MinIO object storage.

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   React App     │    │   FastAPI        │
│   (Frontend)    │◄──►│   Backend        │
│                 │    │                 │
│ • Vite          │    │ • Document       │
│ • TypeScript    │    │   Processing     │
│ • TailwindCSS   │    │ • API Endpoints  │
└─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx         │    │   PostgreSQL    │    │   Redis         │
│   (Web Server)  │    │   Database      │    │   Queue         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                  │
                                                  ▼
                                           ┌─────────────────┐
                                           │   MinIO         │
                                           │   Object Store  │
                                           └─────────────────┘
```

## Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 20.04+), macOS, or Windows 10+
- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 10GB free space
- **Network**: Internet connection for dependencies

### Software Dependencies

#### Backend
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Node.js 18+ (for frontend)

#### Development Tools
- Git
- Docker & Docker Compose (optional)
- VS Code or similar IDE

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/takeoff-platform.git
cd takeoff-platform
```

### 2. Backend Setup

#### Install Python Dependencies

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# For development (optional)
pip install -r requirements-dev.txt
```

#### Database Setup

```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
```

```sql
CREATE DATABASE takeoff;
CREATE USER takeoff_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE takeoff TO takeoff_user;
\q
```

```bash
# Or use Docker
docker run --name postgres-takeoff -e POSTGRES_DB=takeoff \
  -e POSTGRES_USER=takeoff_user -e POSTGRES_PASSWORD=your_password \
  -p 5432:5432 -d postgres:15
```

#### Redis Setup

```bash
# Install Redis (Ubuntu/Debian)
sudo apt install redis-server
sudo systemctl start redis-server

# Or use Docker
docker run --name redis-takeoff -p 6379:6379 -d redis:7
```

#### MinIO Setup

```bash
# Using Docker (recommended for development)
docker run --name minio-takeoff \
  -p 9000:9000 -p 9001:9001 \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  -v /data/minio:/data \
  -d minio/minio server /data --console-address ":9001"
```

Access MinIO console at: http://localhost:9001

#### Environment Configuration

```bash
# Create .env file in backend directory
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Application
SECRET_KEY=your-super-secret-key-here-32-chars-min
APP_ENV=development
DEBUG=true

# Database
DATABASE_URL=postgresql+asyncpg://takeoff_user:your_password@localhost:5432/takeoff

# Redis/Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Storage (MinIO)
STORAGE_ENDPOINT=localhost:9000
STORAGE_ACCESS_KEY=minioadmin
STORAGE_SECRET_KEY=minioadmin
STORAGE_BUCKET=takeoff-documents
STORAGE_USE_SSL=false

# Optional: LLM API Keys (for future phases)
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GOOGLE_AI_API_KEY=
```

#### Database Migration

```bash
# Run database migrations
alembic upgrade head

# Verify migration
alembic current
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at: http://localhost:5173

### 4. Backend Server

```bash
cd backend

# Activate virtual environment
source venv/bin/activate

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend API will be available at: http://localhost:8000

### 5. Celery Worker

```bash
cd backend

# Activate virtual environment
source venv/bin/activate

# Start worker
celery -A app.workers.celery_app worker --loglevel=info
```

### 6. Verify Setup

#### Test API Health

```bash
curl http://localhost:8000/api/v1/health
# Expected: {"status": "healthy"}
```

#### Test Frontend

Open http://localhost:5173 in browser - should show the React app.

## Docker Development Setup

### Using Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: takeoff
      POSTGRES_USER: takeoff_user
      POSTGRES_PASSWORD: takeoff_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  minio:
    image: minio/minio
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data

  backend:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql+asyncpg://takeoff_user:takeoff_password@postgres:5432/takeoff
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - STORAGE_ENDPOINT=minio:9000
      - STORAGE_ACCESS_KEY=minioadmin
      - STORAGE_SECRET_KEY=minioadmin
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
      - minio
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  worker:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql+asyncpg://takeoff_user:takeoff_password@postgres:5432/takeoff
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - STORAGE_ENDPOINT=minio:9000
      - STORAGE_ACCESS_KEY=minioadmin
      - STORAGE_SECRET_KEY=minioadmin
    depends_on:
      - postgres
      - redis
      - minio
    volumes:
      - ./backend:/app
    command: celery -A app.workers.celery_app worker --loglevel=info

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev -- --host 0.0.0.0

volumes:
  postgres_data:
  minio_data:
```

### Docker Build Files

#### Backend Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

#### Frontend Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Build and serve
RUN npm run build
EXPOSE 5173
CMD ["npm", "run", "preview", "--", "--port", "5173", "--host"]
```

### Running with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

## Production Deployment

### Infrastructure Setup

#### 1. Server Provisioning

```bash
# Example with Ubuntu 22.04 LTS
# Minimum: 2 vCPU, 4GB RAM, 20GB SSD

# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y curl wget git htop ufw
```

#### 2. Security Setup

```bash
# Configure firewall
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

# Create application user
sudo useradd -m -s /bin/bash takeoff
sudo usermod -aG sudo takeoff

# Setup SSH key authentication (recommended)
# Copy your public key to /home/takeoff/.ssh/authorized_keys
```

#### 3. Database Setup (PostgreSQL)

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Configure PostgreSQL
sudo -u postgres psql

# In PostgreSQL shell:
CREATE DATABASE takeoff_prod;
CREATE USER takeoff_prod WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE takeoff_prod TO takeoff_prod;
ALTER USER takeoff_prod CREATEDB;
\q

# Enable remote connections (if needed)
# Edit /etc/postgresql/15/main/pg_hba.conf
# Add: host    takeoff_prod    takeoff_prod    your_server_ip/32    md5

sudo systemctl restart postgresql
```

#### 4. Redis Setup

```bash
# Install Redis
sudo apt install redis-server

# Configure Redis (optional - default is usually fine)
# Edit /etc/redis/redis.conf if needed

sudo systemctl enable redis-server
sudo systemctl start redis-server
```

#### 5. MinIO Setup

```bash
# Download and install MinIO
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
sudo mv minio /usr/local/bin/

# Create MinIO user and directories
sudo useradd -r minio -s /sbin/nologin
sudo mkdir -p /opt/minio/data
sudo chown minio:minio /opt/minio/data

# Create systemd service
sudo tee /etc/systemd/system/minio.service > /dev/null <<EOF
[Unit]
Description=MinIO
Documentation=https://docs.min.io
Wants=network-online.target
After=network-online.target
AssertFileIsExecutable=/usr/local/bin/minio

[Service]
User=minio
Group=minio
ProtectProc=invisible
EnvironmentFile=-/etc/default/minio
ExecStartPre=/bin/bash -c "if [ -z \"\$MINIO_VOLUMES\" ]; then echo \"Variable MINIO_VOLUMES not set in /etc/default/minio\"; exit 1; fi"
ExecStart=/usr/local/bin/minio server \$MINIO_VOLUMES
Restart=always
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

# Configure MinIO
sudo tee /etc/default/minio > /dev/null <<EOF
MINIO_VOLUMES="/opt/minio/data"
MINIO_OPTS="--console-address :9001"
MINIO_ROOT_USER="your_minio_admin"
MINIO_ROOT_PASSWORD="your_secure_minio_password"
EOF

# Start MinIO
sudo systemctl enable minio
sudo systemctl start minio
```

#### 6. Application Deployment

```bash
# Clone repository
cd /home/takeoff
git clone https://github.com/your-org/takeoff-platform.git
cd takeoff-platform

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create production .env
cp .env.example .env
# Edit .env with production values

# Run migrations
alembic upgrade head

# Frontend build
cd ../frontend
npm ci
npm run build

# Install PM2 for process management
sudo npm install -g pm2

# Create ecosystem file
tee ecosystem.config.js > /dev/null <<EOF
module.exports = {
  apps: [
    {
      name: 'takeoff-backend',
      script: 'uvicorn',
      args: 'app.main:app --host 0.0.0.0 --port 8000',
      cwd: '/home/takeoff/takeoff-platform/backend',
      interpreter: 'venv/bin/python',
      instances: 1,
      exec_mode: 'fork',
      env: {
        NODE_ENV: 'production'
      }
    },
    {
      name: 'takeoff-worker',
      script: 'celery',
      args: '-A app.workers.celery_app worker --loglevel=info',
      cwd: '/home/takeoff/takeoff-platform/backend',
      interpreter: 'venv/bin/python',
      instances: 1,
      exec_mode: 'fork'
    }
  ]
};
EOF

# Start applications
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

#### 7. Web Server Setup (Nginx)

```bash
# Install Nginx
sudo apt install nginx

# Configure Nginx
sudo tee /etc/nginx/sites-available/takeoff > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:5173;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Static files
    location /static/ {
        alias /home/takeoff/takeoff-platform/frontend/dist/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/takeoff /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 8. SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Configure automatic renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Monitoring and Maintenance

#### Health Checks

```bash
# API health
curl https://your-domain.com/api/v1/health

# Application status
pm2 status

# Logs
pm2 logs takeoff-backend --lines 50
pm2 logs takeoff-worker --lines 50

# Nginx status
sudo systemctl status nginx

# Database status
sudo -u postgres psql -c "SELECT version();"
```

#### Backup Strategy

```bash
# Database backup
pg_dump -U takeoff_prod takeoff_prod > backup_$(date +%Y%m%d_%H%M%S).sql

# MinIO backup
# Use mc (MinIO client) or rclone for object storage backup

# Application backup
tar -czf app_backup_$(date +%Y%m%d).tar.gz /home/takeoff/takeoff-platform
```

#### Log Rotation

```bash
# PM2 log rotation
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 10M
pm2 set pm2-logrotate:retain 7

# Nginx log rotation (usually configured by default)
```

### Scaling Considerations

#### Horizontal Scaling

```bash
# Multiple backend instances
pm2 start ecosystem.config.js -i 4  # 4 instances

# Load balancer configuration (Nginx)
upstream backend {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
    server localhost:8003;
}

# Multiple workers
pm2 start ecosystem.config.js --only takeoff-worker -i 2
```

#### Database Optimization

```sql
-- Create indexes for performance
CREATE INDEX CONCURRENTLY idx_documents_status_created
ON documents(status, created_at DESC);

CREATE INDEX CONCURRENTLY idx_pages_document_status
ON pages(document_id, status);

-- Partition large tables (future)
-- Partition documents by month
-- Partition measurements by page
```

### Troubleshooting

#### Common Issues

1. **Application won't start**
   ```bash
   # Check logs
   pm2 logs takeoff-backend

   # Check environment
   pm2 show takeoff-backend

   # Restart
   pm2 restart takeoff-backend
   ```

2. **Database connection issues**
   ```bash
   # Test connection
   psql -U takeoff_prod -d takeoff_prod -h localhost

   # Check PostgreSQL logs
   sudo tail -f /var/log/postgresql/postgresql-15-main.log
   ```

3. **File upload issues**
   ```bash
   # Check MinIO status
   sudo systemctl status minio

   # Check MinIO logs
   sudo journalctl -u minio -f
   ```

4. **Worker not processing**
   ```bash
   # Check Redis
   redis-cli ping

   # Check worker status
   pm2 show takeoff-worker

   # Restart worker
   pm2 restart takeoff-worker
   ```

### Performance Tuning

#### Database Tuning

```sql
-- Adjust PostgreSQL settings in postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
max_wal_size = 1GB
```

#### Application Tuning

```python
# Gunicorn configuration (for production)
bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
```

#### Monitoring Setup

```bash
# Install monitoring tools
sudo apt install prometheus prometheus-node-exporter grafana

# PM2 monitoring
pm2 install pm2-prometheus
```

This deployment guide provides a complete setup for both development and production environments, ensuring the document ingestion system is robust, scalable, and maintainable.