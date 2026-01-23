"""
E2E Test Configuration and Fixtures

These tests run against REAL services - not mocks.
Requires all Docker services running.
"""

import os
import time
from typing import Generator
from dataclasses import dataclass

import pytest
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ============================================================================
# Configuration
# ============================================================================

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
API_V1_URL = f"{API_BASE_URL}/api/v1"

# Timeouts
DEFAULT_TIMEOUT = 30
PROCESSING_TIMEOUT = 300  # 5 minutes for document processing
AI_TAKEOFF_TIMEOUT = 180  # 3 minutes for AI takeoff

# Test data paths (relative to backend/)
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "test_data")


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class TestProject:
    """Test project data."""
    id: str
    name: str


@dataclass
class TestDocument:
    """Test document data."""
    id: str
    project_id: str
    filename: str


@dataclass
class TestPage:
    """Test page data."""
    id: str
    document_id: str
    page_number: int
    width: int
    height: int
    scale_calibrated: bool
    scale_value: float | None


@dataclass 
class TestCondition:
    """Test condition data."""
    id: str
    project_id: str
    name: str
    measurement_type: str
    unit: str


@dataclass
class TestMeasurement:
    """Test measurement data."""
    id: str
    condition_id: str
    page_id: str
    geometry_type: str
    quantity: float
    unit: str
    is_ai_generated: bool


# ============================================================================
# HTTP Client with Retries
# ============================================================================

def create_http_session() -> requests.Session:
    """Create HTTP session with retry logic."""
    session = requests.Session()
    
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def api_url() -> str:
    """API base URL."""
    return API_V1_URL


@pytest.fixture(scope="session")
def http_session() -> Generator[requests.Session, None, None]:
    """HTTP session for API calls."""
    session = create_http_session()
    yield session
    session.close()


@pytest.fixture(scope="session")
def api_health_check(http_session: requests.Session, api_url: str) -> bool:
    """Verify API is healthy before running tests."""
    try:
        response = http_session.get(
            f"{api_url}/health",
            timeout=DEFAULT_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        return True
    except Exception as e:
        pytest.fail(f"API health check failed: {e}")


@pytest.fixture(scope="session")
def test_project(
    http_session: requests.Session,
    api_url: str,
    api_health_check: bool,
) -> Generator[TestProject, None, None]:
    """Create a test project for E2E tests."""
    # Create project
    response = http_session.post(
        f"{api_url}/projects",
        json={
            "name": f"E2E Test Project {int(time.time())}",
            "description": "Automated E2E integration test project",
            "client_name": "Test Client",
        },
        timeout=DEFAULT_TIMEOUT,
    )
    
    assert response.status_code in [200, 201], f"Failed to create project: {response.text}"
    data = response.json()
    
    project = TestProject(
        id=data["id"],
        name=data["name"],
    )
    
    yield project
    
    # Cleanup: Delete project (cascades to all related data)
    try:
        http_session.delete(
            f"{api_url}/projects/{project.id}",
            timeout=DEFAULT_TIMEOUT,
        )
    except Exception:
        pass  # Best effort cleanup


@pytest.fixture(scope="module")
def test_condition(
    http_session: requests.Session,
    api_url: str,
    test_project: TestProject,
) -> Generator[TestCondition, None, None]:
    """Create a test condition for measurements."""
    response = http_session.post(
        f"{api_url}/projects/{test_project.id}/conditions",
        json={
            "name": "6\" SOG Test",
            "scope": "concrete",
            "category": "slabs",
            "measurement_type": "area",
            "unit": "SF",
            "color": "#4CAF50",
            "depth": 6.0,
        },
        timeout=DEFAULT_TIMEOUT,
    )
    
    assert response.status_code in [200, 201], f"Failed to create condition: {response.text}"
    data = response.json()
    
    condition = TestCondition(
        id=data["id"],
        project_id=test_project.id,
        name=data["name"],
        measurement_type=data["measurement_type"],
        unit=data["unit"],
    )
    
    yield condition


# ============================================================================
# Helper Functions
# ============================================================================

def wait_for_document_processing(
    http_session: requests.Session,
    api_url: str,
    document_id: str,
    timeout: int = PROCESSING_TIMEOUT,
) -> dict:
    """Wait for document processing to complete."""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        response = http_session.get(
            f"{api_url}/documents/{document_id}",
            timeout=DEFAULT_TIMEOUT,
        )
        
        if response.status_code != 200:
            time.sleep(5)
            continue
            
        data = response.json()
        status = data.get("status")
        
        if status == "ready":
            return data
        elif status == "error":
            raise Exception(f"Document processing failed: {data.get('error')}")
        
        time.sleep(5)
    
    raise TimeoutError(f"Document processing timed out after {timeout}s")


def wait_for_task_completion(
    http_session: requests.Session,
    api_url: str,
    task_id: str,
    timeout: int = AI_TAKEOFF_TIMEOUT,
) -> dict:
    """Wait for a Celery task to complete."""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        response = http_session.get(
            f"{api_url}/tasks/{task_id}/status",
            timeout=DEFAULT_TIMEOUT,
        )
        
        if response.status_code != 200:
            time.sleep(2)
            continue
            
        data = response.json()
        status = data.get("status")
        
        if status == "SUCCESS":
            return data
        elif status in ["FAILURE", "REVOKED"]:
            raise Exception(f"Task failed: {data.get('error', 'Unknown error')}")
        
        time.sleep(2)
    
    raise TimeoutError(f"Task timed out after {timeout}s")


def poll_with_progress(
    http_session: requests.Session,
    api_url: str,
    task_id: str,
    description: str,
    timeout: int = AI_TAKEOFF_TIMEOUT,
) -> dict:
    """Poll task with progress output."""
    import sys
    
    start_time = time.time()
    dots = 0
    
    while time.time() - start_time < timeout:
        response = http_session.get(
            f"{api_url}/tasks/{task_id}/status",
            timeout=DEFAULT_TIMEOUT,
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get("status")
            
            if status == "SUCCESS":
                sys.stdout.write(" Done!\n")
                sys.stdout.flush()
                return data
            elif status in ["FAILURE", "REVOKED"]:
                sys.stdout.write(" FAILED\n")
                sys.stdout.flush()
                raise Exception(f"Task failed: {data.get('error', 'Unknown error')}")
        
        # Progress indicator
        if dots % 20 == 0:
            sys.stdout.write(f"\n{description}")
        sys.stdout.write(".")
        sys.stdout.flush()
        dots += 1
        
        time.sleep(2)
    
    sys.stdout.write(" TIMEOUT\n")
    sys.stdout.flush()
    raise TimeoutError(f"Task timed out after {timeout}s")
