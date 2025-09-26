#!/bin/bash

# Fetch client principal from orch service and kinit
echo "Fetching client principal from orch service..."

KEYTAB_PATH="$HOME/habitude.keytab"

# Fetch keytab from orch service using admin keytab (since no client-specific keytab exists)
/app/orch.sh checkout "${KOJI_HABITUDE_KEYTAB}" "$KEYTAB_PATH"

# Set proper permissions on keytab
chmod 600 "$KEYTAB_PATH"

# Perform kinit with the keytab
echo "Performing kinit with keytab..."
if kinit -kt "$KEYTAB_PATH" "${KOJI_HABITUDE_PRINC}"; then
    echo "Successfully authenticated as $KOJI_HABITUDE_PRINC"
else
    echo "ERROR: Failed to authenticate with keytab"
    exit 1
fi

echo "Client authentication complete"

# The end.
