#!/bin/bash

# Koji Worker Service
# Build worker for Koji build system

set -euo pipefail

# Configure logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $*"
}

log "Running configure.sh"
/app/configure.sh
log "✓ configure.sh completed"


# This value is used to fetch the keytab from the orch service and to set the
# keytab path in the kojid.conf template.
export KOJID_KEYTAB=/app/kojid.keytab

log "Registering worker with orch..."
if ! /app/orch.sh checkout ${KOJI_WORKER_KEYTAB} ${KOJID_KEYTAB} ; then
    log "Failed to checkout keytab"
    exit 1
fi
export KOJID_PRINC=$(klist -k ${KOJID_KEYTAB} | tail -n 1 | awk '{print $2}')

log "Granted principal: ${KOJID_PRINC}"
log "✓ worker registered with orch"

log "Generating kojid.conf"
mkdir -p /etc/kojid
envsubst < /app/kojid.conf.template > /etc/kojid/kojid.conf
log "✓ kojid.conf generated"

mkdir -p /etc/mock/koji /var/lib/mock /var/tmp/koji

log "exec'ing kojid"
exec /app/kojid --fg ${BUILDER_ARGS}

# The end.
