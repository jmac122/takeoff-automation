#!/bin/bash
# ============================================================================
# End-to-End Test Runner
# 
# Runs comprehensive E2E tests against the live system.
# These tests use REAL services, REAL LLM calls, and REAL data.
#
# Usage:
#   ./scripts/run_e2e_tests.sh [options]
#
# Options:
#   --quick       Run only quick health checks
#   --full        Run full test suite including AI takeoff
#   --upload      Run document upload tests (requires PDFs in test_data/)
#   --ai          Run AI takeoff tests only
#   --all         Run everything
#   --help        Show this help
#
# Prerequisites:
#   - Docker services running (docker compose up -d)
#   - API healthy at http://localhost:8000
#   - For upload tests: PDF files in backend/tests/e2e/test_data/
#   - For AI tests: LLM API keys configured
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
DOCKER_DIR="docker"
API_URL="http://localhost:8000"
TIMEOUT=300

# ============================================================================
# Functions
# ============================================================================

print_header() {
    echo ""
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

check_docker() {
    print_header "Checking Docker Services"
    
    cd "$DOCKER_DIR" 2>/dev/null || cd "../$DOCKER_DIR"
    
    # Check if services are running
    if ! docker compose ps --services --filter "status=running" | grep -q "api"; then
        print_error "API container not running"
        echo "Start services with: cd docker && docker compose up -d"
        exit 1
    fi
    
    print_success "Docker services running"
}

check_api_health() {
    print_header "Checking API Health"
    
    local retries=10
    local wait=5
    
    for i in $(seq 1 $retries); do
        if curl -sf "${API_URL}/api/v1/health" > /dev/null; then
            print_success "API healthy at ${API_URL}"
            return 0
        fi
        echo "Waiting for API... ($i/$retries)"
        sleep $wait
    done
    
    print_error "API not responding at ${API_URL}"
    exit 1
}

run_quick_tests() {
    print_header "Running Quick Health Tests"
    
    docker compose exec -e PYTHONPATH=/app api pytest \
        tests/e2e/test_takeoff_workflow.py::TestPlatformHealth \
        -v -s --tb=short \
        || return 1
    
    print_success "Quick tests passed"
}

run_unit_tests() {
    print_header "Running Unit Tests"
    
    docker compose exec -e PYTHONPATH=/app api pytest \
        tests/test_ai_takeoff.py \
        tests/test_condition_templates.py \
        -v --tb=short \
        || return 1
    
    print_success "Unit tests passed"
}

run_upload_tests() {
    print_header "Running Document Upload Tests"
    
    # Check for test PDFs
    if [ ! -d "../backend/tests/e2e/test_data" ] || [ -z "$(ls -A ../backend/tests/e2e/test_data/*.pdf 2>/dev/null)" ]; then
        print_warning "No PDF files in backend/tests/e2e/test_data/"
        print_warning "Skipping upload tests. Add PDFs to enable."
        return 0
    fi
    
    docker compose exec -e PYTHONPATH=/app api pytest \
        tests/e2e/test_document_upload.py \
        -v -s --tb=short \
        || return 1
    
    print_success "Upload tests passed"
}

run_ai_tests() {
    print_header "Running AI Takeoff Tests"
    
    echo ""
    echo "NOTE: These tests make REAL LLM API calls."
    echo "Ensure API keys are configured in .env"
    echo ""
    
    docker compose exec -e PYTHONPATH=/app api pytest \
        tests/e2e/test_takeoff_workflow.py::TestAITakeoff \
        -v -s --tb=short \
        || return 1
    
    print_success "AI takeoff tests passed"
}

run_full_tests() {
    print_header "Running Full E2E Test Suite"
    
    docker compose exec -e PYTHONPATH=/app api pytest \
        tests/e2e/ \
        -v -s --tb=short \
        --timeout=600 \
        || return 1
    
    print_success "Full E2E tests passed"
}

run_accuracy_tests() {
    print_header "Running Measurement Accuracy Tests"
    
    docker compose exec -e PYTHONPATH=/app api pytest \
        tests/e2e/test_takeoff_workflow.py::TestMeasurementAccuracy \
        -v -s --tb=short \
        || return 1
    
    print_success "Accuracy tests passed"
}

show_help() {
    echo "E2E Test Runner for Takeoff Platform"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --quick       Quick health checks only"
    echo "  --unit        Run unit tests"
    echo "  --upload      Document upload tests (needs PDFs)"
    echo "  --ai          AI takeoff tests (needs LLM keys)"
    echo "  --accuracy    Measurement accuracy tests"
    echo "  --full        Full E2E suite"
    echo "  --all         Everything (unit + e2e)"
    echo "  --help        Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 --quick              # Just health checks"
    echo "  $0 --unit --accuracy    # Unit + accuracy tests"
    echo "  $0 --full               # Full E2E suite"
    echo "  $0 --all                # Everything"
}

# ============================================================================
# Main
# ============================================================================

main() {
    local run_quick=false
    local run_unit=false
    local run_upload=false
    local run_ai=false
    local run_accuracy=false
    local run_full=false
    
    # Parse arguments
    if [ $# -eq 0 ]; then
        run_quick=true
    fi
    
    while [ $# -gt 0 ]; do
        case "$1" in
            --quick)
                run_quick=true
                ;;
            --unit)
                run_unit=true
                ;;
            --upload)
                run_upload=true
                ;;
            --ai)
                run_ai=true
                ;;
            --accuracy)
                run_accuracy=true
                ;;
            --full)
                run_full=true
                ;;
            --all)
                run_unit=true
                run_full=true
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
        shift
    done
    
    # Run tests
    print_header "TAKEOFF PLATFORM E2E TESTS"
    echo "Started: $(date)"
    
    check_docker
    check_api_health
    
    local failed=0
    
    if [ "$run_quick" = true ]; then
        run_quick_tests || failed=1
    fi
    
    if [ "$run_unit" = true ]; then
        run_unit_tests || failed=1
    fi
    
    if [ "$run_accuracy" = true ]; then
        run_accuracy_tests || failed=1
    fi
    
    if [ "$run_upload" = true ]; then
        run_upload_tests || failed=1
    fi
    
    if [ "$run_ai" = true ]; then
        run_ai_tests || failed=1
    fi
    
    if [ "$run_full" = true ]; then
        run_full_tests || failed=1
    fi
    
    # Summary
    print_header "TEST SUMMARY"
    echo "Completed: $(date)"
    
    if [ $failed -eq 0 ]; then
        print_success "All tests passed!"
        exit 0
    else
        print_error "Some tests failed"
        exit 1
    fi
}

main "$@"
