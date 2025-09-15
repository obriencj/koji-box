#!/bin/bash

# Fetch client principal from orch service and kinit
echo "Fetching client principal from orch service..."

# Configuration
ORCH_SERVICE_URL="${ORCH_SERVICE_URL:-http://orch.koji.box:5000}"

CLIENT_KEYTAB_PATH="$HOME/friend.keytab"
ADMIN_KEYTAB_PATH="$HOME/superfriend.keytab"

# Fetch keytab from orch service using admin keytab (since no client-specific keytab exists)
echo "Fetching keytab for principal: $KOJI_CLIENT_PRINC"
if ! /app/orch.sh checkout ${KOJI_CLIENT_KEYTAB} "$CLIENT_KEYTAB_PATH"; then
    echo "ERROR: Failed to fetch keytab for $KOJI_CLIENT_PRINC"
    exit 1
fi

echo "Fetching keytab for principal: $KOJI_CLIENT_ADMIN_PRINC"
if ! /app/orch.sh checkout ${KOJI_CLIENT_ADMIN_KEYTAB} "$ADMIN_KEYTAB_PATH"; then
    echo "ERROR: Failed to fetch keytab for $KOJI_CLIENT_ADMIN_PRINC"
    exit 1
fi

# Set proper permissions on keytab
chmod 600 "$CLIENT_KEYTAB_PATH"
chmod 600 "$ADMIN_KEYTAB_PATH"

# Perform kinit with the keytab
echo "Performing kinit with keytab..."
if kinit -kt "$CLIENT_KEYTAB_PATH" "${KOJI_CLIENT_PRINC}"; then
    echo "Successfully authenticated as $KOJI_CLIENT_PRINC"
else
    echo "ERROR: Failed to authenticate with keytab"
    exit 1
fi

echo "Performing kinit with admin keytab..."
if kinit -kt "$ADMIN_KEYTAB_PATH" "${KOJI_CLIENT_ADMIN_PRINC}"; then
    echo "Successfully authenticated as $KOJI_CLIENT_ADMIN_PRINC"
else
    echo "ERROR: Failed to authenticate with admin keytab"
    exit 1
fi

echo "Client authentication complete"

# The end.
