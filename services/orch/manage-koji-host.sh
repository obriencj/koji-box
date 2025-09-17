#!/bin/bash

# Manage Koji Host Script
# Placeholder for Koji host management functionality

set -e

function setup_kinit() {

    export KRB5_CCNAME="FILE:$(mktemp -d)/krb5cc_orch"

    if [ -f /app/orch.keytab ]; then
        echo "✓ Keytab already exists"
    else
        /app/orch.sh ${ORCH_KEYTAB} /app/orch.keytab
    fi

    kinit -k -t /app/orch.keytab ${ORCH_PRINC}
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
    local FULL_PRINCIPAL_NAME="$2"
    local WORKER_ARCH="$3-x86_64"

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

    # we'll need to install the CA bundle as well.
    /app/orch.sh ca-install

    echo "Managing Koji host: $WORKER_NAME"

    local HOSTINFO=$(koji --noauth call --json-output getUser "${FULL_PRINCIPAL_NAME}")
    if [ "$HOSTINFO" == "null" ]; then
        koji add-host "${WORKER_NAME}" "${WORKER_ARCH}" --krb-principal "${FULL_PRINCIPAL_NAME}"
    fi

    echo "✓ Koji host $WORKER_NAME managed successfully"

    cleanup_kinit
}

main "$@"

# The end.
