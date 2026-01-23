# Documentation Index

Complete documentation for the ForgeX Takeoffs platform.

---

## 📚 Quick Links

| Document | Description |
|----------|-------------|
| [Docker Workflow](./development/DOCKER_WORKFLOW.md) | ⭐ **START HERE** - Docker-first development guide |
| [Setup Complete](./plans/SETUP_COMPLETE.md) | Current system status and quick commands |
| [API Reference](./api/API_REFERENCE.md) | Complete API endpoint documentation |
| [OCR API](./api/OCR_API.md) | OCR and text extraction endpoints |
| [Database Schema](./database/DATABASE_SCHEMA.md) | Database structure and relationships |
| [OCR Service](./services/OCR_SERVICE.md) | OCR service implementation guide |
| [Scale Service](./services/SCALE_SERVICE.md) | Scale detection and calibration service |
| [Measurement Service](./services/MEASUREMENT_SERVICE.md) | Measurement engine service |
| [Google Cloud Setup](./deployment/GOOGLE_CLOUD_SETUP.md) | Google Cloud Platform configuration |
| [Phase 2B Complete](./phase-guides/PHASE_2B_COMPLETE.md) | ✅ Phase 2B completion status |
| [Phase 3A Guide](./phase-guides/PHASE_3A_GUIDE.md) | ⭐ Complete measurement engine guide |

---

## 📁 Documentation Structure

### `/api/` - API Documentation
- **API_REFERENCE.md** - Complete endpoint reference with examples
- **OCR_API.md** - OCR and text extraction API reference
- **API-CONVENTIONS.md** - API design patterns and standards

### `/database/` - Database Documentation
- **DATABASE_SCHEMA.md** - Tables, relationships, and data models

### `/deployment/` - Deployment & Operations
- **DEPLOYMENT_SETUP.md** - Production deployment guide
- **DOCKER_GUIDE.md** - Docker configuration and commands
- **GOOGLE_CLOUD_SETUP.md** - Google Cloud Platform setup (Cloud Vision API)

### `/development/` - Development Workflow
- **DOCKER_WORKFLOW.md** - ⭐ **Docker-first development guide** (start here!)
- **DOCKER_QUICK_REFERENCE.md** - Quick Docker commands

### `/design/` - Design System
- **DESIGN-SYSTEM.md** - UI components and design patterns

### `/plans/` - Implementation Plans
- **SETUP_COMPLETE.md** - ✅ System setup and verification
- **PHASE_1A_VERIFICATION.md** - ✅ Phase 1A completion status
- **PHASE_1A_IMPLEMENTATION.md** - Phase 1A implementation details

### `/frontend/` - Frontend Documentation
- **FRONTEND_IMPLEMENTATION.md** - React architecture and components

### `/phase-guides/` - Phase-by-Phase Guides
- **PHASE_1A_COMPLETE.md** - Document ingestion (complete)
- **PHASE_1B_COMPLETE.md** - OCR and text extraction (complete)
- **PHASE_2A_COMPLETE.md** - Page classification (complete)
- **PHASE_2A_DOCKER_TESTING.md** - Docker testing guide for Phase 2A
- **PHASE_2B_COMPLETE.md** - Scale detection and calibration (complete)
- **PHASE_3A_GUIDE.md** - ⭐ Measurement engine complete guide (API, geometry types, examples)
- **PHASE_3A_COMPLETE.md** - Measurement engine implementation report
- **PHASE_3B_COMPLETE.md** - Condition management (complete)

### `/services/` - Service Documentation
- **OCR_SERVICE.md** - OCR service implementation and usage
- **SCALE_SERVICE.md** - Scale detection and calibration service
- **MEASUREMENT_SERVICE.md** - Measurement engine service implementation

---

## 🎯 Current Status: **Phase 3B Complete** ✅

### Completed Phases
- ✅ **Phase 0:** Project Setup
- ✅ **Phase 1A:** Document Ingestion
- ✅ **Phase 1B:** OCR and Text Extraction
- ✅ **Phase 2A:** Page Classification
- ✅ **Phase 2B:** Scale Detection and Calibration
- ✅ **Phase 3B:** Condition Management

### Current Phase
- 🔄 **Phase 3A:** Measurement Engine (In Progress)

### Services Running
- ✅ PostgreSQL (localhost:5432)
- ✅ Redis (localhost:6379)
- ✅ MinIO (localhost:9000)
- ✅ API (http://localhost:8000)
- ✅ Frontend (http://localhost:5173)
- ✅ Celery Worker (background processing)

---

## 🤖 AI/LLM Features (Phase 2A & 2B)

### Multi-Provider LLM Support
The platform supports multiple AI providers for page classification:

| Provider | Model | Best For |
|----------|-------|----------|
| **Anthropic** | Claude 3.5 Sonnet | Recommended primary - best accuracy |
| **OpenAI** | GPT-4o | Fast, good accuracy |
| **Google** | Gemini 2.5 Flash | Cost-effective |
| **xAI** | Grok Vision | Alternative option |

### Page Classification (Phase 2A)
- **Discipline Detection**: Structural, Architectural, Civil, Mechanical, Electrical, Plumbing, Landscape, General
- **Page Type Detection**: Plan, Elevation, Section, Detail, Schedule, Notes, Cover, Title
- **Concrete Relevance**: high, medium, low, none
- **Confidence Scoring**: 0-100% confidence for each classification

### Scale Detection (Phase 2B)
- **Automatic Detection**: Parses 15+ scale formats from OCR text
  - Architectural: `1/4" = 1'-0"`, `1" = 1'-0"`, etc.
  - Engineering: `1" = 20'`, `1" = 50'`, etc.
  - Metric: `1:100`, `1:50`, etc.
- **Visual Detection**: OpenCV-based scale bar recognition
- **Manual Calibration**: User-specified pixel-to-distance mapping
- **Scale Copying**: Copy calibrated scale between similar pages
- **Auto-Calibration**: High-confidence detections (≥85%) automatically calibrate pages

---

## 🔗 External References

- [Main Project README](../README.md)
- [Phase Prompts](../PHASE_PROMPTS.md) - Complete implementation guide
- [Project Plans](../plans/) - Original specification documents

---

## 📝 Contributing to Documentation

When adding new documentation:

1. **Place in appropriate folder:**
   - API changes → `/api/`
   - Database changes → `/database/`
   - New features → `/plans/`

2. **Update this index** with links to new docs

3. **Follow naming convention:**
   - Use UPPERCASE with hyphens: `NEW-FEATURE.md`
   - Be descriptive: `PHASE_2A_CLASSIFICATION.md`

---

**Last Updated:** January 22, 2026 - Phase 3B Complete
