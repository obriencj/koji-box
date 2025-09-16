#!/bin/bash


echo "Configuring Koji client..."

echo "export REQUESTS_CA_BUNDLE=${REQUESTS_CA_BUNDLE-/etc/ssl/certs/ca-certificates.crt}" >> $HOME/.bashrc

# Test Koji client functionality
echo "Testing Koji client functionality..."

# Test koji command availability
if command -v koji >/dev/null 2>&1; then
    echo "✓ koji command is available"

    # Test koji version
    echo "Koji version:"
    koji version || echo "Could not get koji version"

    # Test koji list-hosts (if authenticated)
    echo "Testing koji-admin list-hosts:"
    $HOME/.local/bin/koji-admin list-hosts || echo "Could not list hosts (may need authentication)"

else
    echo "✗ koji command is not available"
    exit 1
fi

echo "Koji client test complete"

# The end.
