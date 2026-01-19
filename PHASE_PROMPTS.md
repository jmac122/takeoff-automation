# Takeoff Platform - Phase Prompts

Use these prompts to start each phase. Copy and paste into a new Cursor chat when ready to begin that phase.

---

## Phase 0: Project Setup

```
Let's begin implementing the Takeoff Platform. Start with Phase 0 - Project Setup.

Read `plans/01-PROJECT-SETUP.md` and implement all tasks in order:
- Task 0.1: Initialize Repository Structure
- Task 0.2: Backend Setup (Python/FastAPI)
- Task 0.3: Frontend Setup
- Task 0.4: Database Configuration
- Task 0.5: Docker Configuration
- Task 0.6: CI/CD Pipeline
- Task 0.7: Makefile for Common Commands
- Task 0.8: README

Run through the verification checklist at the end before we proceed to the next phase.
```

---

## Phase 1A: Document Ingestion

```
Continue to Phase 1A - Document Ingestion.

Read `plans/02-DOCUMENT-INGESTION.md` and implement all tasks in order:
- Task 1.1: Create Document and Page Models
- Task 1.2: Create Initial Migration
- Task 1.3: Implement S3-Compatible Storage
- Task 1.4: Document Processing Service
- Task 1.5: Celery Worker Tasks
- Task 1.6: API Endpoints
- Task 1.7: Frontend Upload Component

Run through the verification checklist at the end before we proceed.
```

---

## Phase 1B: OCR and Text Extraction

```
Continue to Phase 1B - OCR and Text Extraction.

Read `plans/03-OCR-TEXT-EXTRACTION.md` and implement all tasks in order:
- Task 3.1: Google Cloud Vision Setup
- Task 3.2: OCR Service Implementation
- Task 3.3: Title Block Parser
- Task 3.4: OCR Celery Tasks
- Task 3.5: Page API Endpoints
- Task 3.6: Page Schemas
- Task 3.7: Search Index (Full-Text Search)

Run through the verification checklist and test cases at the end.
```

---

## Phase 2A: Page Classification

```
Continue to Phase 2A - Page Classification.

Read `plans/04-PAGE-CLASSIFICATION.md` and implement all tasks in order:
- Task 4.1: Multi-Provider LLM Client Service
- Task 4.2: Page Classification Service
- Task 4.3: Classification Celery Tasks
- Task 4.4: Classification API Endpoints
- Task 4.5: Frontend Provider Selector Component
- Task 4.6: Page Browser with Classification Filters

Run through the verification checklist and test cases at the end.
```

---

## Phase 2B: Scale Detection

```
Continue to Phase 2B - Scale Detection and Calibration.

Read `plans/05-SCALE-DETECTION.md` and implement all tasks in order:
- Task 5.1: Scale Parser Service
- Task 5.2: Scale Detection Service
- Task 5.3: Scale Celery Tasks
- Task 5.4: Scale API Endpoints
- Task 5.5: Frontend Scale Calibration Component

Run through the verification checklist and test cases at the end.
```

---

## Phase 3A: Measurement Engine

```
Continue to Phase 3A - Measurement Engine.

Read `plans/06-MEASUREMENT-ENGINE.md` and implement all tasks in order:
- Task 6.1: Measurement and Condition Models
- Task 6.2: Geometry Utilities
- Task 6.3: Measurement Calculator Service
- Task 6.4: Measurement API Endpoints
- Task 6.5: Frontend Measurement Tools
- Task 6.6: Measurement Layer Component

Run through the verification checklist and test cases at the end.
```

---

## Phase 3B: Condition Management

```
Continue to Phase 3B - Condition Management.

Read `plans/07-CONDITION-MANAGEMENT.md` and implement all tasks in order:
- Task 7.1: Condition API Routes
- Task 7.2: Condition Schemas
- Task 7.3: Frontend Condition Panel
- Task 7.4: Create Condition Modal
- Task 7.5: Condition Templates

Run through the verification checklist and test cases at the end.
```

