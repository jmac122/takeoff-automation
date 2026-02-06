# Phase 6: Deployment & Operations
## Production Deployment and Monitoring

> **Duration**: Weeks 30-36
> **Prerequisites**: Testing & QA complete (Phase 5B), all core features tested and passing
> **Outcome**: Production-ready deployment with monitoring, alerting, backup systems, and operational runbooks

---

## Context for LLM Assistant

You are implementing the production deployment infrastructure for a construction takeoff platform. This phase establishes:
- Docker containerization and orchestration
- Production infrastructure provisioning
- CI/CD pipeline for automated deployments
- Monitoring, logging, and alerting systems
- Backup and disaster recovery procedures
- Security hardening and compliance
- Operational runbooks and documentation

### Deployment Philosophy

The platform follows a **container-first, infrastructure-as-code** approach:
- All services run in Docker containers
- Infrastructure defined in Terraform/CloudFormation
- Immutable deployments with zero-downtime updates
- Comprehensive observability from day one

```
Deployment Architecture:
┌─────────────────────────────────────────────────────────────────────┐
│                        Load Balancer (Nginx/ALB)                     │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        ▼                         ▼                         ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│   Frontend    │       │   API (x3)    │       │   Workers     │
│   (Static)    │       │   FastAPI     │       │   Celery (x5) │
└───────────────┘       └───────────────┘       └───────────────┘
                                  │                         │
        ┌─────────────────────────┴─────────────────────────┤
        ▼                         ▼                         ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│  PostgreSQL   │       │     Redis     │       │     MinIO     │
│   (Primary)   │       │   (Cluster)   │       │   (Storage)   │
└───────────────┘       └───────────────┘       └───────────────┘
```

### Environment Strategy

| Environment | Purpose | Update Frequency |
|-------------|---------|------------------|
| **Development** | Local development | On save |
| **Staging** | Integration testing | On PR merge |
| **Production** | Live users | Manual approval |

---

## Infrastructure Directory Structure

```
takeoff-platform/
├── docker/
│   ├── Dockerfile.api
│   ├── Dockerfile.worker
│   ├── Dockerfile.frontend
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   └── docker-compose.override.yml
├── infrastructure/
│   ├── terraform/
│   │   ├── environments/
│   │   │   ├── staging/
│   │   │   │   ├── main.tf
│   │   │   │   ├── variables.tf
│   │   │   │   └── terraform.tfvars
│   │   │   └── production/
│   │   │       ├── main.tf
│   │   │       ├── variables.tf
│   │   │       └── terraform.tfvars
│   │   ├── modules/
│   │   │   ├── networking/
│   │   │   ├── database/
│   │   │   ├── storage/
│   │   │   ├── compute/
│   │   │   └── monitoring/
│   │   └── shared/
│   │       └── versions.tf
│   ├── kubernetes/
│   │   ├── base/
│   │   │   ├── namespace.yaml
│   │   │   ├── api-deployment.yaml
│   │   │   ├── worker-deployment.yaml
│   │   │   ├── frontend-deployment.yaml
│   │   │   ├── services.yaml
│   │   │   └── configmaps.yaml
│   │   ├── overlays/
│   │   │   ├── staging/
│   │   │   └── production/
│   │   └── kustomization.yaml
│   └── scripts/
│       ├── deploy.sh
│       ├── rollback.sh
│       ├── backup-db.sh
│       └── restore-db.sh
├── monitoring/
│   ├── prometheus/
│   │   ├── prometheus.yml
│   │   ├── alerts/
│   │   │   ├── api-alerts.yml
│   │   │   ├── worker-alerts.yml
│   │   │   └── infrastructure-alerts.yml
│   │   └── rules/
│   ├── grafana/
│   │   ├── provisioning/
│   │   │   ├── dashboards/
│   │   │   │   ├── api-dashboard.json
│   │   │   │   ├── worker-dashboard.json
│   │   │   │   ├── ai-accuracy-dashboard.json
│   │   │   │   └── business-metrics-dashboard.json
│   │   │   └── datasources/
│   │   └── grafana.ini
│   └── alertmanager/
│       └── alertmanager.yml
├── logging/
│   ├── fluentd/
│   │   └── fluent.conf
│   └── elasticsearch/
│       └── elasticsearch.yml
└── docs/
    └── operations/
        ├── runbooks/
        │   ├── incident-response.md
        │   ├── scaling-procedures.md
        │   ├── backup-restore.md
        │   └── troubleshooting.md
        ├── architecture-decision-records/
        └── disaster-recovery-plan.md
```

---

## Docker Configuration

### Task 12.1: Production Dockerfiles

Create `docker/Dockerfile.api`:

```dockerfile
# Multi-stage build for optimized production image
# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Production
FROM python:3.11-slim as production

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini .

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

Create `docker/Dockerfile.worker`:

```dockerfile
# Multi-stage build for Celery worker
FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim as production

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash appuser

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY backend/app ./app

RUN chown -R appuser:appuser /app

USER appuser

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    C_FORCE_ROOT=false

# Celery worker command
CMD ["celery", "-A", "app.workers.celery_app", "worker", \
     "--loglevel=info", "--concurrency=4", \
     "--max-tasks-per-child=100"]
```

Create `docker/Dockerfile.frontend`:

```dockerfile
# Multi-stage build for frontend
# Stage 1: Build
FROM node:20-alpine as builder

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci --only=production=false

# Copy source code
COPY frontend/ .

# Build arguments for environment configuration
ARG VITE_API_URL
ARG VITE_APP_VERSION
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_APP_VERSION=$VITE_APP_VERSION

# Build application
RUN npm run build

# Stage 2: Production
FROM nginx:alpine as production

# Copy custom nginx config
COPY docker/nginx/nginx.conf /etc/nginx/nginx.conf
COPY docker/nginx/default.conf /etc/nginx/conf.d/default.conf

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Add non-root user
RUN adduser -D -u 1001 appuser && \
    chown -R appuser:appuser /var/cache/nginx && \
    chown -R appuser:appuser /var/log/nginx && \
    chown -R appuser:appuser /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R appuser:appuser /var/run/nginx.pid

USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

### Task 12.2: Production Docker Compose

Create `docker/docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  # API Service
  api:
    build:
      context: ..
      dockerfile: docker/Dockerfile.api
    image: takeoff-platform/api:${IMAGE_TAG:-latest}
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
        order: start-first
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - MINIO_ENDPOINT=${MINIO_ENDPOINT}
      - MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY}
      - MINIO_SECRET_KEY=${MINIO_SECRET_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
      - CORS_ORIGINS=${CORS_ORIGINS}
      # NEW v2.0: Assembly System configuration
      - ASSEMBLY_DEFAULT_WASTE_PERCENT=${ASSEMBLY_DEFAULT_WASTE_PERCENT:-5}
      # NEW v2.0: Auto Count configuration
      - AUTO_COUNT_DEFAULT_THRESHOLD=${AUTO_COUNT_DEFAULT_THRESHOLD:-0.80}
      - AUTO_COUNT_MAX_DETECTIONS=${AUTO_COUNT_MAX_DETECTIONS:-500}
      # NEW v2.0: Review Interface configuration
      - REVIEW_AUTO_ACCEPT_DEFAULT_THRESHOLD=${REVIEW_AUTO_ACCEPT_DEFAULT_THRESHOLD:-0.90}
      - REVIEW_ENABLE_KEYBOARD_SHORTCUTS=${REVIEW_ENABLE_KEYBOARD_SHORTCUTS:-true}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "5"
    networks:
      - internal
      - external

  # Worker Service
  worker:
    build:
      context: ..
      dockerfile: docker/Dockerfile.worker
    image: takeoff-platform/worker:${IMAGE_TAG:-latest}
    deploy:
      replicas: 5
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - MINIO_ENDPOINT=${MINIO_ENDPOINT}
      - MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY}
      - MINIO_SECRET_KEY=${MINIO_SECRET_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "5"
    networks:
      - internal

  # Celery Beat Scheduler
  beat:
    build:
      context: ..
      dockerfile: docker/Dockerfile.worker
    image: takeoff-platform/worker:${IMAGE_TAG:-latest}
    command: ["celery", "-A", "app.workers.celery_app", "beat", "--loglevel=info"]
    deploy:
      replicas: 1
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - ENVIRONMENT=production
    networks:
      - internal

  # Frontend Service
  frontend:
    build:
      context: ..
      dockerfile: docker/Dockerfile.frontend
      args:
        - VITE_API_URL=${VITE_API_URL}
        - VITE_APP_VERSION=${IMAGE_TAG:-latest}
    image: takeoff-platform/frontend:${IMAGE_TAG:-latest}
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
      restart_policy:
        condition: on-failure
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - external

  # Nginx Load Balancer
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
    depends_on:
      - api
      - frontend
    networks:
      - external
      - internal

networks:
  internal:
    driver: overlay
    internal: true
  external:
    driver: overlay
```

### Task 12.3: Nginx Configuration

