#!/bin/bash
# Setup script for Koji Hub

set -e

echo "Setting up Koji Hub..."

# Wait for database to be ready
echo "Waiting for database to be ready..."
while ! pg_isready -h postgres -p 5432 -U koji; do
    echo "Database not ready, waiting..."
    sleep 2
done

echo "Database is ready"

# Initialize database schema
echo "Initializing database schema..."
koji-hub --config /etc/koji-hub/hub.conf --init-db

# Create admin user
echo "Creating admin user..."
koji add-user admin || true
koji grant-permission admin || true

echo "Koji Hub setup completed"
