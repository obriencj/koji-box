#!/usr/bin/env bash

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}


log "Running configure.sh"
/app/configure.sh
log "✓ configure.sh completed"

# Run main function
log "Running startup.sh as koji user..."
su koji /app/startup.sh
log "✓ startup.sh completed"

log "Going idle..."
exec tail -f /dev/null

# The end.
