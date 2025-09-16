#!/usr/bin/env bash


log "Running configure.sh"
/app/configure.sh
log "✓ configure.sh completed"

# Run main function
echo "Running startup.sh as koji user..."
su koji /app/startup.sh

exec tail -f /dev/null

# The end.
