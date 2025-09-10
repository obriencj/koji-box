#!/bin/bash
# Basic functionality test for Boxed Koji

set -e

echo "Running basic functionality tests..."

# Test 1: Check if all services are running
echo "Test 1: Checking service status..."
podman-compose -f docker-compose.yml -p koji-boxed ps

# Test 2: Test Koji Hub connectivity
echo "Test 2: Testing Koji Hub connectivity..."
curl -f http://localhost:8080/status || {
    echo "ERROR: Koji Hub not responding"
    exit 1
}

# Test 3: Test Koji Web connectivity
echo "Test 3: Testing Koji Web connectivity..."
curl -f http://localhost:8081/ || {
    echo "ERROR: Koji Web not responding"
    exit 1
}

# Test 4: Test Storage service
echo "Test 4: Testing Storage service..."
curl -f http://localhost:8082/health || {
    echo "ERROR: Storage service not responding"
    exit 1
}

# Test 5: Test database connectivity
echo "Test 5: Testing database connectivity..."
podman exec koji-boxed-postgres-1 pg_isready -U koji -d koji || {
    echo "ERROR: Database not ready"
    exit 1
}

echo "All basic functionality tests passed!"
