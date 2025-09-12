#!/bin/bash
# Koji Host Management Script
# Manages Koji hosts with proper admin authentication

set -e

# Configuration
KRB5_REALM="${KRB5_REALM:-KOJI.BOX}"
KOJI_HUB_URL="${KOJI_HUB_URL:-http://koji.box/kojihub}"
KEYTAB_SERVICE_URL="${KEYTAB_SERVICE_URL:-http://keytabs.koji.box:5000}"
KOJI_ADMIN_PRINCIPAL="${KOJI_ADMIN_PRINCIPAL:-koji-admin@${KRB5_REALM}}"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >&2
}

# Function to clean up old temporary files
cleanup_old_files() {
    # Remove temporary keytab files older than 1 hour
    find /tmp -name "admin-*-*.keytab" -mmin +60 -delete 2>/dev/null || true
    # Remove temporary credential cache files older than 1 hour
    find /tmp -name "krb5cc-*-*" -mmin +60 -delete 2>/dev/null || true
}

# Function to set up Kerberos environment
setup_krb() {
    log "Setting up Kerberos environment..."
    
    # Check for existing admin keytab
    ADMIN_KEYTAB_CACHE="/tmp/admin.keytab"
    if [ ! -f "$ADMIN_KEYTAB_CACHE" ] || [ ! -s "$ADMIN_KEYTAB_CACHE" ]; then
        log "Admin keytab not found, fetching from keytab service..."
        if ! curl -f -s -o "$ADMIN_KEYTAB_CACHE" "${KEYTAB_SERVICE_URL}/api/v1/principal/${KOJI_ADMIN_PRINCIPAL}"; then
            log "Error: Failed to get admin keytab from keytab service"
            return 1
        fi
        log "✓ Admin keytab fetched and cached"
    else
        log "Using cached admin keytab"
    fi
    
    # Create a unique temporary credential cache file
    KRB5CCNAME="/tmp/krb5cc-$$-$(date +%s)"
    export KRB5CCNAME
    
    # Set up Kerberos configuration
    export KRB5_CONFIG="/etc/krb5.conf"
    
    # Authenticate using the admin keytab
    if ! kinit -k -t "$ADMIN_KEYTAB_CACHE" "$KOJI_ADMIN_PRINCIPAL"; then
        log "Error: Failed to authenticate as admin using kinit"
        return 1
    fi
    
    log "✓ Successfully authenticated as admin with credential cache: $KRB5CCNAME"
    return 0
}

# Function to tear down Kerberos environment
teardown_krb() {
    # Only run if we have a credential cache file
    if [ -n "$KRB5CCNAME" ] && [ -f "$KRB5CCNAME" ]; then
        log "Tearing down Kerberos environment..."
        
        # Destroy Kerberos tickets
        kdestroy 2>/dev/null || true
        
        # Clean up temporary credential cache file
        rm -f "$KRB5CCNAME"
        
        log "✓ Kerberos environment cleaned up"
    fi

    # Clean up old temporary files
    cleanup_old_files
}

# Function to show usage
usage() {
    echo "Usage: $0 <principal_name>"
    echo "  principal_name: The principal name to check/create as a Koji host"
    echo ""
    echo "This script will:"
    echo "  1. Get the admin@${KRB5_REALM} keytab from the keytab service"
    echo "  2. Authenticate as admin using kinit"
    echo "  3. Check if a Koji host exists with the given principal"
    echo "  4. Create the host if it doesn't exist"
    exit 1
}

# Check if principal name is provided
if [ $# -ne 1 ]; then
    log "Error: Principal name is required"
    usage
fi

PRINCIPAL_NAME="$1"

# Validate principal name
if [[ "$PRINCIPAL_NAME" =~ [^a-zA-Z0-9._-/@] ]]; then
    log "Error: Invalid principal name '$PRINCIPAL_NAME'. Only alphanumeric characters, dots, underscores, and hyphens are allowed."
    exit 1
fi

log "Starting Koji host management for principal: $PRINCIPAL_NAME"

# Step 1: Set up Kerberos environment
log "Setting up Kerberos environment..."
if ! setup_krb; then
    log "Error: Failed to set up Kerberos environment"
    teardown_krb
    exit 1
else
    # Set up trap to ensure cleanup on exit
    trap 'teardown_krb' EXIT INT TERM
fi

# Step 2: Check if Koji host exists
log "Step 2: Checking if Koji host exists for principal: $PRINCIPAL_NAME"

# Set up Koji configuration
KOJI_CONFIG="/etc/koji/koji.conf"
mkdir -p "$(dirname "$KOJI_CONFIG")"

# Use shared configuration template with environment variables
export KRB5_PRINCIPAL="${ADMIN_PRINCIPAL}"
export KRB5_KEYTAB="${ADMIN_KEYTAB}"
envsubst < /app/koji.conf.template > "$KOJI_CONFIG"

# Check if host exists
if koji list-hosts --name "$PRINCIPAL_NAME" >/dev/null 2>&1; then
    log "✓ Koji host '$PRINCIPAL_NAME' already exists"
    rm -f "$ADMIN_KEYTAB"
    exit 0
fi

log "Host '$PRINCIPAL_NAME' does not exist, will create it"

# Step 3: Create the Koji host
log "Step 3: Creating Koji host for principal: $PRINCIPAL_NAME"

# Determine the full principal name for the host
HOST_PRINCIPAL="koji/${PRINCIPAL_NAME}.koji.box@${KRB5_REALM}"

# Create the host with the principal
if koji add-host "$PRINCIPAL_NAME" --krb-principal "$HOST_PRINCIPAL" --capacity 2; then
    log "✓ Successfully created Koji host '$PRINCIPAL_NAME' with principal '$HOST_PRINCIPAL'"
else
    log "Error: Failed to create Koji host '$PRINCIPAL_NAME'"
    teardown_krb
    exit 1
fi

log "✓ Koji host management completed successfully for principal: $PRINCIPAL_NAME"
