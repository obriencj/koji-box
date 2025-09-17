#!/bin/bash

# Manage Koji Host Script
# Placeholder for Koji host management functionality

set -e

function log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $*"
}

export KRB5_CCNAME="FILE:$(mktemp -d)/krb5cc_orch"


function setup_kinit() {
    log "Setting up kinit in order to manage Koji host"

    kinit -k -t /app/orch.keytab ${ORCH_PRINC}
    trap cleanup_kinit EXIT
    log "✓ kinit setup"
}

function cleanup_kinit() {
    log "Cleaning up kinit"
    kdestroy

    if [ -n "$KRB5_CCNAME" ]; then
        rm -rf "$(dirname "$KRB5_CCNAME")"
    fi
    log "✓ kinit cleaned up"
}

function main() {

    local WORKER_NAME="$1"
    local FULL_PRINCIPAL_NAME="$2"
    local WORKER_ARCH="$3-x86_64"

    log "Managing Koji host: $WORKER_NAME"
    log "Full principal name: $FULL_PRINCIPAL_NAME"
    log "Host arch: $WORKER_ARCH"

    if [ -z "$WORKER_NAME" ]; then
        echo "ERROR: Worker name required"
        exit 1
    fi

    if [ -z "$FULL_PRINCIPAL_NAME" ]; then
        echo "ERROR: Full principal name required"
        exit 1
    fi

    # we ourselves need to be authenticated to the KDC to be able to manage the host, using the koji client.
    setup_kinit

    log "Checking if host exists in Koji"
    local HOSTINFO=$(koji --noauth call --json-output getUser "${FULL_PRINCIPAL_NAME}")

    echo "HOSTINFO: "
    jq . <<< "$HOSTINFO"

    if [ "$HOSTINFO" == "null" ]; then
        log "Host does not exist in Koji, adding it"
        koji add-host "${WORKER_NAME}" "${WORKER_ARCH}" --krb-principal "${FULL_PRINCIPAL_NAME}"
    else
        log "Host already exists in Koji, skipping"
    fi

    koji hostinfo "${WORKER_NAME}"
    log "✓ Koji host $WORKER_NAME managed successfully"

    cleanup_kinit
}

main "$@"

# The end.
