#!/bin/bash

# Koji Hub Entrypoint Script
# Sets up Koji hub and starts the service

set -e

# --- Config (override with env) ---
KRB5_REALM=${KRB5_REALM:-KOJI.BOX}

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "Starting Koji Hub entrypoint..."

# Generate hub configuration from template
log "Generating Koji hub configuration..."
if ! envsubst < /app/hub.conf.template > /etc/koji-hub/hub.conf; then
    log "Error: Failed to generate hub configuration"
    exit 1
fi
log "✓ Koji hub configured"

# Generate apache configuration from template
log "Generating Apache configuration..."
if ! envsubst < /app/httpd.conf.template > /etc/koji-hub/httpd.conf; then
    log "Error: Failed to generate Apache configuration"
    exit 1
fi
cp -f /etc/koji-hub/httpd.conf /etc/httpd/conf.d/kojihub.conf
log "✓ Apache configured"

# Generate Koji client configuration from template
log "Generating Koji client configuration..."
if ! envsubst < /app/koji.conf.template > /etc/koji.conf; then
    log "Error: Failed to generate Koji client configuration"
    exit 1
fi
log "✓ Koji client configured"

# Set up Kerberos configuration
log "Generating Kerberos configuration..."
if ! envsubst < /app/krb5.conf.template > /etc/krb5.conf; then
    log "Error: Failed to generate Kerberos configuration"
    exit 1
fi
log "✓ Kerberos configured"

/app/orch.sh ca-install

# Fetching hub keytabs using orch.sh
log "Fetching hub keytabs..."
/app/orch.sh checkout ${KOJI_HUB_KEYTAB} /etc/koji-hub/koji-hub.keytab
/app/orch.sh checkout ${KOJI_NGINX_KEYTAB} /etc/koji-hub/nginx.keytab

# Fetching admin keytab
/app/orch.sh checkout ${KOJI_ADMIN_KEYTAB} /etc/koji-hub/admin.keytab


log "Creating SSL certificate..."
/app/orch.sh checkout ${KOJI_HUB_CERT} /etc/pki/tls/certs/localhost.crt
/app/orch.sh checkout ${KOJI_HUB_KEY} /etc/pki/tls/private/localhost.key
log "✓ SSL certificate created"

/sbin/httpd -DFOREGROUND &
export HUB_PID=$!
log "✓ Koji hub service started (pid: $HUB_PID)"

# Start the Koji hub service
log "Starting startup.sh"
su koji -c /usr/local/bin/startup.sh

wait $HUB_PID

# The end.
