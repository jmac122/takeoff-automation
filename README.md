# ForgeX Takeoffs

AI-powered construction takeoff automation platform.

## 📊 Current Status

### ✅ **Phase 1B: OCR and Text Extraction - COMPLETE**

Phase 1B has been fully implemented with Google Cloud Vision integration, automatic text extraction, pattern detection, and full-text search. See [STATUS.md](STATUS.md) for detailed implementation status.

**Completed:**
- ✅ Phase 1A: Document Ingestion
- ✅ Phase 1B: OCR and Text Extraction

**Ready for Phase 2A: Page Classification**

## 🚀 Quick Start

### Prerequisites

**Required:**
- Docker Desktop (20.10+) and Docker Compose (2.x+)
- Git
- Cursor IDE or VS Code

**NOT Required:**
- ❌ Python (runs in Docker)
- ❌ Node.js (runs in Docker)
- ❌ PostgreSQL (runs in Docker)
- ❌ Redis (runs in Docker)

### 🐳 Docker Setup (Only Way)

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/takeoff-platform.git
   cd takeoff-platform
   ```

2. **Create environment file**
   ```bash
   cp docker-env.example .env
   # Edit .env if needed for LLM API keys (optional for Phase 1A)
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - **Frontend**: http://localhost:5173
   - **Backend API**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/api/docs
   - **MinIO Console**: http://localhost:9001

5. **Run commands inside Docker**
   ```bash
   # Run tests
   docker compose exec api pytest
   
   # Run migrations
   docker compose exec api alembic upgrade head
   
   # Get a shell
   docker compose exec api bash
   ```

### 💻 Development Workflow

**Code in Cursor IDE, Run in Docker:**

1. **Edit code locally** - Use Cursor IDE to edit files
2. **Auto-sync to Docker** - Changes automatically appear in containers
3. **Test in Docker** - Run all commands via `docker compose exec`

```bash
# Example workflow
# 1. Edit backend/app/api/routes/pages.py in Cursor
# 2. Save file (Ctrl+S)
# 3. Test immediately in Docker
docker compose exec api pytest tests/test_pages.py
```

See [Docker Workflow Guide](docs/development/DOCKER_WORKFLOW.md) for complete instructions.

### 🧪 Testing the Implementation

**All testing happens in Docker containers:**

```bash
# Run verification script
docker compose exec api python test_ocr_verification.py

# Run unit tests
docker compose exec api pytest

# Run specific test
docker compose exec api pytest tests/test_ocr_service.py

# Run with coverage
docker compose exec api pytest --cov=app tests/
```

**Manual testing:**
1. **Open the frontend** at http://localhost:5173
2. **Create a test project** (API call or through UI)
3. **Upload a PDF/TIFF file** using the drag-and-drop interface
4. **Monitor processing status** in real-time
5. **View processed pages** with OCR data

## 📚 Documentation

### Implementation Documentation
- **[STATUS.md](STATUS.md)** - Current implementation status and roadmap
- **[docs/README.md](docs/README.md)** - Main documentation index
- **[docs/phase-guides/PHASE_1A_COMPLETE.md](docs/phase-guides/PHASE_1A_COMPLETE.md)** - Phase 1A completion guide
- **[docs/phase-guides/PHASE_1B_COMPLETE.md](docs/phase-guides/PHASE_1B_COMPLETE.md)** - Phase 1B completion guide

### API Documentation
- **[docs/api/API_REFERENCE.md](docs/api/API_REFERENCE.md)** - Complete API reference
- **[docs/api/OCR_API.md](docs/api/OCR_API.md)** - OCR API endpoints

### Service Documentation
- **[docs/services/OCR_SERVICE.md](docs/services/OCR_SERVICE.md)** - OCR service implementation
- **[docs/API_REFERENCE.md](docs/API_REFERENCE.md)** - REST API endpoints and usage
- **[docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md)** - Database design and schema
- **[docs/FRONTEND_IMPLEMENTATION.md](docs/FRONTEND_IMPLEMENTATION.md)** - React frontend architecture
- **[docs/DEPLOYMENT_SETUP.md](docs/DEPLOYMENT_SETUP.md)** - Development and production setup

### Original Specifications
- **[plans/](plans/)** - Phase specifications and requirements
- **[PHASE_PROMPTS.md](PHASE_PROMPTS.md)** - Implementation instructions

## 🏗️ Architecture

