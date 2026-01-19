# ForgeX Takeoffs

AI-powered construction takeoff automation platform.

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 20+
- At least one LLM API key (Anthropic, OpenAI, Google, or xAI)

### Setup

1. Clone the repository
2. Copy environment file and configure API keys:

   ```bash
   cp .env.example .env
   # Edit .env and add your LLM API keys
   ```

3. Run setup:

   ```bash
   make setup
   ```

4. Start development environment:

   ```bash
   make dev
   ```

5. Access the application:
   - Frontend: http://localhost:5173
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/api/docs
   - MinIO Console: http://localhost:9001

## LLM Provider Configuration

The platform supports multiple LLM providers for AI operations:

| Provider  | Model             | Best For                              |
| --------- | ----------------- | ------------------------------------- |
| Anthropic | Claude 3.5 Sonnet | General accuracy, recommended primary |
| OpenAI    | GPT-4o            | Good all-around performance           |
| Google    | Gemini 1.5 Pro    | Cost-effective option                 |
| xAI       | Grok Vision       | Alternative option                    |

### Configuration Options

```env
# Set default provider
DEFAULT_LLM_PROVIDER=anthropic

# Configure fallbacks (comma-separated)
LLM_FALLBACK_PROVIDERS=openai,google

# Override provider per task (optional)
LLM_PROVIDER_PAGE_CLASSIFICATION=google
LLM_PROVIDER_SCALE_DETECTION=anthropic
LLM_PROVIDER_ELEMENT_DETECTION=anthropic
LLM_PROVIDER_MEASUREMENT=anthropic
```

### Benchmarking Providers

Configure all provider API keys to run accuracy benchmarks:

```bash
# Run benchmark comparison across all providers
make benchmark-llm
```

## Development

### Running Tests

```bash
make test
```

### Running Linters

```bash
make lint
```

### Database Migrations

```bash
# Create a new migration
make create-migration name="add_users_table"

# Apply migrations
make migrate
```

## Architecture

See `/docs/architecture` for detailed architecture documentation.

## Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy, PostgreSQL, Redis, Celery
- **Frontend**: React 18, TypeScript, Vite, TailwindCSS, Konva.js
- **AI/ML**: Multi-LLM support (Anthropic, OpenAI, Google, xAI)
- **Storage**: MinIO (S3-compatible)
- **Infrastructure**: Docker, Docker Compose

## API Endpoints

All endpoints under `/api/v1/`:

```
Projects:     /projects, /projects/{id}
Documents:    /projects/{id}/documents, /documents/{id}
Pages:        /documents/{id}/pages, /pages/{id}
Conditions:   /projects/{id}/conditions, /conditions/{id}
Measurements: /conditions/{id}/measurements, /measurements/{id}
Exports:      /projects/{id}/export, /exports/{id}
Settings:     /settings/llm (LLM provider configuration)
```

## Data Model

```
Project (1) ──< Document (many) ──< Page (many)
    │                                    │
    ▼                                    ▼
Condition (many) ──────────────< Measurement (many)
```

- **Project**: Contains plan sets and takeoff conditions
- **Document**: A PDF/TIFF file (can be 100+ pages)
- **Page**: Individual sheet with classification, scale, OCR data
- **Condition**: Takeoff line item (e.g., "4" Concrete Slab")
- **Measurement**: Geometry on a page linked to a condition

## Contributing

1. Follow the established coding standards (SOLID, DRY, KISS)
2. Use type hints everywhere in Python
3. Strict TypeScript mode in frontend
4. Run tests and linters before committing
5. Follow conventional commit messages

## License

[Add license information here]
