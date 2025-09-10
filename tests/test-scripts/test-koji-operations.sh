#!/bin/bash
# Koji operations test

set -e

echo "Running Koji operations tests..."

# Test 1: List users
echo "Test 1: Listing users..."
podman exec koji-boxed-koji-hub-1 koji list-users || {
    echo "ERROR: Failed to list users"
    exit 1
}

# Test 2: List tags
echo "Test 2: Listing tags..."
podman exec koji-boxed-koji-hub-1 koji list-tags || {
    echo "ERROR: Failed to list tags"
    exit 1
}

# Test 3: List targets
echo "Test 3: Listing targets..."
podman exec koji-boxed-koji-hub-1 koji list-targets || {
    echo "ERROR: Failed to list targets"
    exit 1
}

# Test 4: List hosts
echo "Test 4: Listing hosts..."
podman exec koji-boxed-koji-hub-1 koji list-hosts || {
    echo "ERROR: Failed to list hosts"
    exit 1
}

# Test 5: Test build creation (dry run)
echo "Test 5: Testing build creation..."
podman exec koji-boxed-koji-hub-1 koji build --scratch dist-foo "test-package-1.0-1" || {
    echo "ERROR: Failed to create test build"
    exit 1
}

echo "All Koji operations tests passed!"
