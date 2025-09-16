#!/bin/bash

# Fetch client principal from orch service and kinit
echo "Fetching client principal from orch service..."

CLIENT_KEYTAB_PATH="$HOME/friend.keytab"
ADMIN_KEYTAB_PATH="$HOME/superfriend.keytab"

# Fetch keytab from orch service using admin keytab (since no client-specific keytab exists)
/app/orch.sh checkout "${KOJI_CLIENT_KEYTAB}" "$CLIENT_KEYTAB_PATH"
/app/orch.sh checkout "${KOJI_CLIENT_ADMIN_KEYTAB}" "$ADMIN_KEYTAB_PATH"

# Set proper permissions on keytab
chmod 600 "$CLIENT_KEYTAB_PATH" "$ADMIN_KEYTAB_PATH"

# Perform kinit with the keytab
echo "Performing kinit with keytab..."
if kinit -kt "$CLIENT_KEYTAB_PATH" "${KOJI_CLIENT_PRINC}"; then
    echo "Successfully authenticated as $KOJI_CLIENT_PRINC"
else
    echo "ERROR: Failed to authenticate with keytab"
    exit 1
fi

echo "Client authentication complete"

# The end.
