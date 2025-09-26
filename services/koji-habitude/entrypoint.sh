$!/usr/bin/env bash

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')]" "$@"
}


log "Running configure.sh"
/app/configure.sh
log "✓ configure.sh completed"


log "Exec'ing startup"
exec su koji /app/startup.sh


# The end.
