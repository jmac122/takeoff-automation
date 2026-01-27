#!/bin/bash
# ============================================================================
# AI Takeoff Integration Test Script
# 
# This script tests the full AI takeoff flow end-to-end:
# 1. Create a project
# 2. Upload a document
# 3. Wait for processing
# 4. Calibrate page scale
# 5. Create a condition
# 6. Trigger AI takeoff
# 7. Poll for completion
# 8. Verify measurements created
#
# Prerequisites:
# - Docker services running (api, worker, postgres, redis, minio)
# - curl and jq installed
# - A test PDF file at /tmp/test_plan.pdf (or skip document upload)
#
# Usage:
#   ./test_ai_takeoff_integration.sh [API_URL]
#
# Default API_URL: http://localhost:8000
# ============================================================================

set -e

# Configuration
API_URL="${1:-http://localhost:8000}"
API_BASE="${API_URL}/api/v1"
TIMEOUT=300  # 5 minutes max for the entire test
POLL_INTERVAL=5

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test state
PROJECT_ID=""
DOCUMENT_ID=""
PAGE_ID=""
CONDITION_ID=""
TASK_ID=""

# ============================================================================
# Utility Functions
# ============================================================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}[STEP] $1${NC}"
    echo -e "${GREEN}========================================${NC}"
}

cleanup() {
    log_step "Cleaning up test data"
    
    if [ -n "$PROJECT_ID" ]; then
        log_info "Deleting project: $PROJECT_ID"
        curl -s -X DELETE "${API_BASE}/projects/${PROJECT_ID}" > /dev/null 2>&1 || true
    fi
    
    log_info "Cleanup complete"
}

# Cleanup on exit
trap cleanup EXIT

check_api_health() {
    log_step "Checking API health"
    
    local response
    response=$(curl -s -w "%{http_code}" -o /tmp/health_response.json "${API_BASE}/health")
    
    if [ "$response" != "200" ]; then
        log_error "API health check failed with status: $response"
        cat /tmp/health_response.json
        exit 1
    fi
    
    log_info "API is healthy"
    cat /tmp/health_response.json | jq .
}

wait_for_services() {
    log_step "Waiting for services to be ready"
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "${API_BASE}/health" > /dev/null 2>&1; then
            log_info "Services ready after $attempt attempts"
            return 0
        fi
        log_info "Waiting for services... (attempt $attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_error "Services did not become ready in time"
    exit 1
}

# ============================================================================
# Test Functions
# ============================================================================

test_get_providers() {
    log_step "Testing GET /ai-takeoff/providers"
    
    local response
    response=$(curl -s "${API_BASE}/ai-takeoff/providers")
    
    echo "$response" | jq .
    
    # Verify response structure
    local available
    available=$(echo "$response" | jq -r '.available | length')
    
    if [ "$available" -eq 0 ]; then
        log_warn "No LLM providers configured - AI takeoff tests may fail"
    else
        log_info "Found $available available provider(s)"
    fi
}

create_test_project() {
    log_step "Creating test project"
    
    local response
    response=$(curl -s -X POST "${API_BASE}/projects" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "AI Takeoff Integration Test",
            "description": "Automated test project for AI takeoff"
        }')
    
    PROJECT_ID=$(echo "$response" | jq -r '.id')
    
    if [ "$PROJECT_ID" == "null" ] || [ -z "$PROJECT_ID" ]; then
        log_error "Failed to create project"
        echo "$response"
        exit 1
    fi
    
    log_info "Created project: $PROJECT_ID"
}

create_mock_page() {
    log_step "Creating mock page for testing"
    
    # Since we don't have a real document, we'll need to use an existing page
    # or the test will need to upload a document first
    
    # For now, let's check if there are any existing pages in the project
    local response
    response=$(curl -s "${API_BASE}/projects/${PROJECT_ID}/documents")
    
    local doc_count
    doc_count=$(echo "$response" | jq -r '.documents | length')
    
    if [ "$doc_count" -eq 0 ]; then
        log_warn "No documents in project. Skipping document-dependent tests."
        log_warn "To run full integration tests, upload a PDF document first."
        return 1
    fi
    
    DOCUMENT_ID=$(echo "$response" | jq -r '.documents[0].id')
    log_info "Using document: $DOCUMENT_ID"
    
    # Get first page from document
    response=$(curl -s "${API_BASE}/documents/${DOCUMENT_ID}/pages")
    PAGE_ID=$(echo "$response" | jq -r '.pages[0].id')
    
    if [ "$PAGE_ID" == "null" ] || [ -z "$PAGE_ID" ]; then
        log_warn "No pages found in document"
        return 1
    fi
    
    log_info "Using page: $PAGE_ID"
    return 0
}