Create `docker/nginx/nginx.conf`:

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging format with request ID for tracing
    log_format main '$remote_addr - $remote_user [$time_local] '
                    '"$request" $status $body_bytes_sent '
                    '"$http_referer" "$http_user_agent" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time" '
                    'rid=$request_id';

    access_log /var/log/nginx/access.log main;

    # Performance optimizations
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json 
               application/javascript application/xml application/rss+xml 
               application/atom+xml image/svg+xml;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Rate limiting zones
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/s;
    limit_req_zone $binary_remote_addr zone=upload_limit:10m rate=10r/s;
    limit_conn_zone $binary_remote_addr zone=conn_limit:10m;

    # Upstream definitions
    upstream api_servers {
        least_conn;
        server api:8000 weight=1 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    upstream frontend_servers {
        server frontend:8080 weight=1;
        keepalive 16;
    }

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;

    include /etc/nginx/conf.d/*.conf;
}
```

Create `docker/nginx/conf.d/default.conf`:

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name _;
    
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
    
    location / {
        return 301 https://$host$request_uri;
    }
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    server_name _;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # Request size limits
    client_max_body_size 500M;  # For large plan uploads
    client_body_buffer_size 128k;
    client_body_timeout 300s;

    # Proxy timeouts for long-running requests
    proxy_connect_timeout 60s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;

    # Frontend static files
    location / {
        proxy_pass http://frontend_servers;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Request-ID $request_id;
        proxy_cache_bypass $http_upgrade;

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            proxy_pass http://frontend_servers;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # API endpoints
    location /api/ {
        limit_req zone=api_limit burst=50 nodelay;
        limit_conn conn_limit 100;

        proxy_pass http://api_servers;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Request-ID $request_id;
        proxy_set_header Connection "";

        # Disable buffering for streaming responses
        proxy_buffering off;
    }

    # Upload endpoints with different limits
    location /api/v1/projects/*/documents {
        limit_req zone=upload_limit burst=5 nodelay;
        limit_conn conn_limit 10;

        client_max_body_size 500M;

        proxy_pass http://api_servers;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Request-ID $request_id;
        proxy_set_header Connection "";

        # Increase timeouts for uploads
        proxy_connect_timeout 60s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }

    # WebSocket for real-time updates
    location /ws/ {
        proxy_pass http://api_servers;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Request-ID $request_id;

        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }

    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://api_servers/health;
    }

    # Metrics endpoint (internal only)
    location /metrics {
        allow 10.0.0.0/8;
        allow 172.16.0.0/12;
        allow 192.168.0.0/16;
        deny all;

        proxy_pass http://api_servers/metrics;
    }
}
```

---

## Terraform Infrastructure

### Task 12.4: AWS Infrastructure Modules

Create `infrastructure/terraform/modules/networking/main.tf`:

```hcl
# VPC and Networking Module

variable "environment" {
  type        = string
  description = "Environment name (staging/production)"
}

variable "vpc_cidr" {
  type        = string
  default     = "10.0.0.0/16"
  description = "CIDR block for VPC"
}

variable "availability_zones" {
  type        = list(string)
  description = "List of availability zones"
}

# VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "takeoff-${var.environment}-vpc"
    Environment = var.environment
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name        = "takeoff-${var.environment}-igw"
    Environment = var.environment
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, count.index)
  availability_zone = var.availability_zones[count.index]

  map_public_ip_on_launch = true

  tags = {
    Name        = "takeoff-${var.environment}-public-${count.index + 1}"
    Environment = var.environment
    Type        = "public"
  }
}

# Private Subnets
resource "aws_subnet" "private" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, count.index + length(var.availability_zones))
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name        = "takeoff-${var.environment}-private-${count.index + 1}"
    Environment = var.environment
    Type        = "private"
  }
}

# NAT Gateway (one per AZ for high availability)
resource "aws_eip" "nat" {
  count  = length(var.availability_zones)
  domain = "vpc"

  tags = {
    Name        = "takeoff-${var.environment}-nat-eip-${count.index + 1}"
    Environment = var.environment
  }
}

resource "aws_nat_gateway" "main" {
  count         = length(var.availability_zones)
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = {
    Name        = "takeoff-${var.environment}-nat-${count.index + 1}"
    Environment = var.environment
  }
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name        = "takeoff-${var.environment}-public-rt"
    Environment = var.environment
  }
}

resource "aws_route_table" "private" {
  count  = length(var.availability_zones)
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }

  tags = {
    Name        = "takeoff-${var.environment}-private-rt-${count.index + 1}"
    Environment = var.environment
  }
}

# Route Table Associations
resource "aws_route_table_association" "public" {
  count          = length(var.availability_zones)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count          = length(var.availability_zones)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# Security Groups
resource "aws_security_group" "alb" {
  name        = "takeoff-${var.environment}-alb-sg"
  description = "Security group for ALB"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "takeoff-${var.environment}-alb-sg"
    Environment = var.environment
  }
}

resource "aws_security_group" "ecs" {
  name        = "takeoff-${var.environment}-ecs-sg"
  description = "Security group for ECS tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 0
    to_port         = 65535
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "takeoff-${var.environment}-ecs-sg"
    Environment = var.environment
  }
}

resource "aws_security_group" "database" {
  name        = "takeoff-${var.environment}-db-sg"
  description = "Security group for RDS"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }

  tags = {
    Name        = "takeoff-${var.environment}-db-sg"
    Environment = var.environment
  }
}

resource "aws_security_group" "redis" {
  name        = "takeoff-${var.environment}-redis-sg"
  description = "Security group for ElastiCache Redis"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }

  tags = {
    Name        = "takeoff-${var.environment}-redis-sg"
    Environment = var.environment
  }
}

# Outputs
output "vpc_id" {
  value = aws_vpc.main.id
}

output "public_subnet_ids" {
  value = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  value = aws_subnet.private[*].id
}

output "alb_security_group_id" {
  value = aws_security_group.alb.id
}

output "ecs_security_group_id" {
  value = aws_security_group.ecs.id
}

output "database_security_group_id" {
  value = aws_security_group.database.id
}

output "redis_security_group_id" {
  value = aws_security_group.redis.id
}
```

Create `infrastructure/terraform/modules/database/main.tf`:

```hcl
# RDS PostgreSQL Module

variable "environment" {
  type        = string
  description = "Environment name"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID"
}

variable "subnet_ids" {
  type        = list(string)
  description = "Subnet IDs for DB subnet group"
}

variable "security_group_id" {
  type        = string
  description = "Security group ID for RDS"
}

variable "instance_class" {
  type        = string
  default     = "db.r6g.large"
  description = "RDS instance class"
}

variable "allocated_storage" {
  type        = number
  default     = 100
  description = "Allocated storage in GB"
}

variable "max_allocated_storage" {
  type        = number
  default     = 500
  description = "Maximum storage for autoscaling in GB"
}

variable "database_name" {
  type        = string
  default     = "takeoff"
  description = "Database name"
}

variable "master_username" {
  type        = string
  default     = "takeoff_admin"
  description = "Master username"
}

# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "takeoff-${var.environment}-db-subnet"
  subnet_ids = var.subnet_ids

  tags = {
    Name        = "takeoff-${var.environment}-db-subnet"
    Environment = var.environment
  }
}

# Random password for master user
resource "random_password" "master" {
  length  = 32
  special = false
}

# Store password in Secrets Manager
resource "aws_secretsmanager_secret" "db_password" {
  name                    = "takeoff-${var.environment}-db-password"
  recovery_window_in_days = 7

  tags = {
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id = aws_secretsmanager_secret.db_password.id
  secret_string = jsonencode({
    username = var.master_username
    password = random_password.master.result
    host     = aws_db_instance.main.endpoint
    port     = 5432
    database = var.database_name
  })
}

# Parameter Group
resource "aws_db_parameter_group" "main" {
  name   = "takeoff-${var.environment}-pg15"
  family = "postgres15"

  parameter {
    name  = "log_statement"
    value = "ddl"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"  # Log queries taking > 1 second
  }

  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"
  }

  parameter {
    name  = "pg_stat_statements.track"
    value = "all"
  }

  tags = {
    Environment = var.environment
  }
}

# RDS Instance
resource "aws_db_instance" "main" {
  identifier = "takeoff-${var.environment}"

  engine               = "postgres"
  engine_version       = "15.4"
  instance_class       = var.instance_class
  allocated_storage    = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type         = "gp3"
  storage_encrypted    = true

  db_name  = var.database_name
  username = var.master_username
  password = random_password.master.result

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [var.security_group_id]
  parameter_group_name   = aws_db_parameter_group.main.name

  multi_az               = var.environment == "production"
  publicly_accessible    = false
  deletion_protection    = var.environment == "production"
  skip_final_snapshot    = var.environment != "production"
  final_snapshot_identifier = var.environment == "production" ? "takeoff-${var.environment}-final" : null

  backup_retention_period = var.environment == "production" ? 30 : 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "Mon:04:00-Mon:05:00"

  performance_insights_enabled          = true
  performance_insights_retention_period = 7

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  tags = {
    Name        = "takeoff-${var.environment}"
    Environment = var.environment
  }
}

# Read Replica (Production only)
resource "aws_db_instance" "replica" {
  count = var.environment == "production" ? 1 : 0

  identifier          = "takeoff-${var.environment}-replica"
  replicate_source_db = aws_db_instance.main.identifier

  instance_class    = var.instance_class
  storage_encrypted = true

  vpc_security_group_ids = [var.security_group_id]
  parameter_group_name   = aws_db_parameter_group.main.name

  publicly_accessible = false
  multi_az            = false

  performance_insights_enabled          = true
  performance_insights_retention_period = 7

  tags = {
    Name        = "takeoff-${var.environment}-replica"
    Environment = var.environment
  }
}

# Outputs
output "endpoint" {
  value = aws_db_instance.main.endpoint
}

output "replica_endpoint" {
  value = var.environment == "production" ? aws_db_instance.replica[0].endpoint : null
}

output "database_name" {
  value = var.database_name
}

output "secret_arn" {
  value = aws_secretsmanager_secret.db_password.arn
}
```

### Task 12.5: ECS Cluster and Services

Create `infrastructure/terraform/modules/compute/main.tf`:

```hcl
# ECS Cluster and Services Module

variable "environment" {
  type        = string
  description = "Environment name"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID"
}

variable "public_subnet_ids" {
  type        = list(string)
  description = "Public subnet IDs for ALB"
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "Private subnet IDs for ECS tasks"
}

variable "alb_security_group_id" {
  type        = string
  description = "ALB security group ID"
}

variable "ecs_security_group_id" {
  type        = string
  description = "ECS security group ID"
}

variable "api_image" {
  type        = string
  description = "API Docker image URI"
}

variable "worker_image" {
  type        = string
  description = "Worker Docker image URI"
}

variable "frontend_image" {
  type        = string
  description = "Frontend Docker image URI"
}

