#!/bin/bash

echo "Configuring Koji client..."

# Test Koji client functionality
echo "Testing Koji client functionality..."

# Test koji command availability
if command -v koji >/dev/null 2>&1; then
    echo "✓ koji command is available"

    # Test koji version
    echo "Koji version:"
    koji version

    echo "Koji hello:"
    koji hello

else
    echo "✗ koji command is not available"
    exit 1
fi

echo "Koji client test complete"

# The end.
