#!/bin/bash
# ============================================================================
# Test Runner Script for Takeoff Automation
# 
# Runs tests inside Docker containers or locally.
#
# Usage:
#   ./scripts/run_tests.sh [command]
#
# Commands:
#   unit        - Run backend unit tests (pytest)
#   integration - Run integration tests against running containers
#   all         - Run all tests
#   rebuild     - Rebuild Docker containers and run tests
#
# Examples:
#   ./scripts/run_tests.sh unit
#   ./scripts/run_tests.sh integration
#   ./scripts/run_tests.sh rebuild
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DOCKER_DIR="$PROJECT_ROOT/docker"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Rebuild Docker containers
rebuild_containers() {
    log_step "Rebuilding Docker containers"
    
    cd "$DOCKER_DIR"
    
    log_info "Stopping existing containers..."
    docker compose down --remove-orphans || true
    
    log_info "Building containers..."
    docker compose build --no-cache
    
    log_info "Starting containers..."
    docker compose up -d
    
    log_info "Waiting for services to be ready..."
    sleep 10
    
    # Wait for API to be healthy
    local max_attempts=30
    local attempt=1
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
            log_info "API is ready!"
            break
        fi
        log_info "Waiting for API... (attempt $attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log_error "API did not become ready in time"
        docker compose logs api
        exit 1
    fi
}

# Run backend unit tests
run_unit_tests() {
    log_step "Running Backend Unit Tests"
    
    cd "$PROJECT_ROOT/backend"
    
    # Check if we're in a virtual environment or use docker
    if [ -n "$VIRTUAL_ENV" ]; then
        log_info "Running tests in virtual environment..."
        python -m pytest tests/test_ai_takeoff.py -v --tb=short
    else
        log_info "Running tests in Docker container..."
        cd "$DOCKER_DIR"
        docker compose exec -T api python -m pytest tests/test_ai_takeoff.py -v --tb=short
    fi
}

# Run integration tests
run_integration_tests() {
    log_step "Running Integration Tests"
    
    # Check if containers are running
    cd "$DOCKER_DIR"
    if ! docker compose ps | grep -q "api.*running"; then
        log_warn "Containers not running. Starting them..."
        docker compose up -d
        sleep 10
    fi
    
    # Run integration test script
    log_info "Running integration tests..."
    bash "$PROJECT_ROOT/backend/tests/test_ai_takeoff_integration.sh" http://localhost:8000
}

# Run all tests
run_all_tests() {
    run_unit_tests
    run_integration_tests
}

# Show help
show_help() {
    echo "Test Runner for Takeoff Automation"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  unit        Run backend unit tests (pytest)"
    echo "  integration Run integration tests against running containers"
    echo "  all         Run all tests"
    echo "  rebuild     Rebuild Docker containers and run tests"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 unit"
    echo "  $0 integration"
    echo "  $0 rebuild"
}

# Main
main() {
    local command="${1:-help}"
    
    case "$command" in
        unit)
            check_docker
            run_unit_tests
            ;;
        integration)
            check_docker
            run_integration_tests
            ;;
        all)
            check_docker
            run_all_tests
            ;;
        rebuild)
            check_docker
            rebuild_containers
            run_all_tests
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
