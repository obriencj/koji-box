#!/bin/bash
# Nginx functionality test for Boxed Koji

set -e

echo "Running Nginx functionality tests..."

# Test 1: Check if nginx is running
echo "Test 1: Checking nginx status..."
podman exec koji-boxed-nginx-1 pgrep nginx || {
    echo "ERROR: Nginx not running"
    exit 1
}

# Test 2: Test nginx health check
echo "Test 2: Testing nginx health check..."
curl -f http://localhost/health || {
    echo "ERROR: Nginx health check failed"
    exit 1
}

# Test 3: Test root path (should go to koji-web)
echo "Test 3: Testing root path routing..."
curl -f http://localhost/ | grep -i "koji" || {
    echo "ERROR: Root path not routing to koji-web"
    exit 1
}

# Test 4: Test /kojihub path (should go to koji-hub)
echo "Test 4: Testing /kojihub path routing..."
curl -f http://localhost/kojihub/ | grep -i "koji" || {
    echo "ERROR: /kojihub path not routing to koji-hub"
    exit 1
}

# Test 5: Test /downloads path (should serve static content)
echo "Test 5: Testing /downloads path..."
curl -f http://localhost/downloads/ | grep -i "index" || {
    echo "ERROR: /downloads path not serving static content"
    exit 1
}

# Test 6: Test nginx configuration syntax
echo "Test 6: Testing nginx configuration..."
podman exec koji-boxed-nginx-1 nginx -t || {
    echo "ERROR: Nginx configuration syntax error"
    exit 1
}

echo "All Nginx functionality tests passed!"
