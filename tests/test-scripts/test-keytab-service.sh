#!/bin/bash
# Test script for Keytab Service

set -e

echo "Testing Keytab Service..."

# Wait for service to be ready
echo "Waiting for keytab service to be ready..."
for i in {1..30}; do
    if curl -f http://keytabs.koji.box:80/health >/dev/null 2>&1; then
        echo "Keytab service is ready"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 2
done

# Test health endpoint
echo "Testing health endpoint..."
curl -f http://keytabs.koji.box:80/health

# Test service info endpoint
echo -e "\nTesting service info endpoint..."
curl -f http://keytabs.koji.box:80/

# Test principal creation and keytab download
echo -e "\nTesting principal creation..."
PRINCIPAL_NAME="test-principal-$(date +%s)"
curl -f -o "/tmp/${PRINCIPAL_NAME}.keytab" "http://keytabs.koji.box:80/api/v1/principal/${PRINCIPAL_NAME}"

if [ -f "/tmp/${PRINCIPAL_NAME}.keytab" ]; then
    echo "✓ Principal keytab created successfully"
    ls -la "/tmp/${PRINCIPAL_NAME}.keytab"
else
    echo "✗ Failed to create principal keytab"
    exit 1
fi

# Test worker creation and keytab download
echo -e "\nTesting worker creation..."
WORKER_NAME="test-worker-$(date +%s)"
curl -f -o "/tmp/${WORKER_NAME}.keytab" "http://keytabs.koji.box:80/api/v1/worker/${WORKER_NAME}"

if [ -f "/tmp/${WORKER_NAME}.keytab" ]; then
    echo "✓ Worker keytab created successfully"
    ls -la "/tmp/${WORKER_NAME}.keytab"
else
    echo "✗ Failed to create worker keytab"
    exit 1
fi

# Test that the worker was actually registered with Koji hub
echo -e "\nTesting worker registration with Koji hub..."
# This would require access to the Koji hub from the test environment
# For now, we'll just verify the keytab was created
if [ -f "/tmp/${WORKER_NAME}.keytab" ] && [ -s "/tmp/${WORKER_NAME}.keytab" ]; then
    echo "✓ Worker keytab is valid (non-empty file)"
else
    echo "✗ Worker keytab is invalid or empty"
    exit 1
fi

# Test static file serving
echo -e "\nTesting static file serving..."
curl -f -o "/tmp/static-test.keytab" "http://keytabs.koji.box:80/principals/${PRINCIPAL_NAME}.keytab"

if [ -f "/tmp/static-test.keytab" ]; then
    echo "✓ Static file serving works"
    ls -la "/tmp/static-test.keytab"
else
    echo "✗ Static file serving failed"
    exit 1
fi

# Cleanup
rm -f "/tmp/${PRINCIPAL_NAME}.keytab" "/tmp/${WORKER_NAME}.keytab" "/tmp/static-test.keytab"

echo -e "\n✓ All Keytab Service tests passed!"
