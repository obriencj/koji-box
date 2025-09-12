#!/bin/bash
# Test script for manage-koji-host.sh

set -e

echo "Testing manage-koji-host.sh script..."

# Test with a sample worker name
WORKER_NAME="test-host-$(date +%s)"

echo "Testing with worker name: $WORKER_NAME"

# Run the script
if /app/manage-koji-host.sh "$WORKER_NAME"; then
    echo "✓ manage-koji-host.sh completed successfully"
else
    echo "✗ manage-koji-host.sh failed"
    exit 1
fi

# Test with invalid characters (should fail)
echo -e "\nTesting with invalid worker name..."
if /app/manage-koji-host.sh "invalid@name"; then
    echo "✗ Script should have failed with invalid name"
    exit 1
else
    echo "✓ Script correctly rejected invalid name"
fi

# Test without arguments (should fail)
echo -e "\nTesting without arguments..."
if /app/manage-koji-host.sh; then
    echo "✗ Script should have failed without arguments"
    exit 1
else
    echo "✓ Script correctly failed without arguments"
fi

echo -e "\n✓ All manage-koji-host.sh tests passed!"