---

## Phase 4A: AI Takeoff Generation

```
Continue to Phase 4A - AI Takeoff Generation.

Read `plans/08-AI-TAKEOFF-GENERATION.md` and implement all tasks in order:
- Task 8.1: AI Takeoff Service with Provider Selection
- Task 8.2: Element Detection Prompts
- Task 8.3: AI Takeoff Celery Tasks
- Task 8.4: AI Takeoff API Endpoints
- Task 8.5: Provider Comparison UI Component
- Task 8.6: Frontend AI Takeoff Trigger

Run through the verification checklist, test cases, and accuracy testing at the end.
```

---

## Phase 4B: Review Interface

```
Continue to Phase 4B - Review Interface.

Read `plans/09-REVIEW-INTERFACE.md` and implement all tasks in order:
- Task 9.1: Add Review Fields to Models
- Task 9.2: Review Statistics Model
- Task 9.3: Review Service Implementation
- Task 9.4: Review API Endpoints
- Task 9.5: Frontend Review Panel
- Task 9.6: Side-by-Side View Component
- Task 9.7: Bulk Actions Component
- Task 9.8: Review Workspace Page

Run through the verification checklist and test cases at the end.
```

---

## Phase 5A: Export System

```
Continue to Phase 5A - Export System.

Read `plans/10-EXPORT-SYSTEM.md` and implement all tasks in order:
- Task 10.1: Export Job Model
- Task 10.2: Base Export Service
- Task 10.3: Excel Exporter
- Task 10.4: OST XML Exporter
- Task 10.5: CSV Exporter
- Task 10.6: PDF Report Exporter
- Task 10.7: Export Celery Tasks
- Task 10.8: Export API Endpoints
- Task 10.9-10.14: Frontend Export Components

Run through the verification checklist and test cases at the end.
```

---

## Phase 5B: Testing & QA

```
Continue to Phase 5B - Testing & Quality Assurance.

Read `plans/11-TESTING-QA.md` and implement all tasks in order:
- Task 11.1: Test Configuration and Fixtures
- Task 11.2: Test Factories
- Task 11.3: Unit Tests (Geometry, Scale Parser, Measurement Calculator)
- Task 11.4: Integration Tests (API endpoints)
- Task 11.5: E2E Tests
- Task 11.6: AI Accuracy Benchmark System
- Task 11.7: Multi-Provider Benchmark
- Task 11.8: CI/CD Quality Gates
- Task 11.9: Performance Tests

Ensure all coverage targets are met and CI pipeline passes.
```

---

## Phase 6: Deployment

```
Continue to Phase 6 - Deployment & Operations.

Read `plans/12-DEPLOYMENT.md` and implement all tasks in order:
- Task 12.1: Production Dockerfiles
- Task 12.2: Nginx Configuration
- Task 12.3: Docker Compose Production
- Task 12.4: GitHub Actions Workflows
- Task 12.5: Terraform Modules (networking, database, compute)
- Task 12.6: Monitoring (Prometheus, Grafana)
- Task 12.7: Alerting Configuration
- Task 12.8: Backup Scripts
- Task 12.9: Operational Runbooks
- Task 12.10-12.14: Security, DNS, Final Infrastructure

Complete the production readiness checklist before launch.
```

---

## Resuming Mid-Phase

If you need to start a new chat in the middle of a phase, use this template:

```
I'm working on the Takeoff Platform, currently in Phase [X] - [Phase Name].

Read `plans/[XX-DOCUMENT-NAME.md]`.

I've completed:
- Task X.1: [Name]
- Task X.2: [Name]

Continue with Task X.3: [Name]
```

---

## Troubleshooting / Debugging

```
I'm working on the Takeoff Platform and encountering an issue.

Phase: [X] - [Phase Name]
Relevant spec: `plans/[XX-DOCUMENT-NAME.md]`

Issue: [Describe the problem]

[Paste any error messages or relevant code]
```