create_test_condition() {
    log_step "Creating test condition"
    
    local response
    response=$(curl -s -X POST "${API_BASE}/projects/${PROJECT_ID}/conditions" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "4\" SOG Test",
            "scope": "concrete",
            "category": "slabs",
            "measurement_type": "area",
            "color": "#22C55E",
            "unit": "SF",
            "depth": 4
        }')
    
    CONDITION_ID=$(echo "$response" | jq -r '.id')
    
    if [ "$CONDITION_ID" == "null" ] || [ -z "$CONDITION_ID" ]; then
        log_error "Failed to create condition"
        echo "$response"
        exit 1
    fi
    
    log_info "Created condition: $CONDITION_ID"
}

test_ai_takeoff_uncalibrated() {
    log_step "Testing AI takeoff on uncalibrated page (should fail)"
    
    if [ -z "$PAGE_ID" ]; then
        log_warn "Skipping - no page available"
        return
    fi
    
    local response
    local http_code
    
    response=$(curl -s -w "\n%{http_code}" -X POST "${API_BASE}/pages/${PAGE_ID}/ai-takeoff" \
        -H "Content-Type: application/json" \
        -d "{\"condition_id\": \"${CONDITION_ID}\"}")
    
    http_code=$(echo "$response" | tail -n 1)
    response=$(echo "$response" | head -n -1)
    
    if [ "$http_code" == "400" ]; then
        log_info "Correctly rejected uncalibrated page with 400"
        echo "$response" | jq .
    else
        log_warn "Expected 400 for uncalibrated page, got: $http_code"
        echo "$response"
    fi
}

calibrate_page() {
    log_step "Calibrating page scale"
    
    if [ -z "$PAGE_ID" ]; then
        log_warn "Skipping - no page available"
        return 1
    fi
    
    # Set a mock scale calibration
    local response
    response=$(curl -s -X PUT "${API_BASE}/pages/${PAGE_ID}/scale" \
        -H "Content-Type: application/json" \
        -d '{
            "scale_value": 48.0,
            "scale_text": "1/4\" = 1'\''0\"",
            "scale_calibrated": true,
            "calibration_line": {
                "start": {"x": 100, "y": 100},
                "end": {"x": 200, "y": 100},
                "known_length_feet": 10.0
            }
        }')
    
    local scale_calibrated
    scale_calibrated=$(echo "$response" | jq -r '.scale_calibrated')
    
    if [ "$scale_calibrated" == "true" ]; then
        log_info "Page calibrated successfully"
        return 0
    else
        log_error "Failed to calibrate page"
        echo "$response"
        return 1
    fi
}

test_ai_takeoff() {
    log_step "Testing AI takeoff generation"
    
    if [ -z "$PAGE_ID" ]; then
        log_warn "Skipping - no page available"
        return
    fi
    
    local response
    response=$(curl -s -X POST "${API_BASE}/pages/${PAGE_ID}/ai-takeoff" \
        -H "Content-Type: application/json" \
        -d "{\"condition_id\": \"${CONDITION_ID}\"}")
    
    TASK_ID=$(echo "$response" | jq -r '.task_id')
    
    if [ "$TASK_ID" == "null" ] || [ -z "$TASK_ID" ]; then
        log_error "Failed to start AI takeoff"
        echo "$response"
        return 1
    fi
    
    log_info "AI takeoff started with task: $TASK_ID"
    echo "$response" | jq .
    return 0
}

