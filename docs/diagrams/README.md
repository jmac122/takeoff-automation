# System Diagrams

Visual documentation of the ForgeX Takeoffs platform architecture and workflows.

## Diagrams Index

| Diagram | Description |
|---------|-------------|
| [Document Processing Pipeline](document-processing-pipeline.md) | PDF upload → page extraction → storage flow |
| [OCR and Classification Flow](ocr-classification-flow.md) | OCR → classification → scale detection chain |
| [Scale Detection Accuracy](scale-detection-accuracy.md) | How pixel-perfect scale bbox accuracy is achieved |
| [Frontend Viewer Rendering](frontend-viewer-rendering.md) | TakeoffViewer canvas and overlay rendering |
| [Project Lifecycle](project-lifecycle.md) | Complete workflow from project creation to export |
| [Celery Task Chain](celery-task-chain.md) | Background task orchestration and dependencies |

## Viewing Diagrams

These diagrams use [Mermaid](https://mermaid.js.org/) syntax. They render automatically in:
- GitHub / GitLab markdown preview
- VS Code with Mermaid extension
- Cursor IDE markdown preview

## Quick Reference

### Processing Flow Summary

```
PDF Upload → Extract Pages → OCR → Classify → Scale Detect → Ready for Takeoff
```

### Key Technologies

| Layer | Technology |
|-------|------------|
| Task Queue | Celery + Redis |
| Storage | MinIO (S3-compatible) |
| OCR | Google Cloud Vision |
| AI Classification | Multi-provider LLM (Claude, GPT-4o, Gemini, Grok) |
| Scale Detection | Gemini 2.5 Flash + OCR bbox matching |
| Frontend Canvas | Konva.js |

### Image Resolution

All page images are stored at **max 1568px** on the longest edge. This ensures:
- No compression needed for LLM vision calls
- Consistent coordinate system across all operations
- Pixel-perfect bounding box accuracy
