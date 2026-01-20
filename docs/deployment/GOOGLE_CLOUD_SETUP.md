# Google Cloud Platform Setup

This document explains how to set up Google Cloud services for the Takeoff Automation platform.

## Prerequisites

- Google Cloud account
- `gcloud` CLI installed and authenticated
- Project created in Google Cloud Console

## Services Used

| Service | Purpose | Phase |
|---------|---------|-------|
| Cloud Vision API | OCR text extraction from construction drawings | 1B |

## Setup Instructions

### 1. Create and Configure Project

```bash
# Create project (if not already created)
gcloud projects create takeoff-automation --name="Takeoff Automation"

# Set as active project
gcloud config set project takeoff-automation

# Enable billing (required for Cloud Vision API)
# This must be done through the Cloud Console:
# https://console.cloud.google.com/billing
```

### 2. Enable Required APIs

```bash
# Enable Cloud Vision API
gcloud services enable vision.googleapis.com

# Verify enabled services
gcloud services list --enabled
```

### 3. Create Service Account

```bash
# Create service account for OCR
gcloud iam service-accounts create takeoff-ocr \
  --display-name="Takeoff OCR Service" \
  --description="Service account for Cloud Vision API access"

# Generate and download credentials
# Run this from your project root directory
gcloud iam service-accounts keys create credentials/google-cloud-key.json \
  --iam-account=takeoff-ocr@takeoff-automation.iam.gserviceaccount.com
```

**Important**: The `credentials/` folder is automatically mounted to `/app/credentials` in Docker containers.

### 4. Configure Environment

```bash
# The GOOGLE_APPLICATION_CREDENTIALS is already set in docker/.env
# It points to: /app/credentials/google-cloud-key.json
# This path is inside the container (the credentials/ folder is mounted)

# Verify the setting
cd docker
grep GOOGLE_APPLICATION_CREDENTIALS .env
```

### 5. Verify Setup

```bash
# Restart Docker services to load new credentials
cd docker
docker compose down
docker compose up -d

# Test Cloud Vision API connection
docker compose exec api python -c "from google.cloud import vision; client = vision.ImageAnnotatorClient(); print('✅ Cloud Vision API connected successfully!')"
```

Expected output:
```
✅ Cloud Vision API connected successfully!
```

## Security Best Practices

### Credentials Management

- ✅ **DO**: Keep `credentials/google-cloud-key.json` in `.gitignore`
- ✅ **DO**: Store credentials in the `credentials/` folder at project root
- ✅ **DO**: Use service accounts with minimal required permissions
- ❌ **DON'T**: Commit service account keys to Git
- ❌ **DON'T**: Share keys in chat/email/Slack

### Service Account Permissions

The service account only needs access to Cloud Vision API. It does **not** need:
- Project-level IAM roles
- Storage bucket access (we use MinIO)
- Database access
- Compute Engine permissions

The Cloud Vision API is enabled at the project level, and any service account in that project can use it without additional IAM bindings.

## Cost Management

### Cloud Vision API Pricing (as of 2024)

| Feature | First 1,000 units/month | Units 1,001+ |
|---------|------------------------|--------------|
| Text Detection (OCR) | Free | $1.50 per 1,000 images |
| Document Text Detection | Free | $1.50 per 1,000 images |

**Estimate for typical usage:**
- 100-page plan set = 100 API calls
- Cost per plan set (after free tier): ~$0.15
- 1,000 plan sets/month: ~$150/month

### Monitoring Usage

```bash
# View API usage in Cloud Console
gcloud logging read "resource.type=cloud_vision_api" --limit 50

# Set up billing alerts
# https://console.cloud.google.com/billing/alerts
```

## Troubleshooting

### Error: "DefaultCredentialsError"

**Problem**: Container can't find credentials file

**Solutions**:
1. Verify credentials file exists:
   ```bash
   ls -la credentials/google-cloud-key.json
   ```

2. Check if volume is mounted:
   ```bash
   cd docker
   docker compose exec api ls -la /app/credentials/
   ```

3. Verify environment variable:
   ```bash
   docker compose exec api env | grep GOOGLE_APPLICATION_CREDENTIALS
   ```

4. Restart containers:
   ```bash
   cd docker
   docker compose down
   docker compose up -d
   ```

### Error: "API not enabled"

**Problem**: Cloud Vision API not enabled for project

**Solution**:
```bash
gcloud services enable vision.googleapis.com
```

### Error: "Permission denied"

**Problem**: Service account lacks permissions

**Solution**: Cloud Vision API doesn't require additional IAM roles. Verify:
1. API is enabled: `gcloud services list --enabled | grep vision`
2. Service account exists: `gcloud iam service-accounts list`
3. Credentials file is valid JSON

## File Locations

```
takeoff-automation/
├── credentials/                          # Git-ignored
│   └── google-cloud-key.json            # Service account key
├── docker/
│   ├── .env                             # Contains GOOGLE_APPLICATION_CREDENTIALS
│   └── docker-compose.yml               # Mounts credentials/ to /app/credentials
└── docker-env.example                   # Template with setup instructions
```

## Related Documentation

- [Phase 1B Complete Guide](../phase-guides/PHASE_1B_COMPLETE.md)
- [OCR Service Documentation](../services/OCR_SERVICE.md)
- [Docker Workflow](../development/DOCKER_WORKFLOW.md)
- [Google Cloud Vision API Docs](https://cloud.google.com/vision/docs)
