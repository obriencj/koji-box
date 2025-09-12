#!/bin/bash


echo "Configuring Koji client..."
mkdir -p ~/.koji
envsubst < /etc/koji.conf.template > ~/.koji/config
echo "✓ Koji client configured"


# Test Koji client functionality
echo "Testing Koji client functionality..."

# Test koji command availability
if command -v koji >/dev/null 2>&1; then
    echo "✓ koji command is available"
    
    # Test koji version
    echo "Koji version:"
    koji version || echo "Could not get koji version"
    
    # Test koji list-hosts (if authenticated)
    echo "Testing koji list-hosts:"
    koji list-hosts || echo "Could not list hosts (may need authentication)"
    
else
    echo "✗ koji command is not available"
    exit 1
fi

echo "Koji client test complete"
