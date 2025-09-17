#!/bin/bash

# Koji Hub Entrypoint Script
# Sets up Koji hub and starts the service

set -e


# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}
log "Starting Koji Hub entrypoint..."


log "Ensuring /mnt/koji consistency..."
mkdir -p /mnt/koji/repos /mnt/koji/packages /mnt/koji/builds /mnt/koji/tasks /mnt/koji/scratch
chmod -R a+rX /mnt/koji/
ls -al /mnt/koji/


log "Running configure.sh"
/app/configure.sh
log "✓ configure.sh completed"


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

log "Updating Apache to run as koji user"
sed -r 's,^(User|Group) apache,\1 koji,g' -i /etc/httpd/conf/httpd.conf

log "✓ Apache configured"


# Fetching hub keytab claims
log "Fetching hub keytabs..."
/app/orch.sh checkout ${KOJI_HUB_KEYTAB} /etc/koji-hub/koji-hub.keytab
/app/orch.sh checkout ${KOJI_NGINX_KEYTAB} /etc/koji-hub/nginx.keytab

# Fetching admin keytab claim
log "Fetching admin keytab..."
/app/orch.sh checkout ${KOJI_ADMIN_KEYTAB} /etc/koji-hub/admin.keytab

# Fetching SSL claims
log "Fetching SSL certificate..."
/app/orch.sh checkout ${KOJI_HUB_CERT} /etc/pki/tls/certs/localhost.crt
/app/orch.sh checkout ${KOJI_HUB_KEY} /etc/pki/tls/private/localhost.key

log "Starting Koji hub service"
/sbin/httpd -DFOREGROUND &
export HUB_PID=$!
log "✓ Koji hub service started (pid: $HUB_PID)"

log "Launching startup scripts"
su koji -c /app/startup.sh
log "✓ startup scripts completed"

log "Rejoining process $HUB_PID"
wait "$HUB_PID"

# The end.
