#!/bin/bash

# Orch Service Initialization Script
# Generates resource mapping from environment variables

set -e

echo "Starting Orch service initialization..."

echo "Generating kerberos configuration from environment variables..."
if ! envsubst < /app/krb5.conf.template > /etc/krb5.conf; then
    echo "ERROR: Failed to generate kerberos configuration"
    exit 1
fi
echo "✓ Kerberos configuration generated"

echo "Generating koji configuration from environment variables..."
if ! envsubst < /app/koji.conf.template > /etc/koji.conf; then
    echo "ERROR: Failed to generate koji configuration"
    exit 1
fi
echo "✓ Koji configuration generated"

# Generate resource mapping from template
echo "Generating resource mapping from environment variables..."
if ! envsubst < /app/resource_mapping.yaml.template > /app/resource_mapping.yaml; then
    echo "ERROR: Failed to generate resource mapping"
    exit 1
fi

echo "✓ Resource mapping generated"

# Validate generated mapping
echo "Validating resource mapping..."
if ! python -c "import yaml; yaml.safe_load(open('/app/resource_mapping.yaml'))" 2>/dev/null; then
    echo "ERROR: Generated resource mapping is not valid YAML"
    exit 1
fi

echo "✓ Resource mapping validated"

# Create necessary directories
mkdir -p /mnt/data/keytabs /mnt/data/certs /mnt/data/logs

echo "✓ Directories created"

echo "Orch service initialization complete"

exec gunicorn -b 0.0.0.0:5000 app:app

# The end.
