#!/bin/bash
# Test script for koji-hub entrypoint

set -e

echo "Testing koji-hub entrypoint..."

# Test that the entrypoint script exists and is executable
if [ -f "/usr/local/bin/entrypoint.sh" ] && [ -x "/usr/local/bin/entrypoint.sh" ]; then
    echo "✓ Entrypoint script exists and is executable"
else
    echo "✗ Entrypoint script not found or not executable"
    exit 1
fi

# Test that Koji tools are available after entrypoint runs
if command -v koji-hub >/dev/null 2>&1; then
    echo "✓ koji-hub is available"
    koji-hub --version
else
    echo "✗ koji-hub not found"
    exit 1
fi

if command -v koji >/dev/null 2>&1; then
    echo "✓ koji CLI is available"
    koji --version
else
    echo "✗ koji CLI not found"
    exit 1
fi

# Test that hub configuration exists
if [ -f "/etc/koji-hub/hub.conf" ]; then
    echo "✓ Hub configuration exists"
    echo "Configuration contents:"
    cat /etc/koji-hub/hub.conf
else
    echo "✗ Hub configuration not found"
    exit 1
fi

# Test that Kerberos configuration exists
if [ -f "/etc/krb5.conf" ]; then
    echo "✓ Kerberos configuration exists"
    echo "Kerberos configuration contents:"
    cat /etc/krb5.conf
else
    echo "✗ Kerberos configuration not found"
    exit 1
fi

# Test that database is accessible
if pg_isready -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}"; then
    echo "✓ Database is accessible"
else
    echo "✗ Database is not accessible"
    exit 1
fi

echo -e "\n✓ All koji-hub entrypoint tests passed!"