variable "api_cpu" {
  type        = number
  default     = 1024
  description = "API task CPU units"
}

variable "api_memory" {
  type        = number
  default     = 2048
  description = "API task memory in MB"
}

variable "api_desired_count" {
  type        = number
  default     = 3
  description = "Desired number of API tasks"
}

variable "worker_cpu" {
  type        = number
  default     = 2048
  description = "Worker task CPU units"
}

variable "worker_memory" {
  type        = number
  default     = 4096
  description = "Worker task memory in MB"
}

variable "worker_desired_count" {
  type        = number
  default     = 5
  description = "Desired number of worker tasks"
}

variable "environment_variables" {
  type        = map(string)
  description = "Environment variables for ECS tasks"
  default     = {}
}

variable "secrets" {
  type        = map(string)
  description = "Secret ARNs for ECS tasks"
  default     = {}
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "takeoff-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  configuration {
    execute_command_configuration {
      logging = "OVERRIDE"
      log_configuration {
        cloud_watch_log_group_name = aws_cloudwatch_log_group.ecs_exec.name
      }
    }
  }

  tags = {
    Environment = var.environment
  }
}

resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name = aws_ecs_cluster.main.name

  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    base              = 1
    weight            = 100
    capacity_provider = "FARGATE"
  }
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "ecs_exec" {
  name              = "/ecs/${var.environment}/exec"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${var.environment}/api"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/ecs/${var.environment}/worker"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/ecs/${var.environment}/frontend"
  retention_in_days = 30
}

# IAM Role for ECS Tasks
resource "aws_iam_role" "ecs_task_execution" {
  name = "takeoff-${var.environment}-ecs-task-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "ecs_task_execution_secrets" {
  name = "secrets-access"
  role = aws_iam_role.ecs_task_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = values(var.secrets)
      }
    ]
  })
}

resource "aws_iam_role" "ecs_task" {
  name = "takeoff-${var.environment}-ecs-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "ecs_task_s3" {
  name = "s3-access"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::takeoff-${var.environment}-*",
          "arn:aws:s3:::takeoff-${var.environment}-*/*"
        ]
      }
    ]
  })
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "takeoff-${var.environment}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.alb_security_group_id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = var.environment == "production"

  tags = {
    Environment = var.environment
  }
}

resource "aws_lb_target_group" "api" {
  name        = "takeoff-${var.environment}-api"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 3
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 10
    unhealthy_threshold = 3
  }

  tags = {
    Environment = var.environment
  }
}

resource "aws_lb_target_group" "frontend" {
  name        = "takeoff-${var.environment}-frontend"
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = {
    Environment = var.environment
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }
}

resource "aws_lb_listener_rule" "api" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }

  condition {
    path_pattern {
      values = ["/api/*", "/health", "/metrics"]
    }
  }
}

resource "aws_lb_listener" "http_redirect" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# ECS Task Definition - API
resource "aws_ecs_task_definition" "api" {
  family                   = "takeoff-${var.environment}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.api_cpu
  memory                   = var.api_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = var.api_image
      essential = true

      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        for key, value in var.environment_variables : {
          name  = key
          value = value
        }
      ]

      secrets = [
        for key, arn in var.secrets : {
          name      = key
          valueFrom = arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.api.name
          awslogs-region        = data.aws_region.current.name
          awslogs-stream-prefix = "api"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
        interval    = 30
        timeout     = 10
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = {
    Environment = var.environment
  }
}

# ECS Service - API
resource "aws_ecs_service" "api" {
  name            = "api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.api_desired_count

  capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight            = 100
    base              = 1
  }

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_security_group_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8000
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 100
  }

  enable_execute_command = true

  tags = {
    Environment = var.environment
  }
}

# Auto Scaling for API
resource "aws_appautoscaling_target" "api" {
  max_capacity       = 10
  min_capacity       = var.api_desired_count
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.api.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "api_cpu" {
  name               = "api-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.api.resource_id
  scalable_dimension = aws_appautoscaling_target.api.scalable_dimension
  service_namespace  = aws_appautoscaling_target.api.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}

resource "aws_appautoscaling_policy" "api_memory" {
  name               = "api-memory-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.api.resource_id
  scalable_dimension = aws_appautoscaling_target.api.scalable_dimension
  service_namespace  = aws_appautoscaling_target.api.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = 80.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
  }
}

# Worker Task Definition and Service (similar pattern)
resource "aws_ecs_task_definition" "worker" {
  family                   = "takeoff-${var.environment}-worker"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.worker_cpu
  memory                   = var.worker_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "worker"
      image     = var.worker_image
      essential = true

      environment = [
        for key, value in var.environment_variables : {
          name  = key
          value = value
        }
      ]

      secrets = [
        for key, arn in var.secrets : {
          name      = key
          valueFrom = arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.worker.name
          awslogs-region        = data.aws_region.current.name
          awslogs-stream-prefix = "worker"
        }
      }
    }
  ])

  tags = {
    Environment = var.environment
  }
}

resource "aws_ecs_service" "worker" {
  name            = "worker"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = var.worker_desired_count

  capacity_provider_strategy {
    capacity_provider = "FARGATE_SPOT"
    weight            = 100
  }

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_security_group_id]
    assign_public_ip = false
  }

  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 50  # Workers can have more aggressive rollout
  }

  enable_execute_command = true

  tags = {
    Environment = var.environment
  }
}

# Auto Scaling for Workers based on queue depth
resource "aws_appautoscaling_target" "worker" {
  max_capacity       = 20
  min_capacity       = var.worker_desired_count
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.worker.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

data "aws_region" "current" {}

variable "certificate_arn" {
  type        = string
  description = "ACM certificate ARN for HTTPS"
}

# Outputs
output "cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "alb_dns_name" {
  value = aws_lb.main.dns_name
}

output "alb_zone_id" {
  value = aws_lb.main.zone_id
}

output "api_service_name" {
  value = aws_ecs_service.api.name
}

output "worker_service_name" {
  value = aws_ecs_service.worker.name
}
```

---

## CI/CD Pipeline

### Task 12.6: GitHub Actions Workflow

Create `.github/workflows/deploy-prod.yml`:

```yaml
name: Deploy to Production

on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to deploy (e.g., v1.2.3)'
        required: true
        type: string
      skip_tests:
        description: 'Skip test suite (use with caution)'
        required: false
        type: boolean
        default: false

env:
  AWS_REGION: us-east-1
  ECR_REGISTRY: ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.us-east-1.amazonaws.com
  ECS_CLUSTER: takeoff-production

permissions:
  id-token: write
  contents: read
  packages: write

