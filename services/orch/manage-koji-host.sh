#!/bin/bash

# Manage Koji Host Script
# Placeholder for Koji host management functionality

set -e

function log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $*"
}


function setup_kinit() {
    local KINIT_LOCK=/tmp/orch-kinit.lock
    log "Setting up kinit in order to manage Koji host"

    set +e
    flock -e "$KINIT_LOCK"
    if klist >/dev/null 2>&1 ; then
        kinit -R -kt /app/orch.keytab  ${ORCH_PRINC}
    else
        kinit -kt /app/orch.keytab ${ORCH_PRINC}
    fi
    flock -u "$KINIT_LOCK"
    set -e

    log "✓ kinit setup"
}


function main() {

    local WORKER_NAME="$1"
    local FULL_PRINCIPAL_NAME="$2"
    local WORKER_ARCH="${3:-x86_64}"

    log "Managing Koji host: $WORKER_NAME"
    log "Full principal name: $FULL_PRINCIPAL_NAME"
    log "Host arch: $WORKER_ARCH"

    if [ -z "$WORKER_NAME" ] ; then
        echo "ERROR: Worker name required"
        exit 1
    fi

    if [ -z "$FULL_PRINCIPAL_NAME" ] ; then
        echo "ERROR: Full principal name required"
        exit 1
    fi

    # we ourselves need to be authenticated to the KDC to be able to manage the host, using the koji client.

    log "Checking if host exists in Koji"
    local HOSTINFO=$(koji --noauth call --json-output getUser "${FULL_PRINCIPAL_NAME}")

    if [ "$HOSTINFO" == "null" ] ; then
        setup_kinit

        log "Host does not exist in Koji, adding it"
        koji add-host "${WORKER_NAME}" "${WORKER_ARCH}" --krb-principal "${FULL_PRINCIPAL_NAME}"

    elif jq -e '.usertype == 0' <<< "$HOSTINFO" >/dev/null ; then
        setup_kinit

        log "Host exists but as a user. Changing to host"

        log "Ensuring name consistency"
        koji edit-user "${FULL_PRINCIPAL_NAME}" --rename "${WORKER_NAME}"

        log "Forcing host config association to update usertype"
        koji add-host "${WORKER_NAME}" "${WORKER_ARCH}" --force

        HOSTINFO=$(koji --noauth call --json-output getUser "${FULL_PRINCIPAL_NAME}")
        if jq -e '.usertype == 0' <<< "$HOSTINFO" >/dev/null ; then
            log "Need to manually change the host's usertype to 1"
            exit 1
        fi

    elif jq -e '.usertype == 1' <<< "$HOSTINFO" >/dev/null ; then
        log "Host already exists in Koji, skipping"

    else
        log "Host usertype is invalid!"
        exit 1
    fi

    koji userinfo "${FULL_PRINCIPAL_NAME}"
    koji hostinfo "${WORKER_NAME}"

    log "✓ Koji host $WORKER_NAME managed successfully"
}


main "$@"


# The end.
