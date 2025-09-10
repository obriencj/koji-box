#!/bin/bash
# Cleanup script for Boxed Koji

set -e

echo "Cleaning up Boxed Koji environment..."

# Stop all containers
echo "Stopping containers..."
podman-compose -f docker-compose.yml -p koji-boxed down || true

# Remove containers
echo "Removing containers..."
podman container prune -f || true

# Remove images
echo "Removing images..."
podman image prune -f || true

# Remove volumes
echo "Removing volumes..."
podman volume prune -f || true

# Remove networks
echo "Removing networks..."
podman network prune -f || true

# Clean up data directories
echo "Cleaning data directories..."
rm -rf data/postgres/*
rm -rf data/koji-storage/*
rm -rf data/logs/*

# Remove Koji source
echo "Removing Koji source..."
rm -rf koji-src

echo "Cleanup completed"
