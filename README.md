# Takeoff Automation

AI-Powered Construction Takeoff Platform - Automated Plan Analysis & Quantity Extraction System

## Overview

This platform automates the analysis of construction plan sets (PDF and TIFF formats), identifies relevant scopes of work, extracts measurements, and generates draft takeoffs that human estimators can review and refine.

## Project Status

**Current Phase:** Phase 1 - Foundation

## Documentation

- [Phase 1 Task List](docs/PHASE_1_TASK_LIST.md) - Detailed breakdown of foundation tasks

## Technology Stack

### Backend
- Python 3.11+
- FastAPI
- PostgreSQL 15+
- Redis + Celery
- SQLAlchemy 2.0

### Frontend
- React 18+ with TypeScript
- Vite
- Tailwind CSS + Shadcn/ui
- Zustand
- PDF.js

### Infrastructure
- Docker + Docker Compose
- MinIO (S3-compatible storage)

## Getting Started

*Setup instructions will be added as Phase 1 infrastructure tasks are completed.*

## Project Phases

1. **Phase 1: Foundation** - Project scaffolding, file upload, document viewer
2. **Phase 2: Classification** - LLM integration, page classification, OCR
3. **Phase 3: Measurement Engine** - Scale calibration, area/linear detection
4. **Phase 4: Review Interface** - Interactive overlay editing
5. **Phase 5: Export & Polish** - Excel/OST export, derived calculations
6. **Phase 6: SaaS Preparation** - Multi-tenancy, billing, public launch
