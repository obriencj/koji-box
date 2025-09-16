#!/bin/bash
# Koji Web Entrypoint Script
# Sets up Koji web and starts the service

set -e

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "Starting Koji Web entrypoint..."

log "Running configure.sh"
/app/configure.sh
log "✓ configure.sh completed"

# Install Koji web from source
log "Installing Koji web from source..."
cd /mnt/koji/koji-src/web

if ! python setup.py install; then
    log "Error: Failed to install Koji web"
    exit 1
fi

log "✓ Koji web installation completed"

# Verify Koji web installation
if ! command -v koji-web >/dev/null 2>&1; then
    log "Error: koji-web not found after installation"
    exit 1
fi

log "✓ Koji web tools verified"

# Set up Koji web configuration
log "Setting up Koji web configuration..."
envsubst < /app/koji_web.conf.template > /etc/koji-web/koji_web.conf
log "✓ Koji web configuration created"

# Set proper ownership
log "Setting up file ownership..."
chown -R koji:koji /etc/koji-web /var/log/koji-web /var/lib/koji-web /usr/share/koji-web 2>/dev/null || true
log "✓ File ownership set"

# Start the Koji web service
log "Starting Koji web service..."
exec gunicorn --bind 0.0.0.0:8080 \
    --workers 2 \
    --timeout 300 \
    --access-logfile - \
    --error-logfile - \
    koji.web:app

# The end.
