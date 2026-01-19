# ForgeX Takeoffs

AI-powered construction takeoff automation platform.

## 📊 Current Status

### ✅ **Phase 1A: Document Ingestion - COMPLETE**

Phase 1A has been fully implemented with comprehensive document upload, processing, and management capabilities. See [STATUS.md](STATUS.md) for detailed implementation status.

**Ready for Phase 1B: OCR Text Extraction**

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose (recommended)
- Python 3.11+ (alternative manual setup)
- Node.js 18+ (alternative manual setup)
- PostgreSQL 15+ (alternative manual setup)
- Redis (alternative manual setup)

### 🐳 Docker Setup (Recommended)

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

### 🔧 Manual Development Setup (Alternative)

1. **Clone and setup**
   ```bash
   git clone https://github.com/your-org/takeoff-platform.git
   cd takeoff-platform
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   alembic upgrade head  # Database migrations
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Start Services**
   ```bash
   # Redis (required for Celery)
   redis-server

   # Backend API
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

   # Celery Worker (new terminal)
   celery -A app.workers.celery_app worker --loglevel=info
   ```

### 🧪 Testing the Implementation

Once running, you can test the document upload functionality:

1. **Open the frontend** at http://localhost:5173
2. **Create a test project** (API call or through UI)
3. **Upload a PDF/TIFF file** using the drag-and-drop interface
4. **Monitor processing status** in real-time
5. **View processed pages** with thumbnails

## 📚 Documentation

### Phase 1A Documentation
- **[STATUS.md](STATUS.md)** - Current implementation status and roadmap
- **[docs/README.md](docs/README.md)** - Main documentation index
- **[docs/PHASE_1A_IMPLEMENTATION.md](docs/PHASE_1A_IMPLEMENTATION.md)** - Complete technical implementation guide
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
