#!/bin/bash
# Keytab Service Entrypoint
# Sets up Koji client and starts the Flask application

set -e

KOJI_SRC_DIR="${KOJI_SRC_DIR:-/mnt/koji-src}"

echo "Starting Keytab Service entrypoint..."

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "Setting up Koji configuration..."

# Generate Koji configuration
mkdir -p ~/.koji
envsubst < /app/koji.conf.template > ~/.koji/config

log "✓ Koji configuration created"

# Set up Kerberos configuration
log "Setting up Kerberos configuration..."

# Use shared configuration template
export KRB5_CONFIG="$HOME/.krb5.conf"
envsubst < /app/krb5.conf.template > "$KRB5_CONFIG"

log "✓ Kerberos configuration created"

# Start the Flask application
log "Starting Flask application..."
exec gunicorn -b 0.0.0.0:5000 -w 4 app:app

# The end.