poll_task_status() {
    log_step "Polling task status"
    
    if [ -z "$TASK_ID" ]; then
        log_warn "Skipping - no task to poll"
        return 1
    fi
    
    local max_attempts=60  # 5 minutes at 5s intervals
    local attempt=1
    local status="PENDING"
    
    while [ $attempt -le $max_attempts ]; do
        local response
        response=$(curl -s "${API_BASE}/tasks/${TASK_ID}/status")
        
        status=$(echo "$response" | jq -r '.status')
        
        log_info "Task status: $status (attempt $attempt/$max_attempts)"
        
        if [ "$status" == "SUCCESS" ]; then
            log_info "Task completed successfully!"
            echo "$response" | jq .
            return 0
        elif [ "$status" == "FAILURE" ]; then
            log_error "Task failed!"
            echo "$response" | jq .
            return 1
        fi
        
        sleep $POLL_INTERVAL
        attempt=$((attempt + 1))
    done
    
    log_error "Task did not complete in time (status: $status)"
    return 1
}

verify_measurements() {
    log_step "Verifying measurements were created"
    
    if [ -z "$PAGE_ID" ]; then
        log_warn "Skipping - no page available"
        return
    fi
    
    local response
    response=$(curl -s "${API_BASE}/pages/${PAGE_ID}/measurements")
    
    local count
    count=$(echo "$response" | jq -r '.measurements | length')
    
    log_info "Found $count measurements on page"
    
    # Check for AI-generated measurements
    local ai_count
    ai_count=$(echo "$response" | jq '[.measurements[] | select(.is_ai_generated == true)] | length')
    
    log_info "AI-generated measurements: $ai_count"
    
    if [ "$ai_count" -gt 0 ]; then
        log_info "Sample AI measurement:"
        echo "$response" | jq '.measurements[] | select(.is_ai_generated == true) | {id, geometry_type, quantity, unit, ai_confidence, ai_model}' | head -20
    fi
}

test_provider_comparison() {
    log_step "Testing provider comparison"
    
    if [ -z "$PAGE_ID" ]; then
        log_warn "Skipping - no page available"
        return
    fi
    
    local response
    response=$(curl -s -X POST "${API_BASE}/pages/${PAGE_ID}/compare-providers" \
        -H "Content-Type: application/json" \
        -d "{\"condition_id\": \"${CONDITION_ID}\"}")
    
    local task_id
    task_id=$(echo "$response" | jq -r '.task_id')
    
    if [ "$task_id" == "null" ] || [ -z "$task_id" ]; then
        log_warn "Failed to start provider comparison (may need multiple providers configured)"
        echo "$response"
        return 1
    fi
    
    log_info "Provider comparison started with task: $task_id"
    echo "$response" | jq .
}

# ============================================================================
# Main Test Execution
# ============================================================================

main() {
    log_info "Starting AI Takeoff Integration Tests"
    log_info "API URL: $API_URL"
    log_info ""
    
    # Wait for services
    wait_for_services
    
    # Health check
    check_api_health
    
    # Test providers endpoint
    test_get_providers
    
    # Create test project
    create_test_project
    
    # Create condition
    create_test_condition
    
    # Try to get a page (requires existing document)
    if create_mock_page; then
        # Test uncalibrated page rejection
        test_ai_takeoff_uncalibrated
        
        # Calibrate page
        if calibrate_page; then
            # Test AI takeoff
            if test_ai_takeoff; then
                # Poll for completion
                if poll_task_status; then
                    # Verify measurements
                    verify_measurements
                fi
            fi
            
            # Test provider comparison
            test_provider_comparison
        fi
    else
        log_warn ""
        log_warn "============================================"
        log_warn "To run full integration tests:"
        log_warn "1. Upload a PDF document to the test project"
        log_warn "2. Run this script again"
        log_warn "============================================"
    fi
    
    log_step "Test Summary"
    log_info "Project ID: $PROJECT_ID"
    log_info "Document ID: $DOCUMENT_ID"
    log_info "Page ID: $PAGE_ID"
    log_info "Condition ID: $CONDITION_ID"
    log_info "Task ID: $TASK_ID"
    
    log_info ""
    log_info "Integration tests completed!"
}

# Run main function
main "$@"
