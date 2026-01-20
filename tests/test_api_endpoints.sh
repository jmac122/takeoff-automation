#!/bin/bash
# Test script for Phase 3A API endpoints

echo "=========================================="
echo "Testing Phase 3A Measurement Engine APIs"
echo "=========================================="

API_BASE="http://localhost:8000/api/v1"

# Test 1: Health check
echo -e "\n✓ Test 1: Health endpoint"
curl -s "$API_BASE/health" | jq .

# Test 2: List projects
echo -e "\n✓ Test 2: List projects"
curl -s "$API_BASE/projects" | jq '.projects | length'

# Test 3: Get first project ID
PROJECT_ID=$(curl -s "$API_BASE/projects" | jq -r '.projects[0].id // empty')

if [ -n "$PROJECT_ID" ]; then
    echo "  Found project: $PROJECT_ID"
    
    # Test 4: List conditions for project
    echo -e "\n✓ Test 3: List conditions for project"
    curl -s "$API_BASE/projects/$PROJECT_ID/conditions" | jq '.total'
    
    # Test 5: Create a test condition
    echo -e "\n✓ Test 4: Create test condition"
    CONDITION_RESPONSE=$(curl -s -X POST "$API_BASE/projects/$PROJECT_ID/conditions" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "API Test Slab",
        "measurement_type": "area",
        "unit": "SF",
        "color": "#FF5733",
        "line_width": 2,
        "fill_opacity": 0.3
      }')
    
    CONDITION_ID=$(echo "$CONDITION_RESPONSE" | jq -r '.id')
    echo "  Created condition: $CONDITION_ID"
    
    # Test 6: Get condition
    echo -e "\n✓ Test 5: Get condition details"
    curl -s "$API_BASE/conditions/$CONDITION_ID" | jq '{id, name, measurement_type, total_quantity}'
    
    # Test 7: List measurements (should be empty)
    echo -e "\n✓ Test 6: List measurements for condition (should be 0)"
    curl -s "$API_BASE/conditions/$CONDITION_ID/measurements" | jq '.total'
    
    # Test 8: Delete test condition
    echo -e "\n✓ Test 7: Delete test condition"
    curl -s -X DELETE "$API_BASE/conditions/$CONDITION_ID"
    echo "  Condition deleted"
    
else
    echo "⚠ No projects found - some tests skipped"
fi

echo -e "\n=========================================="
echo "✅ API Endpoint Tests Complete!"
echo "=========================================="
