#!/bin/bash
# Test script for koji-web entrypoint

set -e

echo "Testing koji-web entrypoint..."

# Test that the entrypoint script exists and is executable
if [ -f "/usr/local/bin/entrypoint.sh" ] && [ -x "/usr/local/bin/entrypoint.sh" ]; then
    echo "✓ Entrypoint script exists and is executable"
else
    echo "✗ Entrypoint script not found or not executable"
    exit 1
fi

# Test that Koji web tools are available after entrypoint runs
if command -v koji-web >/dev/null 2>&1; then
    echo "✓ koji-web is available"
    koji-web --version
else
    echo "✗ koji-web not found"
    exit 1
fi

# Test that web configuration exists
if [ -f "/etc/koji-web/koji_web.conf" ]; then
    echo "✓ Web configuration exists"
    echo "Configuration contents:"
    cat /etc/koji-web/koji_web.conf
else
    echo "✗ Web configuration not found"
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

# Test that web keytab exists
if [ -f "/etc/krb5kdc/web.keytab" ]; then
    echo "✓ Web keytab exists"
    ls -la /etc/krb5kdc/web.keytab
else
    echo "✗ Web keytab not found"
    exit 1
fi

# Test that keytab service is accessible
if curl -f "${KEYTAB_SERVICE_URL:-http://keytabs.koji.box:80}/health" >/dev/null 2>&1; then
    echo "✓ Keytab service is accessible"
else
    echo "✗ Keytab service is not accessible"
    exit 1
fi

echo -e "\n✓ All koji-web entrypoint tests passed!"
