#!/bin/bash

set -euo pipefail

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ANSIBLE-CONFIGURATOR] $1"
}

# Function to wait for koji-hub to be ready
wait_for_koji_hub() {
    local max_attempts=60
    local attempt=1

    log "Waiting for Koji Hub to be ready..."

    while [ $attempt -le $max_attempts ]; do
        if koji --noauth version >/dev/null 2>&1; then
            log "✓ Koji Hub is ready"
            return 0
        fi

        log "Attempt $attempt/$max_attempts: Koji Hub not ready yet, waiting 5s..."
        sleep 5
        ((attempt++))
    done

    log "ERROR: Koji Hub failed to become ready after $max_attempts attempts"
    exit 1
}

# Function to authenticate with Kerberos
authenticate() {
    log "Authenticating with Kerberos..."

    if [[ ! -f "/etc/koji-hub/admin.keytab" ]]; then
        log "ERROR: Admin keytab not found at /etc/koji-hub/admin.keytab"
        log "Make sure the keytab volume is properly mounted"
        exit 1
    fi

    if kinit -kt /etc/koji-hub/admin.keytab "${KOJI_ADMIN_PRINC}"; then
        log "✓ Successfully authenticated as ${KOJI_ADMIN_PRINC}"
    else
        log "ERROR: Failed to authenticate with admin keytab"
        exit 1
    fi

    # Verify authentication works with koji
    if koji hello >/dev/null 2>&1; then
        log "✓ Koji authentication verified"
    else
        log "ERROR: Koji authentication failed"
        exit 1
    fi
}

# Function to validate configuration files
validate_config() {
    log "Validating configuration files..."

    if [[ ! -d "/ansible-configs" ]]; then
        log "No configuration directory found at /ansible-configs"
        log "Creating minimal example configuration..."
        return 0
    fi

    # Run validation using our built-in script
    if python3 /ansible/validation/validate_config.py --config-dir /ansible-configs; then
        log "✓ Configuration validation passed"
    else
        log "⚠ Configuration validation failed"
        exit 1
    fi
}

# Function to run ansible playbooks
run_ansible() {
    log "Starting Ansible configuration..."

    cd /ansible

    # Run the main playbook (now baked into container)
    if ansible-playbook site.yml; then
        log "✓ Ansible configuration completed successfully"
    else
        log "⚠ Ansible configuration failed (exit code: $?)"
        exit 1
    fi
}

# Main execution
main() {
    log "Starting Ansible Configurator..."

    # Wait for koji-hub to be ready
    wait_for_koji_hub

    # Authenticate with Kerberos
    authenticate

    # Validate configuration files
    validate_config

    # Run ansible configuration
    run_ansible

    log "✓ Ansible Configurator completed successfully"
}

# Execute main function
main "$@"
