#!/bin/bash
"""
Koji Worker Service
Build worker for Koji build system
"""

set -euo pipefail

# Configure logging function
log() {
    local level="$1"
    shift
    echo "$(date '+%Y-%m-%d %H:%M:%S') - koji-worker - $level - $*"
}

log_info() {
    log "INFO" "$@"
}

log_error() {
    log "ERROR" "$@"
}

install_koji() {
    """Install Koji from source"""
    local koji_src="/mnt/koji/koji-src"

    if [[ ! -d "$koji_src" ]]; then
        log_error "Koji source not found at /mnt/koji/koji-src"
        return 1
    fi

    # Install Koji worker
    log_info "Installing Koji worker..."

    if ! (cd "$koji_src/builder" && python setup.py install); then
        log_error "Failed to install Koji worker"
        return 1
    fi

    log_info "Koji worker installation completed"
    return 0
}

setup_worker() {
    """Setup worker configuration"""
    log_info "Setting up worker configuration..."

    # Create worker configuration directory if it doesn't exist
    mkdir -p /etc/koji-worker

    # Create worker configuration
    cat > /etc/koji-worker/worker.conf << 'EOF'
[koji]
server = https://koji-hub.koji.box/kojihub
weburl = https://koji.box/
topurl = https://koji.box/kojifiles

[builder]
workdir = /var/lib/koji-worker
mockdir = /var/lib/mock
mockuser = koji
mockgroup = koji
mockhost = x86_64
mockarch = x86_64
mocktarget = x86_64
EOF

    if [[ $? -eq 0 ]]; then
        log_info "Worker configuration created"
        return 0
    else
        log_error "Failed to setup worker"
        return 1
    fi
}

start_worker() {
    """Start the Koji worker service"""
    log_info "Starting Koji worker service..."

    # Start worker daemon
    if ! koji-worker --config /etc/koji-worker/worker.conf --daemon; then
        log_error "Failed to start worker service"
        exit 1
    fi
}

signal_handler() {
    """Handle shutdown signals"""
    log_info "Received shutdown signal, stopping worker..."
    exit 0
}

# Main execution
main() {
    log_info "Starting Koji Worker Service"

    # Setup signal handlers
    trap signal_handler SIGTERM SIGINT

    log "Running configure.sh"
    /app/configure.sh
    log "✓ configure.sh completed"

    # Install Koji if not already installed
    if ! install_koji; then
        log_error "Failed to install Koji worker"
        exit 1
    fi

    # Setup worker
    if ! setup_worker; then
        log_error "Failed to setup worker"
        exit 1
    fi

    # Start worker service
    start_worker
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi

# The end.
