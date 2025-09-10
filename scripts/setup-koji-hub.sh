#!/bin/bash
# Koji Hub setup script

set -e

echo "Setting up Koji Hub..."

# Wait for database to be ready
echo "Waiting for database to be ready..."
while ! pg_isready -h postgres -p 5432 -U koji; do
    echo "Database not ready, waiting..."
    sleep 2
done

echo "Database is ready"

# Initialize Koji hub database
echo "Initializing Koji hub database..."
koji-hub --config /etc/koji-hub/hub.conf --init-db

# Create admin user if it doesn't exist
echo "Creating admin user..."
koji add-user admin || echo "Admin user already exists"

# Grant admin permissions
echo "Granting admin permissions..."
koji grant-permission admin || echo "Admin permissions already granted"

# Create build targets
echo "Creating build targets..."
koji add-tag dist-foo || echo "Tag dist-foo already exists"
koji add-tag --parent dist-foo dist-foo-build || echo "Tag dist-foo-build already exists"
koji add-target dist-foo dist-foo-build || echo "Target dist-foo already exists"

# Add build host
echo "Adding build host..."
koji add-host dist-foo-build x86_64 || echo "Build host already exists"

echo "Koji Hub setup completed"
