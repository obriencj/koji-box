#!/bin/bash
# Test script for keytab service entrypoint

set -e

echo "Testing keytab service entrypoint..."

# Test that the entrypoint script exists and is executable
if [ -f "/app/entrypoint.sh" ] && [ -x "/app/entrypoint.sh" ]; then
    echo "✓ Entrypoint script exists and is executable"
else
    echo "✗ Entrypoint script not found or not executable"
    exit 1
fi

# Test that Koji CLI is available after entrypoint runs
if command -v koji >/dev/null 2>&1; then
    echo "✓ Koji CLI is available"
    koji --version
else
    echo "✗ Koji CLI not found"
    exit 1
fi

# Test that Kerberos configuration exists
if [ -f "/etc/krb5.conf" ]; then
    echo "✓ Kerberos configuration exists"
    cat /etc/krb5.conf
else
    echo "✗ Kerberos configuration not found"
    exit 1
fi

# Test that keytabs directory exists and is writable
if [ -d "/mnt/keytabs" ] && [ -w "/mnt/keytabs" ]; then
    echo "✓ Keytabs directory exists and is writable"
else
    echo "✗ Keytabs directory not found or not writable"
    exit 1
fi

echo -e "\n✓ All entrypoint tests passed!"