### Current Implementation (Phase 1A)

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React App     │    │   FastAPI        │    │   PostgreSQL    │
│   (Frontend)    │◄──►│   Backend        │◄──►│   Database      │
│                 │    │                  │    │                 │
│ • File Upload   │    │ • Document API   │    │ • Projects      │
│ • Progress UI   │    │ • Validation     │    │ • Documents     │
│ • Status Display│    │ • Processing     │    │ • Pages         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Celery        │    │   Redis          │    │   MinIO/S3      │
│   Workers       │◄──►│   Queue          │    │   Storage       │
│                 │    │                  │    │                 │
│ • PDF/TIFF      │    │ • Task Queue     │    │ • File Storage   │
│   Processing    │    │ • Status Updates │    │ • Images         │
│ • Page Extract  │    │                  │    │ • Thumbnails     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0, PostgreSQL, Redis, Celery
- **Frontend**: React 18, TypeScript, Vite, TailwindCSS
- **Storage**: MinIO (S3-compatible), local filesystem (dev)
- **Processing**: Async document processing with background workers
- **Infrastructure**: Docker, Docker Compose (future)

## 🎯 Features (Phase 1A)

### Document Management
- ✅ PDF and TIFF file upload support
- ✅ Multi-page document processing
- ✅ File validation and type checking
- ✅ Automatic thumbnail generation
- ✅ Progress tracking and status updates
- ✅ Error handling and recovery

### API Capabilities
- ✅ RESTful CRUD operations for documents
- ✅ Real-time processing status polling
- ✅ Project-based document organization
- ✅ File upload with multipart support
- ✅ Comprehensive error responses

### Processing Pipeline
- ✅ Async document processing with Celery
- ✅ Page image extraction and storage
- ✅ Background task management
- ✅ Structured logging and monitoring
- ✅ Configurable processing options

## 🧪 Testing & Verification

### Run Tests
```bash
# Backend tests
cd backend && python -m pytest

# Frontend tests
cd frontend && npm test

# Integration verification
cd backend && python test_verification.py
```

### API Testing
```bash
# Health check
curl http://localhost:8000/api/v1/health

# Create project
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Project"}'

# Upload document
curl -X POST http://localhost:8000/api/v1/projects/{id}/documents \
  -F "file=@document.pdf"
```

## 🔧 Development Commands

### Backend
```bash
cd backend

# Run server
uvicorn app.main:app --reload

# Run worker
celery -A app.workers.celery_app worker --loglevel=info

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head

# Run tests
python -m pytest
```

### Frontend
```bash
cd frontend

# Development server
npm run dev

# Build for production
npm run build

# Run tests
npm test

# Lint code
npm run lint
```

## 🚀 Deployment

### Development (Local)
See [docs/DEPLOYMENT_SETUP.md](docs/DEPLOYMENT_SETUP.md) for detailed local setup instructions.

### Production
- Docker containerization
- Nginx reverse proxy
- SSL/TLS encryption
- Process monitoring (PM2)
- Database backups

### Docker (Future)
```bash
# Quick start with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f
```

## 🤝 Contributing

### Code Standards
- **Python**: PEP 8, type hints, async/await patterns
- **TypeScript**: Strict mode, explicit types
- **Git**: Conventional commits, feature branches
- **Testing**: Comprehensive test coverage
- **Documentation**: Update docs for API changes

### Development Workflow
1. Create feature branch: `git checkout -b feature/name`
2. Write tests and implementation
3. Run tests and linting
4. Update documentation
5. Submit pull request

### Commit Convention
```
feat: Add new feature
fix: Bug fix
docs: Documentation update
refactor: Code refactoring
test: Add tests
chore: Maintenance tasks
```

## 📊 Roadmap

### ✅ Completed
- **Phase 1A**: Document Ingestion - Complete
  - File upload and validation
  - Async processing pipeline
  - API and frontend implementation
  - Database schema and migrations

### 🔄 Next Phases
- **Phase 1B**: OCR Text Extraction
- **Phase 2A**: Page Classification
- **Phase 2B**: Scale Detection
- **Phase 3A**: Interactive Measurements
- **Phase 3B**: Export System

## 📞 Support

For questions or issues:
1. Check [docs/README.md](docs/README.md) and [STATUS.md](STATUS.md)
2. Review troubleshooting in deployment docs
3. Check existing issues or create new ones
4. Include detailed error logs and reproduction steps

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Built with ❤️ for the construction industry**

*Phase 1A: Document Ingestion - Complete and production-ready*
