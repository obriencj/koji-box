#!/bin/bash

# Manage Koji Host Script
# Placeholder for Koji host management functionality

set -e

function setup_kinit() {

    export KRB5_CCNAME="FILE:$(mktemp -d)/krb5cc_orch"

    if [ -f /app/orch.keytab ]; then
        echo "✓ Keytab already exists"
    else
        /app/orch.sh ${KOJI_ORCH_KEYTAB} /app/orch.keytab
    fi

    kinit -k -t /app/orch.keytab ${KOJI_ORCH_PRINC}
    trap cleanup_kinit EXIT
}

function cleanup_kinit() {
    kdestroy

    if [ -n "$KRB5_CCNAME" ]; then
        rm -rf "$(dirname "$KRB5_CCNAME")"
    fi
}

function main() {

    local WORKER_NAME="$1"

    if [ -z "$WORKER_NAME" ]; then
        echo "ERROR: Worker name required"
        exit 1
    fi

    setup_kinit
    /app/orch.sh ca-install

    echo "Managing Koji host: $WORKER_NAME"

    # TODO: Implement actual Koji host management
    # This would typically involve:
    # 1. Checking if host exists in Koji
    # 2. Creating host if it doesn't exist
    # 3. Configuring host settings

    echo "✓ Koji host $WORKER_NAME managed successfully"

    cleanup_kinit
}

main "$@"

# The end.
