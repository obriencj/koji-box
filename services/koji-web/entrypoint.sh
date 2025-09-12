#!/bin/bash
# Koji Web Entrypoint Script
# Sets up Koji web and starts the service

set -e

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "Starting Koji Web entrypoint..."

# Check if Koji source is available
if [ ! -d "/mnt/koji/koji-src" ]; then
    log "Error: Koji source not found at /mnt/koji/koji-src"
    exit 1
fi

# Set up Kerberos configuration
log "Setting up Kerberos configuration..."
if ! envsubst < /app/krb5.conf.template > /etc/krb5.conf; then
    log "Error: Failed to generate Kerberos configuration"
    exit 1
fi
log "✓ Kerberos configuration created"

# Fetch web keytab from keytab service
log "Fetching web keytab..."
KEYTAB_SERVICE_URL="${KEYTAB_SERVICE_URL:-http://keytabs.koji.box:80}"
WEB_PRINCIPAL="http/koji-web.koji.box@${KRB5_REALM:-KOJI.BOX}"

# URL encode the principal name
WEB_PRINCIPAL_ENCODED=$(echo "http/koji-web.koji.box" | sed 's|/|%2F|g')

if ! curl -f -o /etc/krb5kdc/web.keytab "${KEYTAB_SERVICE_URL}/api/v1/principal/${WEB_PRINCIPAL_ENCODED}"; then
    log "Error: Failed to fetch web keytab from keytab service"
    exit 1
fi

# Test the keytab
if ! kinit -kt /etc/krb5kdc/web.keytab "${WEB_PRINCIPAL}"; then
    log "Error: Failed to authenticate with web keytab"
    exit 1
fi

log "✓ Web keytab fetched and authenticated"

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
KOJI_WEB_CONFIG="/etc/koji-web/koji_web.conf"
mkdir -p "$(dirname "$KOJI_WEB_CONFIG")"

# Create basic koji web configuration
cat > "$KOJI_WEB_CONFIG" << EOF
[koji_web]
# Koji Web Configuration
ServerName = ${KOJI_WEB_HOST:-koji-web}.koji.box
ServerAlias = ${KOJI_WEB_HOST:-koji-web}

# Hub configuration
KojiHubURL = http://${KOJI_HUB_HOST:-koji-hub}:${KOJI_HUB_PORT:-8080}/kojihub

# Authentication
AuthType = gssapi
LoginCreatesUser = On
KerberosServicePrincipal = ${WEB_PRINCIPAL}
KerberosKeytab = /etc/krb5kdc/web.keytab

# Logging
LogLevel = ${KOJI_LOG_LEVEL:-INFO}
LogFile = ${KOJI_WEB_LOG_FILE:-/var/log/koji-web/web.log}

# Web interface
WebURL = http://${KOJI_WEB_HOST:-koji-web}:${KOJI_WEB_PORT:-8080}/koji
TopURL = ${KOJI_TOP_URL:-http://nginx:80/kojifiles}
TopDir = ${KOJI_TOP_DIR:-/mnt/koji}

# Build system
BuildRootTimeout = ${KOJI_BUILD_ROOT_TIMEOUT:-3600}
MaxBuildsPerHost = ${KOJI_MAX_BUILDS_PER_HOST:-2}
EOF

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