jobs:
  validate:
    name: Validate Deployment
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.validate.outputs.version }}
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          ref: ${{ inputs.version }}
          fetch-depth: 0

      - name: Validate version
        id: validate
        run: |
          if ! git tag -l "${{ inputs.version }}" | grep -q .; then
            echo "Error: Tag ${{ inputs.version }} does not exist"
            exit 1
          fi
          echo "version=${{ inputs.version }}" >> $GITHUB_OUTPUT

  test:
    name: Run Tests
    needs: validate
    runs-on: ubuntu-latest
    if: ${{ !inputs.skip_tests }}
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: takeoff_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          ref: ${{ needs.validate.outputs.version }}

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt -r requirements-dev.txt

      - name: Run tests
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/takeoff_test
          REDIS_URL: redis://localhost:6379/0
        run: |
          cd backend
          pytest tests/ -v --tb=short --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: backend/coverage.xml

  build:
    name: Build and Push Images
    needs: [validate, test]
    if: always() && needs.validate.result == 'success' && (needs.test.result == 'success' || needs.test.result == 'skipped')
    runs-on: ubuntu-latest
    strategy:
      matrix:
        component: [api, worker, frontend]
    outputs:
      api_image: ${{ steps.build.outputs.api_image }}
      worker_image: ${{ steps.build.outputs.worker_image }}
      frontend_image: ${{ steps.build.outputs.frontend_image }}

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          ref: ${{ needs.validate.outputs.version }}

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_DEPLOY_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build and push
        id: build
        uses: docker/build-push-action@v5
        with:
          context: .
          file: docker/Dockerfile.${{ matrix.component }}
          push: true
          tags: |
            ${{ env.ECR_REGISTRY }}/takeoff-${{ matrix.component }}:${{ needs.validate.outputs.version }}
            ${{ env.ECR_REGISTRY }}/takeoff-${{ matrix.component }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
          build-args: |
            VITE_API_URL=${{ secrets.PRODUCTION_API_URL }}
            VITE_APP_VERSION=${{ needs.validate.outputs.version }}

      - name: Output image URI
        run: |
          echo "${{ matrix.component }}_image=${{ env.ECR_REGISTRY }}/takeoff-${{ matrix.component }}:${{ needs.validate.outputs.version }}" >> $GITHUB_OUTPUT

  deploy:
    name: Deploy to Production
    needs: [validate, build]
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://app.takeoff.example.com

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          ref: ${{ needs.validate.outputs.version }}

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_DEPLOY_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Run database migrations
        run: |
          aws ecs run-task \
            --cluster ${{ env.ECS_CLUSTER }} \
            --task-definition takeoff-production-migrations \
            --launch-type FARGATE \
            --network-configuration "awsvpcConfiguration={subnets=[${{ secrets.PRIVATE_SUBNET_IDS }}],securityGroups=[${{ secrets.ECS_SECURITY_GROUP }}],assignPublicIp=DISABLED}" \
            --overrides '{"containerOverrides":[{"name":"migrations","command":["alembic","upgrade","head"]}]}' \
            --query 'tasks[0].taskArn' \
            --output text > /tmp/task_arn.txt

          # Wait for migration to complete
          aws ecs wait tasks-stopped \
            --cluster ${{ env.ECS_CLUSTER }} \
            --tasks $(cat /tmp/task_arn.txt)

          # Check exit code
          EXIT_CODE=$(aws ecs describe-tasks \
            --cluster ${{ env.ECS_CLUSTER }} \
            --tasks $(cat /tmp/task_arn.txt) \
            --query 'tasks[0].containers[0].exitCode' \
            --output text)

          if [ "$EXIT_CODE" != "0" ]; then
            echo "Migration failed with exit code: $EXIT_CODE"
            exit 1
          fi

      - name: Deploy API service
        run: |
          aws ecs update-service \
            --cluster ${{ env.ECS_CLUSTER }} \
            --service api \
            --force-new-deployment \
            --task-definition takeoff-production-api

      - name: Deploy Worker service
        run: |
          aws ecs update-service \
            --cluster ${{ env.ECS_CLUSTER }} \
            --service worker \
            --force-new-deployment \
            --task-definition takeoff-production-worker

      - name: Wait for API deployment
        run: |
          aws ecs wait services-stable \
            --cluster ${{ env.ECS_CLUSTER }} \
            --services api

      - name: Wait for Worker deployment
        run: |
          aws ecs wait services-stable \
            --cluster ${{ env.ECS_CLUSTER }} \
            --services worker

      - name: Invalidate CloudFront cache
        run: |
          aws cloudfront create-invalidation \
            --distribution-id ${{ secrets.CLOUDFRONT_DISTRIBUTION_ID }} \
            --paths "/*"

      - name: Run smoke tests
        run: |
          # Wait for services to be fully healthy
          sleep 30

          # Health check
          HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://api.takeoff.example.com/health)
          if [ "$HTTP_CODE" != "200" ]; then
            echo "Health check failed with status: $HTTP_CODE"
            exit 1
          fi

          # Version check
          VERSION=$(curl -s https://api.takeoff.example.com/health | jq -r '.version')
          if [ "$VERSION" != "${{ needs.validate.outputs.version }}" ]; then
            echo "Version mismatch: expected ${{ needs.validate.outputs.version }}, got $VERSION"
            exit 1
          fi

          echo "Smoke tests passed!"

  notify:
    name: Notify Deployment
    needs: [validate, deploy]
    runs-on: ubuntu-latest
    if: always()

    steps:
      - name: Notify Slack on success
        if: needs.deploy.result == 'success'
        uses: slackapi/slack-github-action@v1.26.0
        with:
          payload: |
            {
              "text": "✅ Production deployment successful",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*✅ Production Deployment Successful*\n\n*Version:* `${{ needs.validate.outputs.version }}`\n*Deployed by:* ${{ github.actor }}\n*URL:* https://app.takeoff.example.com"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
          SLACK_WEBHOOK_TYPE: INCOMING_WEBHOOK

      - name: Notify Slack on failure
        if: needs.deploy.result == 'failure'
        uses: slackapi/slack-github-action@v1.26.0
        with:
          payload: |
            {
              "text": "❌ Production deployment failed",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*❌ Production Deployment Failed*\n\n*Version:* `${{ needs.validate.outputs.version }}`\n*Deployed by:* ${{ github.actor }}\n*Workflow:* <${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}|View Run>"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
          SLACK_WEBHOOK_TYPE: INCOMING_WEBHOOK
```

---

## Monitoring and Observability

### Task 12.7: Prometheus Configuration

Create `monitoring/prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    environment: production
    cluster: takeoff

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

rule_files:
  - /etc/prometheus/rules/*.yml
  - /etc/prometheus/alerts/*.yml

scrape_configs:
  # Prometheus self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # API service metrics
  - job_name: 'api'
    metrics_path: /metrics
    dns_sd_configs:
      - names:
          - 'tasks.api'
        type: 'A'
        port: 8000
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
        regex: '(.+):8000'
        replacement: '${1}'

  # Worker metrics via Redis exporter
  - job_name: 'celery'
    static_configs:
      - targets: ['celery-exporter:9808']

  # PostgreSQL metrics
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  # Redis metrics
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  # Nginx metrics
  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']

  # Node exporter for infrastructure metrics
  - job_name: 'node'
    ec2_sd_configs:
      - region: us-east-1
        port: 9100
        filters:
          - name: tag:Environment
            values: ['production']
    relabel_configs:
      - source_labels: [__meta_ec2_tag_Name]
        target_label: instance
      - source_labels: [__meta_ec2_instance_type]
        target_label: instance_type
```

Create `monitoring/prometheus/alerts/api-alerts.yml`:

```yaml
groups:
  - name: api_alerts
    rules:
      # High error rate
      - alert: APIHighErrorRate
        expr: |
          (
            sum(rate(http_requests_total{job="api", status=~"5.."}[5m]))
            /
            sum(rate(http_requests_total{job="api"}[5m]))
          ) > 0.05
        for: 5m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: "High API error rate"
          description: "API error rate is {{ $value | humanizePercentage }} over the last 5 minutes"

      # High latency
      - alert: APIHighLatency
        expr: |
          histogram_quantile(0.95, 
            sum(rate(http_request_duration_seconds_bucket{job="api"}[5m])) by (le, endpoint)
          ) > 2
        for: 5m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: "High API latency"
          description: "95th percentile latency for {{ $labels.endpoint }} is {{ $value | humanizeDuration }}"

      # Service down
      - alert: APIServiceDown
        expr: up{job="api"} == 0
        for: 1m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: "API service is down"
          description: "API instance {{ $labels.instance }} is not responding"

      # High memory usage
      - alert: APIHighMemoryUsage
        expr: |
          (
            container_memory_usage_bytes{container_name="api"}
            /
            container_spec_memory_limit_bytes{container_name="api"}
          ) > 0.85
        for: 5m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: "High memory usage in API container"
          description: "API container is using {{ $value | humanizePercentage }} of memory limit"

      # Database connection pool exhaustion
      - alert: DatabaseConnectionPoolExhausted
        expr: |
          (
            pg_stat_activity_count{datname="takeoff"}
            /
            pg_settings_max_connections
          ) > 0.9
        for: 2m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: "Database connection pool nearly exhausted"
          description: "{{ $value | humanizePercentage }} of database connections are in use"

  - name: worker_alerts
    rules:
      # Queue backlog
      - alert: CeleryQueueBacklog
        expr: celery_queue_length > 1000
        for: 10m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: "High Celery queue backlog"
          description: "Queue {{ $labels.queue_name }} has {{ $value }} pending tasks"

      # Worker failures
      - alert: CeleryTaskFailureRate
        expr: |
          (
            sum(rate(celery_task_failed_total[5m])) by (task_name)
            /
            sum(rate(celery_task_succeeded_total[5m]) + rate(celery_task_failed_total[5m])) by (task_name)
          ) > 0.1
        for: 5m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: "High Celery task failure rate"
          description: "Task {{ $labels.task_name }} has {{ $value | humanizePercentage }} failure rate"

      # No active workers
      - alert: NoActiveCeleryWorkers
        expr: celery_workers == 0
        for: 2m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: "No active Celery workers"
          description: "All Celery workers are down"

  - name: ai_alerts
    rules:
      # AI API rate limiting
      - alert: AIAPIRateLimited
        expr: |
          sum(rate(ai_api_requests_total{status="rate_limited"}[5m])) > 0
        for: 1m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: "AI API rate limited"
          description: "Anthropic API requests are being rate limited"

      # AI accuracy degradation
      - alert: AIAccuracyDegraded
        expr: |
          avg_over_time(ai_takeoff_accuracy_score[1h]) < 0.70
        for: 30m
        labels:
          severity: warning
          team: ml
        annotations:
          summary: "AI takeoff accuracy degraded"
          description: "AI accuracy is {{ $value | humanizePercentage }}, below 70% threshold"

      # High AI latency
      - alert: AIHighLatency
        expr: |
          histogram_quantile(0.95, 
            sum(rate(ai_request_duration_seconds_bucket[5m])) by (le)
          ) > 30
        for: 5m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: "High AI request latency"
          description: "95th percentile AI request latency is {{ $value | humanizeDuration }}"
```

### Task 12.8: Grafana Dashboards

Create `monitoring/grafana/provisioning/dashboards/api-dashboard.json`:

```json
{
  "annotations": {
    "list": [
      {
        "builtIn": 1,
        "datasource": "-- Grafana --",
        "enable": true,
        "hide": true,
        "iconColor": "rgba(0, 211, 255, 1)",
        "name": "Annotations & Alerts",
        "type": "dashboard"
      },
      {
        "datasource": "Prometheus",
        "enable": true,
        "expr": "changes(process_start_time_seconds{job=\"api\"}[1m]) > 0",
        "iconColor": "orange",
        "name": "Deployments",
        "tagKeys": "version",
        "titleFormat": "Deployment"
      }
    ]
  },
  "title": "API Service Dashboard",
  "uid": "api-service",
  "version": 1,
  "panels": [
    {
      "title": "Request Rate",
      "type": "timeseries",
      "gridPos": { "h": 8, "w": 12, "x": 0, "y": 0 },
      "targets": [
        {
          "expr": "sum(rate(http_requests_total{job=\"api\"}[5m])) by (method)",
          "legendFormat": "{{ method }}"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "reqps"
        }
      }
    },
    {
      "title": "Error Rate",
      "type": "timeseries",
      "gridPos": { "h": 8, "w": 12, "x": 12, "y": 0 },
      "targets": [
        {
          "expr": "sum(rate(http_requests_total{job=\"api\", status=~\"5..\"}[5m])) / sum(rate(http_requests_total{job=\"api\"}[5m])) * 100",
          "legendFormat": "Error Rate %"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "percent",
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "green", "value": null },
              { "color": "yellow", "value": 1 },
              { "color": "red", "value": 5 }
            ]
          }
        }
      }
    },
    {
      "title": "Response Time (p95)",
      "type": "timeseries",
      "gridPos": { "h": 8, "w": 12, "x": 0, "y": 8 },
      "targets": [
        {
          "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{job=\"api\"}[5m])) by (le, endpoint))",
          "legendFormat": "{{ endpoint }}"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "s"
        }
      }
    },
    {
      "title": "Active Connections",
      "type": "stat",
      "gridPos": { "h": 4, "w": 6, "x": 12, "y": 8 },
      "targets": [
        {
          "expr": "sum(http_active_connections{job=\"api\"})"
        }
      ]
    },
    {
      "title": "Request Rate by Endpoint",
      "type": "table",
      "gridPos": { "h": 8, "w": 12, "x": 12, "y": 12 },
      "targets": [
        {
          "expr": "topk(10, sum(rate(http_requests_total{job=\"api\"}[5m])) by (endpoint))",
          "format": "table",
          "instant": true
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "reqps"
        }
      },
      "transformations": [
        {
          "id": "organize",
          "options": {
            "excludeByName": { "Time": true },
            "renameByName": {
              "endpoint": "Endpoint",
              "Value": "Requests/s"
            }
          }
        }
      ]
    },
    {
      "title": "Memory Usage",
      "type": "timeseries",
      "gridPos": { "h": 8, "w": 12, "x": 0, "y": 16 },
      "targets": [
        {
          "expr": "sum(container_memory_usage_bytes{container_name=\"api\"}) by (instance)",
          "legendFormat": "{{ instance }}"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "bytes"
        }
      }
    },
    {
      "title": "CPU Usage",
      "type": "timeseries",
      "gridPos": { "h": 8, "w": 12, "x": 12, "y": 16 },
      "targets": [
        {
          "expr": "sum(rate(container_cpu_usage_seconds_total{container_name=\"api\"}[5m])) by (instance) * 100",
          "legendFormat": "{{ instance }}"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "percent"
        }
      }
    }
  ],
  "time": {
    "from": "now-3h",
    "to": "now"
  },
  "refresh": "30s"
}
```

Create `monitoring/grafana/provisioning/dashboards/ai-accuracy-dashboard.json`:

```json
{
  "title": "AI Takeoff Accuracy Dashboard",
  "uid": "ai-accuracy",
  "version": 1,
  "panels": [
    {
      "title": "Overall Accuracy Score",
      "type": "gauge",
      "gridPos": { "h": 8, "w": 8, "x": 0, "y": 0 },
      "targets": [
        {
          "expr": "avg(ai_takeoff_accuracy_score)"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "percentunit",
          "min": 0,
          "max": 1,
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "red", "value": null },
              { "color": "yellow", "value": 0.65 },
              { "color": "green", "value": 0.75 }
            ]
          }
        }
      },
      "options": {
        "showThresholdLabels": true,
        "showThresholdMarkers": true
      }
    },
    {
      "title": "Accuracy by Plan Type",
      "type": "barchart",
      "gridPos": { "h": 8, "w": 16, "x": 8, "y": 0 },
      "targets": [
        {
          "expr": "avg(ai_takeoff_accuracy_score) by (plan_type)",
          "legendFormat": "{{ plan_type }}"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "percentunit"
        }
      }
    },
    {
      "title": "Accuracy Trend",
      "type": "timeseries",
      "gridPos": { "h": 8, "w": 24, "x": 0, "y": 8 },
      "targets": [
        {
          "expr": "avg(ai_takeoff_accuracy_score)",
          "legendFormat": "Overall"
        },
        {
          "expr": "avg(ai_scale_detection_accuracy)",
          "legendFormat": "Scale Detection"
        },
        {
          "expr": "avg(ai_element_detection_accuracy)",
          "legendFormat": "Element Detection"
        },
        {
          "expr": "avg(ai_measurement_accuracy)",
          "legendFormat": "Measurement"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "percentunit"
        }
      }
    },
    {
      "title": "Human Override Rate",
      "type": "timeseries",
      "gridPos": { "h": 8, "w": 12, "x": 0, "y": 16 },
      "targets": [
        {
          "expr": "sum(rate(ai_measurement_overridden_total[1h])) / sum(rate(ai_measurement_total[1h])) * 100",
          "legendFormat": "Override Rate %"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "percent"
        }
      }
    },
    {
      "title": "AI Processing Time",
      "type": "timeseries",
      "gridPos": { "h": 8, "w": 12, "x": 12, "y": 16 },
      "targets": [
        {
          "expr": "histogram_quantile(0.50, sum(rate(ai_processing_duration_seconds_bucket[5m])) by (le))",
          "legendFormat": "p50"
        },
        {
          "expr": "histogram_quantile(0.95, sum(rate(ai_processing_duration_seconds_bucket[5m])) by (le))",
          "legendFormat": "p95"
        },
        {
          "expr": "histogram_quantile(0.99, sum(rate(ai_processing_duration_seconds_bucket[5m])) by (le))",
          "legendFormat": "p99"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "s"
        }
      }
    },
    {
      "title": "Error Types Distribution",
      "type": "piechart",
      "gridPos": { "h": 8, "w": 12, "x": 0, "y": 24 },
      "targets": [
        {
          "expr": "sum(ai_error_total) by (error_type)",
          "legendFormat": "{{ error_type }}"
        }
      ]
    },
    {
      "title": "AI API Costs",
      "type": "stat",
      "gridPos": { "h": 4, "w": 6, "x": 12, "y": 24 },
      "targets": [
        {
          "expr": "sum(increase(ai_api_cost_total[24h]))"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "currencyUSD"
        }
      },
      "options": {
        "reduceOptions": {
          "calcs": ["lastNotNull"]
        }
      }
    },
    {
      "title": "Token Usage (24h)",
      "type": "stat",
      "gridPos": { "h": 4, "w": 6, "x": 18, "y": 24 },
      "targets": [
        {
          "expr": "sum(increase(ai_tokens_total[24h]))"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "short"
        }
      }
    }
  ],
  "time": {
    "from": "now-24h",
    "to": "now"
  },
  "refresh": "5m"
}
```

---

## Backup and Disaster Recovery

### Task 12.9: Backup Scripts

Create `infrastructure/scripts/backup-db.sh`:

```bash
#!/bin/bash
set -euo pipefail

# Configuration
ENVIRONMENT="${ENVIRONMENT:-production}"
AWS_REGION="${AWS_REGION:-us-east-1}"
BACKUP_BUCKET="takeoff-${ENVIRONMENT}-backups"
RETENTION_DAYS=30
DATE=$(date +%Y-%m-%d-%H%M%S)
BACKUP_FILE="db-backup-${DATE}.sql.gz"

# Get database credentials from Secrets Manager
echo "Fetching database credentials..."
SECRET_JSON=$(aws secretsmanager get-secret-value \
    --secret-id "takeoff-${ENVIRONMENT}-db-password" \
    --region "${AWS_REGION}" \
    --query 'SecretString' \
    --output text)

DB_HOST=$(echo "$SECRET_JSON" | jq -r '.host' | cut -d':' -f1)
DB_PORT=$(echo "$SECRET_JSON" | jq -r '.port')
DB_NAME=$(echo "$SECRET_JSON" | jq -r '.database')
DB_USER=$(echo "$SECRET_JSON" | jq -r '.username')
DB_PASSWORD=$(echo "$SECRET_JSON" | jq -r '.password')

# Export password for pg_dump
export PGPASSWORD="${DB_PASSWORD}"

# Create backup
echo "Creating database backup..."
pg_dump \
    --host="${DB_HOST}" \
    --port="${DB_PORT}" \
    --username="${DB_USER}" \
    --dbname="${DB_NAME}" \
    --format=plain \
    --no-owner \
    --no-privileges \
    --verbose \
    2>&1 | gzip > "/tmp/${BACKUP_FILE}"

# Get backup size
BACKUP_SIZE=$(stat -f%z "/tmp/${BACKUP_FILE}" 2>/dev/null || stat -c%s "/tmp/${BACKUP_FILE}")
echo "Backup size: $(numfmt --to=iec-i --suffix=B ${BACKUP_SIZE})"

# Calculate checksum
CHECKSUM=$(sha256sum "/tmp/${BACKUP_FILE}" | cut -d' ' -f1)
echo "Backup checksum: ${CHECKSUM}"

# Upload to S3
echo "Uploading backup to S3..."
aws s3 cp "/tmp/${BACKUP_FILE}" "s3://${BACKUP_BUCKET}/database/${BACKUP_FILE}" \
    --metadata "checksum=${CHECKSUM},size=${BACKUP_SIZE}" \
    --storage-class STANDARD_IA

# Create latest symlink
aws s3 cp "s3://${BACKUP_BUCKET}/database/${BACKUP_FILE}" \
    "s3://${BACKUP_BUCKET}/database/latest.sql.gz"

# Cleanup local file
rm "/tmp/${BACKUP_FILE}"

# Delete old backups
echo "Cleaning up old backups..."
aws s3 ls "s3://${BACKUP_BUCKET}/database/" | \
    awk '{print $4}' | \
    grep -E '^db-backup-[0-9]{4}-[0-9]{2}-[0-9]{2}' | \
    sort | \
    head -n -${RETENTION_DAYS} | \
    xargs -I {} aws s3 rm "s3://${BACKUP_BUCKET}/database/{}" || true

# Verify backup
echo "Verifying backup..."
aws s3 head-object \
    --bucket "${BACKUP_BUCKET}" \
    --key "database/${BACKUP_FILE}" \
    --query 'ContentLength' \
    --output text > /dev/null

# Record backup metadata
echo "Recording backup metadata..."
aws dynamodb put-item \
    --table-name "takeoff-${ENVIRONMENT}-backup-metadata" \
    --item '{
        "backup_id": {"S": "'${DATE}'"},
        "type": {"S": "database"},
        "file": {"S": "'${BACKUP_FILE}'"},
        "size": {"N": "'${BACKUP_SIZE}'"},
        "checksum": {"S": "'${CHECKSUM}'"},
        "timestamp": {"S": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"},
        "retention_until": {"S": "'$(date -u -d "+${RETENTION_DAYS} days" +%Y-%m-%dT%H:%M:%SZ)'"} 
    }' || echo "Warning: Failed to record metadata to DynamoDB"

echo "Backup completed successfully: ${BACKUP_FILE}"

# Send notification
aws sns publish \
    --topic-arn "arn:aws:sns:${AWS_REGION}:${AWS_ACCOUNT_ID}:takeoff-${ENVIRONMENT}-alerts" \
    --subject "Database Backup Completed" \
    --message "Database backup completed successfully.

File: ${BACKUP_FILE}
Size: $(numfmt --to=iec-i --suffix=B ${BACKUP_SIZE})
Checksum: ${CHECKSUM}
Bucket: s3://${BACKUP_BUCKET}/database/" || true
```

Create `infrastructure/scripts/restore-db.sh`:

```bash
#!/bin/bash
set -euo pipefail

# Configuration
ENVIRONMENT="${ENVIRONMENT:-production}"
AWS_REGION="${AWS_REGION:-us-east-1}"
BACKUP_BUCKET="takeoff-${ENVIRONMENT}-backups"
BACKUP_FILE="${1:-latest.sql.gz}"

# Safety check for production
if [ "$ENVIRONMENT" == "production" ]; then
    echo "⚠️  WARNING: You are about to restore the PRODUCTION database!"
    echo "This will OVERWRITE all current data."
    read -p "Type 'RESTORE PRODUCTION' to confirm: " CONFIRM
    if [ "$CONFIRM" != "RESTORE PRODUCTION" ]; then
        echo "Restore cancelled."
        exit 1
    fi
fi

# Get database credentials from Secrets Manager
echo "Fetching database credentials..."
SECRET_JSON=$(aws secretsmanager get-secret-value \
    --secret-id "takeoff-${ENVIRONMENT}-db-password" \
    --region "${AWS_REGION}" \
    --query 'SecretString' \
    --output text)

DB_HOST=$(echo "$SECRET_JSON" | jq -r '.host' | cut -d':' -f1)
DB_PORT=$(echo "$SECRET_JSON" | jq -r '.port')
DB_NAME=$(echo "$SECRET_JSON" | jq -r '.database')
DB_USER=$(echo "$SECRET_JSON" | jq -r '.username')
DB_PASSWORD=$(echo "$SECRET_JSON" | jq -r '.password')

export PGPASSWORD="${DB_PASSWORD}"

# Download backup
echo "Downloading backup: ${BACKUP_FILE}..."
aws s3 cp "s3://${BACKUP_BUCKET}/database/${BACKUP_FILE}" "/tmp/${BACKUP_FILE}"

# Verify checksum if available
if [ "$BACKUP_FILE" != "latest.sql.gz" ]; then
    STORED_CHECKSUM=$(aws s3api head-object \
        --bucket "${BACKUP_BUCKET}" \
        --key "database/${BACKUP_FILE}" \
        --query 'Metadata.checksum' \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$STORED_CHECKSUM" ] && [ "$STORED_CHECKSUM" != "None" ]; then
        ACTUAL_CHECKSUM=$(sha256sum "/tmp/${BACKUP_FILE}" | cut -d' ' -f1)
        if [ "$STORED_CHECKSUM" != "$ACTUAL_CHECKSUM" ]; then
            echo "ERROR: Checksum mismatch!"
            echo "Expected: ${STORED_CHECKSUM}"
            echo "Actual: ${ACTUAL_CHECKSUM}"
            rm "/tmp/${BACKUP_FILE}"
            exit 1
        fi
        echo "Checksum verified."
    fi
fi

# Stop application services
echo "Stopping application services..."
aws ecs update-service \
    --cluster "takeoff-${ENVIRONMENT}" \
    --service api \
    --desired-count 0 \
    --no-cli-pager || true

aws ecs update-service \
    --cluster "takeoff-${ENVIRONMENT}" \
    --service worker \
    --desired-count 0 \
    --no-cli-pager || true

# Wait for services to stop
echo "Waiting for services to stop..."
sleep 30

# Terminate existing connections
echo "Terminating existing database connections..."
psql \
    --host="${DB_HOST}" \
    --port="${DB_PORT}" \
    --username="${DB_USER}" \
    --dbname="postgres" \
    --command="SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DB_NAME}' AND pid <> pg_backend_pid();" || true

# Drop and recreate database
echo "Recreating database..."
psql \
    --host="${DB_HOST}" \
    --port="${DB_PORT}" \
    --username="${DB_USER}" \
    --dbname="postgres" \
    --command="DROP DATABASE IF EXISTS ${DB_NAME};"

psql \
    --host="${DB_HOST}" \
    --port="${DB_PORT}" \
    --username="${DB_USER}" \
    --dbname="postgres" \
    --command="CREATE DATABASE ${DB_NAME};"

# Restore backup
echo "Restoring backup..."
gunzip -c "/tmp/${BACKUP_FILE}" | psql \
    --host="${DB_HOST}" \
    --port="${DB_PORT}" \
    --username="${DB_USER}" \
    --dbname="${DB_NAME}" \
    --single-transaction

# Cleanup
rm "/tmp/${BACKUP_FILE}"

# Run migrations to ensure schema is up to date
echo "Running database migrations..."
# This would typically be run via ECS task

# Restart application services
echo "Restarting application services..."
aws ecs update-service \
    --cluster "takeoff-${ENVIRONMENT}" \
    --service api \
    --desired-count 3 \
    --no-cli-pager

aws ecs update-service \
    --cluster "takeoff-${ENVIRONMENT}" \
    --service worker \
    --desired-count 5 \
    --no-cli-pager

echo "Database restore completed successfully!"

# Send notification
aws sns publish \
    --topic-arn "arn:aws:sns:${AWS_REGION}:${AWS_ACCOUNT_ID}:takeoff-${ENVIRONMENT}-alerts" \
    --subject "Database Restore Completed" \
    --message "Database restore completed successfully.

Backup file: ${BACKUP_FILE}
Environment: ${ENVIRONMENT}
Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)" || true
```

---

## Operational Runbooks

### Task 12.10: Incident Response Runbook

Create `docs/operations/runbooks/incident-response.md`:

```markdown
# Incident Response Runbook

## Severity Levels

| Severity | Description | Response Time | Examples |
|----------|-------------|---------------|----------|
| **P1** | Critical - Complete outage | 15 minutes | Site down, data loss, security breach |
| **P2** | High - Major feature broken | 30 minutes | API failures, payment issues |
| **P3** | Medium - Degraded performance | 2 hours | Slow responses, minor bugs |
| **P4** | Low - Minor issues | 24 hours | UI glitches, documentation |

## Incident Response Process

### 1. Detection & Alerting

Alerts are triggered via:
- Prometheus/Alertmanager (infrastructure)
- Application error tracking (Sentry)
- Uptime monitoring (external)
- User reports (support channels)

### 2. Initial Response

**On receiving an alert:**

1. **Acknowledge** the incident in PagerDuty/Slack
2. **Assess** severity level based on impact
3. **Communicate** status in #incidents channel
4. **Page** additional responders if needed

**Initial assessment checklist:**
- [ ] What service(s) are affected?
- [ ] How many users are impacted?
- [ ] When did the issue start?
- [ ] Were there recent deployments?
- [ ] Are there related alerts?

### 3. Investigation

**Quick diagnostic commands:**

```bash
# Check service health
aws ecs describe-services --cluster takeoff-production --services api worker

# View recent logs
aws logs tail /ecs/production/api --since 30m

# Check error rates
curl -s 'http://prometheus:9090/api/v1/query?query=sum(rate(http_requests_total{status=~"5.."}[5m]))'

# Check database connections
psql -c "SELECT count(*) FROM pg_stat_activity;"

# Check Redis queue depth
redis-cli LLEN celery
```

**Common investigation paths:**

| Symptom | Check First |
|---------|-------------|
| 5xx errors | API logs, database connectivity |
| High latency | Database queries, external APIs |
| Queue backlog | Worker health, task failures |
| Memory issues | Container metrics, memory leaks |

### 4. Mitigation

**Immediate actions by symptom:**

#### API Service Down
```bash
# Check deployment status
aws ecs describe-services --cluster takeoff-production --services api

# Force new deployment
aws ecs update-service --cluster takeoff-production --service api --force-new-deployment

# Scale up temporarily
aws ecs update-service --cluster takeoff-production --service api --desired-count 5
```

#### Database Issues
```bash
# Check connections
psql -c "SELECT * FROM pg_stat_activity WHERE state != 'idle';"

# Kill long-running queries (>5 minutes)
psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'active' AND query_start < now() - interval '5 minutes';"

# Failover to read replica (if available)
# Update DATABASE_URL to point to replica for read operations
```

#### Worker Backlog
```bash
# Scale up workers
aws ecs update-service --cluster takeoff-production --service worker --desired-count 10

# Purge specific queue (data loss warning!)
celery -A app.workers.celery_app purge -Q document_processing

# Restart workers
aws ecs update-service --cluster takeoff-production --service worker --force-new-deployment
```

### 5. Rollback Procedure

If the issue is related to a recent deployment:

```bash
# Get previous task definition
PREV_TASK=$(aws ecs describe-services --cluster takeoff-production --services api \
    --query 'services[0].deployments[1].taskDefinition' --output text)

# Rollback to previous version
aws ecs update-service --cluster takeoff-production --service api \
    --task-definition "$PREV_TASK"

# Monitor rollback
aws ecs wait services-stable --cluster takeoff-production --services api
```

### 6. Communication

**Status page updates:**

```bash
# Update status page (example with Statuspage.io API)
curl -X POST "https://api.statuspage.io/v1/pages/{page_id}/incidents" \
    -H "Authorization: OAuth {api_key}" \
    -d "incident[name]=API Service Degradation" \
    -d "incident[status]=investigating" \
    -d "incident[body]=We are investigating reports of API errors."
```

**Stakeholder communication template:**

```
Subject: [P{SEVERITY}] {BRIEF_DESCRIPTION}

Status: {Investigating|Identified|Monitoring|Resolved}

Impact: {Description of user impact}

Timeline:
- {HH:MM UTC} - Issue detected
- {HH:MM UTC} - {Action taken}

Current Actions: {What we're doing now}

Next Update: {Time} or when status changes
```

### 7. Resolution & Post-Incident

**After resolving:**

1. Confirm all metrics are normal
2. Update status page to "Resolved"
3. Notify stakeholders
4. Schedule post-incident review
5. Create follow-up tickets for improvements

**Post-incident review template:**

```markdown
## Incident Summary
- **Date/Time**: 
- **Duration**: 
- **Severity**: 
- **Services Affected**: 

## Timeline
(Detailed timeline of events)

## Root Cause
(Technical explanation of what went wrong)

## Resolution
(How the issue was fixed)

## Action Items
| Action | Owner | Due Date |
|--------|-------|----------|
| | | |

## Lessons Learned
(What went well, what could be improved)
```

---

## Emergency Contacts

| Role | Name | Phone | Slack |
|------|------|-------|-------|
| On-Call Primary | Rotating | PagerDuty | @oncall |
| Engineering Lead | TBD | xxx-xxx-xxxx | @eng-lead |
| Database Admin | TBD | xxx-xxx-xxxx | @dba |
| Security | TBD | xxx-xxx-xxxx | @security |

## External Contacts

| Service | Support | SLA |
|---------|---------|-----|
| AWS Support | AWS Console | Business/Enterprise |
| Anthropic API | api-support@anthropic.com | Best effort |
| CloudFlare | Dashboard | Enterprise |
```

### Task 12.11: Scaling Procedures Runbook

Create `docs/operations/runbooks/scaling-procedures.md`:

```markdown
# Scaling Procedures Runbook

## Auto-Scaling Configuration

The platform uses automatic scaling based on these metrics:

| Service | Metric | Target | Min | Max |
|---------|--------|--------|-----|-----|
| API | CPU Utilization | 70% | 3 | 10 |
| API | Memory Utilization | 80% | 3 | 10 |
| Workers | Queue Depth | 100 tasks | 5 | 20 |

## Manual Scaling Procedures

### Scale API Service

```bash
# Check current capacity
aws ecs describe-services --cluster takeoff-production --services api \
    --query 'services[0].{desired:desiredCount,running:runningCount,pending:pendingCount}'

# Scale to specific count
aws ecs update-service \
    --cluster takeoff-production \
    --service api \
    --desired-count 5

# Wait for scaling to complete
aws ecs wait services-stable --cluster takeoff-production --services api
```

### Scale Workers

```bash
# Check queue depth first
redis-cli LLEN celery

# Scale workers
aws ecs update-service \
    --cluster takeoff-production \
    --service worker \
    --desired-count 10

# Monitor scaling
watch -n 5 'aws ecs describe-services --cluster takeoff-production --services worker --query "services[0].{desired:desiredCount,running:runningCount}"'
```

### Scale Database

**Vertical scaling (instance size):**

```bash
# Note: This causes downtime!
aws rds modify-db-instance \
    --db-instance-identifier takeoff-production \
    --db-instance-class db.r6g.xlarge \
    --apply-immediately

# Monitor progress
aws rds describe-db-instances \
    --db-instance-identifier takeoff-production \
    --query 'DBInstances[0].DBInstanceStatus'
```

**Horizontal scaling (read replicas):**

```bash
# Create read replica
aws rds create-db-instance-read-replica \
    --db-instance-identifier takeoff-production-replica-2 \
    --source-db-instance-identifier takeoff-production \
    --db-instance-class db.r6g.large
```

### Scale Redis

```bash
# Increase node type (causes failover)
aws elasticache modify-replication-group \
    --replication-group-id takeoff-production-redis \
    --cache-node-type cache.r6g.large \
    --apply-immediately

# Add read replicas
aws elasticache increase-replica-count \
    --replication-group-id takeoff-production-redis \
    --new-replica-count 2 \
    --apply-immediately
```

## Capacity Planning

### Current Baseline

| Resource | Current | Utilization | Headroom |
|----------|---------|-------------|----------|
| API instances | 3 | 45% CPU | 55% |
| Workers | 5 | 60% CPU | 40% |
| Database | db.r6g.large | 35% CPU | 65% |
| Redis | cache.r6g.medium | 20% memory | 80% |

### Growth Projections

| Metric | Current | +3 months | +6 months |
|--------|---------|-----------|-----------|
| Daily uploads | 100 | 250 | 500 |
| Concurrent users | 50 | 125 | 250 |
| Storage (TB) | 2 | 5 | 12 |

### Scaling Thresholds

**Proactive scaling triggers:**

- API: >60% CPU sustained for 15 minutes
- Workers: Queue depth >500 for 10 minutes
- Database: >70% CPU or connections >80%
- Storage: >80% capacity

## Load Testing

Before major releases or expected traffic increases:

```bash
# Run load test (staging only!)
locust -f tests/performance/locustfile.py \
    --host=https://staging.takeoff.example.com \
    --users=100 \
    --spawn-rate=10 \
    --run-time=30m
```

## Cost Optimization

### Spot Instances for Workers

Workers use FARGATE_SPOT for cost savings:
- 70% cost reduction vs on-demand
- Acceptable for background processing
- Auto-replacement on interruption

### Reserved Capacity

Consider reserved capacity for:
- Database (1-year minimum)
- Baseline API instances
- Redis cluster

### Right-Sizing

Review monthly:
```bash
# Get recommendations
aws compute-optimizer get-ec2-instance-recommendations
aws compute-optimizer get-ecs-service-recommendations
```
```

---

## Security Hardening

### Task 12.12: Security Configuration

Create `infrastructure/terraform/modules/security/main.tf`:

```hcl
# Security Module

variable "environment" {
  type = string
}

variable "vpc_id" {
  type = string
}

# WAF Web ACL
resource "aws_wafv2_web_acl" "main" {
  name        = "takeoff-${var.environment}-waf"
  description = "WAF rules for takeoff platform"
  scope       = "REGIONAL"

  default_action {
    allow {}
  }

  # Rate limiting
  rule {
    name     = "RateLimit"
    priority = 1

    override_action {
      none {}
    }

    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRule"
      sampled_requests_enabled   = true
    }
  }

  # AWS Managed Rules - Common Rule Set
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"

        rule_action_override {
          action_to_use {
            count {}
          }
          name = "SizeRestrictions_BODY"  # Allow large file uploads
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesCommonRuleSet"
      sampled_requests_enabled   = true
    }
  }

  # AWS Managed Rules - SQL Injection
  rule {
    name     = "AWSManagedRulesSQLiRuleSet"
    priority = 3

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesSQLiRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesSQLiRuleSet"
      sampled_requests_enabled   = true
    }
  }

  # Block known bad inputs
  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 4

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesKnownBadInputsRuleSet"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "takeoff-${var.environment}-waf"
    sampled_requests_enabled   = true
  }

  tags = {
    Environment = var.environment
  }
}

# KMS Key for encryption
resource "aws_kms_key" "main" {
  description             = "KMS key for takeoff ${var.environment}"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow ECS to use the key"
        Effect = "Allow"
        Principal = {
          Service = "ecs.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = "*"
      }
    ]
  })

  tags = {
    Environment = var.environment
  }
}

resource "aws_kms_alias" "main" {
  name          = "alias/takeoff-${var.environment}"
  target_key_id = aws_kms_key.main.key_id
}

# VPC Flow Logs
resource "aws_flow_log" "main" {
  vpc_id                   = var.vpc_id
  traffic_type             = "ALL"
  log_destination_type     = "cloud-watch-logs"
  log_destination          = aws_cloudwatch_log_group.flow_logs.arn
  iam_role_arn             = aws_iam_role.flow_logs.arn
  max_aggregation_interval = 60

  tags = {
    Name        = "takeoff-${var.environment}-flow-logs"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "flow_logs" {
  name              = "/vpc/takeoff-${var.environment}/flow-logs"
  retention_in_days = 30

  tags = {
    Environment = var.environment
  }
}

resource "aws_iam_role" "flow_logs" {
  name = "takeoff-${var.environment}-vpc-flow-logs"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "flow_logs" {
  name = "flow-logs-policy"
  role = aws_iam_role.flow_logs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

# Secrets rotation
resource "aws_secretsmanager_secret_rotation" "db_password" {
  secret_id           = var.db_secret_arn
  rotation_lambda_arn = aws_lambda_function.secret_rotation.arn

  rotation_rules {
    automatically_after_days = 30
  }
}

data "aws_caller_identity" "current" {}

variable "db_secret_arn" {
  type = string
}

# Outputs
output "waf_arn" {
  value = aws_wafv2_web_acl.main.arn
}

output "kms_key_arn" {
  value = aws_kms_key.main.arn
}
```

---

## Production Environment Configuration

### Task 12.13: Environment Configuration

Create `infrastructure/terraform/environments/production/main.tf`:

```hcl
# Production Environment Configuration

terraform {
  required_version = ">= 1.5.0"

  backend "s3" {
    bucket         = "takeoff-terraform-state"
    key            = "production/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "takeoff-terraform-locks"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "takeoff"
      Environment = "production"
      ManagedBy   = "terraform"
    }
  }
}

locals {
  environment = "production"
}

# Networking
module "networking" {
  source = "../../modules/networking"

  environment        = local.environment
  vpc_cidr           = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

# Database
module "database" {
  source = "../../modules/database"

  environment           = local.environment
  vpc_id                = module.networking.vpc_id
  subnet_ids            = module.networking.private_subnet_ids
  security_group_id     = module.networking.database_security_group_id
  instance_class        = "db.r6g.large"
  allocated_storage     = 200
  max_allocated_storage = 1000
}

# Redis
module "redis" {
  source = "../../modules/redis"

  environment       = local.environment
  vpc_id            = module.networking.vpc_id
  subnet_ids        = module.networking.private_subnet_ids
  security_group_id = module.networking.redis_security_group_id
  node_type         = "cache.r6g.medium"
  num_cache_nodes   = 2
}

# Storage (S3)
module "storage" {
  source = "../../modules/storage"

  environment = local.environment
}

# Compute (ECS)
module "compute" {
  source = "../../modules/compute"

  environment           = local.environment
  vpc_id                = module.networking.vpc_id
  public_subnet_ids     = module.networking.public_subnet_ids
  private_subnet_ids    = module.networking.private_subnet_ids
  alb_security_group_id = module.networking.alb_security_group_id
  ecs_security_group_id = module.networking.ecs_security_group_id
  certificate_arn       = var.certificate_arn

  api_image     = "${var.ecr_registry}/takeoff-api:${var.image_tag}"
  worker_image  = "${var.ecr_registry}/takeoff-worker:${var.image_tag}"
  frontend_image = "${var.ecr_registry}/takeoff-frontend:${var.image_tag}"

  api_desired_count    = 3
  worker_desired_count = 5

  environment_variables = {
    ENVIRONMENT    = local.environment
    LOG_LEVEL      = "INFO"
    MINIO_ENDPOINT = module.storage.endpoint
    REDIS_URL      = module.redis.endpoint
  }

  secrets = {
    DATABASE_URL    = module.database.secret_arn
    ANTHROPIC_API_KEY = var.anthropic_api_key_arn
    SECRET_KEY      = var.secret_key_arn
    MINIO_ACCESS_KEY = module.storage.access_key_secret_arn
    MINIO_SECRET_KEY = module.storage.secret_key_secret_arn
  }
}

# Security
module "security" {
  source = "../../modules/security"

  environment   = local.environment
  vpc_id        = module.networking.vpc_id
  db_secret_arn = module.database.secret_arn
}

# Monitoring
module "monitoring" {
  source = "../../modules/monitoring"

  environment     = local.environment
  cluster_name    = module.compute.cluster_name
  alb_arn_suffix  = module.compute.alb_arn_suffix
  alert_email     = var.alert_email
  slack_webhook   = var.slack_webhook_url
}

# DNS
resource "aws_route53_record" "api" {
  zone_id = var.route53_zone_id
  name    = "api.takeoff.example.com"
  type    = "A"

  alias {
    name                   = module.compute.alb_dns_name
    zone_id                = module.compute.alb_zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "app" {
  zone_id = var.route53_zone_id
  name    = "app.takeoff.example.com"
  type    = "A"

  alias {
    name                   = module.compute.alb_dns_name
    zone_id                = module.compute.alb_zone_id
    evaluate_target_health = true
  }
}

# Outputs
output "api_endpoint" {
  value = "https://api.takeoff.example.com"
}

output "app_endpoint" {
  value = "https://app.takeoff.example.com"
}

output "database_endpoint" {
  value     = module.database.endpoint
  sensitive = true
}
```

Create `infrastructure/terraform/environments/production/variables.tf`:

```hcl
variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "ecr_registry" {
  type        = string
  description = "ECR registry URL"
}

variable "image_tag" {
  type        = string
  default     = "latest"
  description = "Docker image tag to deploy"
}

variable "certificate_arn" {
  type        = string
  description = "ACM certificate ARN for HTTPS"
}

variable "route53_zone_id" {
  type        = string
  description = "Route53 hosted zone ID"
}

variable "anthropic_api_key_arn" {
  type        = string
  description = "Secrets Manager ARN for Anthropic API key"
}

variable "secret_key_arn" {
  type        = string
  description = "Secrets Manager ARN for application secret key"
}

variable "alert_email" {
  type        = string
  description = "Email address for alerts"
}

variable "slack_webhook_url" {
  type        = string
  description = "Slack webhook URL for notifications"
  sensitive   = true
}
```

---

## Deployment Checklist

### Task 12.14: Pre-Deployment Checklist

Create `docs/operations/deployment-checklist.md`:

```markdown
# Production Deployment Checklist

## Pre-Deployment

### Code & Testing
- [ ] All tests passing in CI
- [ ] Code reviewed and approved
- [ ] Security scan completed (no critical/high vulnerabilities)
- [ ] Performance testing completed (if applicable)
- [ ] Documentation updated

### Infrastructure
- [ ] Database migrations tested on staging
- [ ] Infrastructure changes applied to staging first
- [ ] SSL certificates valid (not expiring within 30 days)
- [ ] Secrets rotated if needed

### Monitoring
- [ ] All dashboards showing healthy metrics
- [ ] No active alerts
- [ ] On-call engineer aware of deployment

### Communication
- [ ] Team notified in #deployments channel
- [ ] Deployment window confirmed (avoid peak hours)
- [ ] Rollback plan documented

## Deployment

### Execution
- [ ] Create deployment tag/release
- [ ] Trigger deployment workflow
- [ ] Monitor CI/CD pipeline
- [ ] Watch for migration errors

### Verification
- [ ] Health checks passing
- [ ] Version endpoint returning new version
- [ ] Smoke tests passing
- [ ] No new errors in logs
- [ ] Key metrics stable

### Post-Deployment
- [ ] Notify team of successful deployment
- [ ] Update status page (if applicable)
- [ ] Monitor for 30 minutes
- [ ] Close deployment ticket

## Rollback Triggers

Initiate rollback if:
- [ ] Health checks failing for >5 minutes
- [ ] Error rate >5% increase
- [ ] P95 latency >2x baseline
- [ ] Critical functionality broken
- [ ] Data integrity issues detected

## Rollback Procedure

```bash
# 1. Get previous task definition
PREV_TASK=$(aws ecs describe-services --cluster takeoff-production --services api \
    --query 'services[0].deployments[1].taskDefinition' --output text)

# 2. Update service to previous version
aws ecs update-service --cluster takeoff-production --service api --task-definition "$PREV_TASK"
aws ecs update-service --cluster takeoff-production --service worker --task-definition "$PREV_WORKER_TASK"

# 3. Wait for rollback to complete
aws ecs wait services-stable --cluster takeoff-production --services api worker

# 4. Verify rollback
curl https://api.takeoff.example.com/health

# 5. Notify team
echo "Rollback completed. Previous version restored."
```

## Emergency Contacts

| Role | Contact |
|------|---------|
| On-Call | PagerDuty |
| Engineering Lead | @eng-lead |
| DevOps | @devops |
```

---


---

## NEW: Kreo-Enhanced Feature Monitoring (v2.0)

Add these metrics to your monitoring configuration for the new features:

### Assembly System Metrics

```yaml
# Prometheus alerting rules for assemblies
groups:
  - name: assembly_alerts
    rules:
      - alert: AssemblyCalculationError
        expr: rate(assembly_calculation_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High assembly calculation error rate"
          
      - alert: AssemblyFormulaEvaluationSlow
        expr: histogram_quantile(0.95, assembly_formula_evaluation_seconds_bucket) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Assembly formula evaluation taking too long"
```

### Auto Count Metrics

```yaml
# Prometheus alerting rules for auto count
groups:
  - name: auto_count_alerts
    rules:
      - alert: AutoCountSessionTimeout
        expr: rate(auto_count_session_timeouts_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Auto count sessions timing out"
          
      - alert: AutoCountLowPrecision
        expr: auto_count_precision_ratio < 0.80
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Auto count detection precision below target"
```

### Enhanced Review Metrics

```yaml
# Prometheus alerting rules for review
groups:
  - name: review_alerts
    rules:
      - alert: ReviewAutoAcceptHighVolume
        expr: rate(review_auto_accepted_total[1h]) > 100
        for: 5m
        labels:
          severity: info
        annotations:
          summary: "High volume of auto-accepted measurements"
          
      - alert: ReviewQueueBacklog
        expr: review_pending_count > 500
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Review queue backlog growing"
```

### Grafana Dashboard Additions

Add these panels to your dashboards:

**Assembly Dashboard:**
- Assembly calculations per hour
- Average calculation time
- Formulas by type (material, labor, equipment)
- Cost breakdowns by assembly

**Auto Count Dashboard:**
- Sessions created per day
- Average detections per session
- Confirmation rate (confirmed / total)
- Measurements created from auto count

**Review Dashboard:**
- Review throughput (measurements per hour)
- Auto-accept rate
- Keyboard shortcut usage
- Average time to approve

| Terraform Modules | networking, database, compute, security | ⬜ |
| CI/CD Pipeline | GitHub Actions workflows | ⬜ |
| Monitoring | Prometheus, Grafana, Alertmanager | ⬜ |
| Backup & Recovery | Backup scripts, restore procedures | ⬜ |
| Runbooks | Incident response, scaling, troubleshooting | ⬜ |
| Security | WAF, KMS, VPC Flow Logs | ⬜ |

### Production Readiness Checklist

- [ ] All services containerized and tested
- [ ] Infrastructure provisioned via Terraform
- [ ] CI/CD pipeline operational
- [ ] Monitoring and alerting configured
- [ ] Backup system tested
- [ ] Runbooks documented and reviewed
- [ ] Security hardening applied
- [ ] Load testing completed
- [ ] Disaster recovery plan documented
- [ ] Team trained on operational procedures

### Estimated Completion

| Task Group | Duration |
|------------|----------|
| Docker & Nginx | 1 week |
| Terraform Infrastructure | 2 weeks |
| CI/CD Pipeline | 1 week |
| Monitoring & Alerting | 1 week |
| Security & Compliance | 1 week |
| Documentation & Testing | 1 week |

**Total: 6 weeks (Weeks 30-36)**

---

## Next Steps

After completing Phase 6:

1. **Production Launch**
   - Execute deployment checklist
   - Monitor closely for first 48 hours
   - Gather initial user feedback

2. **SaaS Preparation (3-4 months)**
   - Multi-tenancy implementation
   - Billing and subscription management
   - Customer onboarding workflow
   - Marketing website

3. **Continuous Improvement**
   - AI model refinement based on usage data
   - Performance optimization
   - Feature enhancements based on feedback
