#!/bin/bash

# Orch Service Initialization Script
# Generates resource mapping from environment variables

set -e

echo "Starting Orch service initialization..."

# Generate resource mapping from template
echo "Generating resource mapping from environment variables..."
if ! envsubst < /app/templates/resource_mapping.yaml.template > /app/resource_mapping.yaml; then
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

gunicorn -b 0.0.0.0:5000 app:app

# The end.
