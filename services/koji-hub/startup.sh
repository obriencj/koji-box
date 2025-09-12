#! /bin/bash

set -e

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "Starting Koji Hub startup..."

INIT_DIR="${INIT_DIR:-/var/lib/koji-hub/hub-init.d}"   # place your init scripts here


# --- Run init scripts exactly once ---
run_init_scripts() {
    if [[ -d "$INIT_DIR" ]]; then
        log "Running init scripts in $INIT_DIR ..."
        # Sort to get a stable order (e.g., 00-foo.sh, 10-bar.sh)
        while IFS= read -r -d '' f; do
            if [[ -x "$f" ]]; then
                log "-> $f"
                # Let scripts exit with non-zero without killing the container:
                set +e
                "$f"
                rc=$?
                set -e
                log "<- $f (exit $rc)"
            else
                log "WARNING: $f is not executable"
            fi
        done < <(find "$INIT_DIR" -maxdepth 1 -type f -iname "*.sh" -print0 | sort -z)

        log "Init complete."
    else
        log "No init directory found at $INIT_DIR"
    fi
}


# Run initialization scripts
run_init_scripts

# The end.
