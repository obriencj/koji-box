#!/bin/bash

# Fetch client principal from keytab service and kinit
echo "Fetching client principal from keytab service..."

# Configuration
KEYTAB_SERVICE_URL="${KEYTAB_SERVICE_URL:-http://keytabs.koji.box:5000}"
KRB5_REALM="${KRB5_REALM:-KOJI.BOX}"
CLIENT_PRINCIPAL="${CLIENT_PRINCIPAL:-friend@${KRB5_REALM}}"
KEYTAB_PATH="$HOME/.client.keytab"

echo "Setting up Kerberos configuration..."

export KRB5_CONFIG="${KRB5_CONFIG:-$HOME/.krb5.conf}"
envsubst < /etc/krb5.conf.template > "$KRB5_CONFIG"

echo "✓ Kerberos configuration created"

# Fetch keytab from keytab service
echo "Fetching keytab for principal: $CLIENT_PRINCIPAL"
if ! curl "${KEYTAB_SERVICE_URL}/api/v1/principal/${CLIENT_PRINCIPAL}" -o "$KEYTAB_PATH"; then
    echo "ERROR: Failed to fetch keytab for $CLIENT_PRINCIPAL"
    exit 1
fi

# Set proper permissions on keytab
chmod 600 "$KEYTAB_PATH"

# Perform kinit with the keytab
echo "Performing kinit with keytab..."
if kinit -kt "$KEYTAB_PATH" "${CLIENT_PRINCIPAL}"; then
    echo "Successfully authenticated as $CLIENT_PRINCIPAL"
    
    # Verify the ticket
    echo "Current Kerberos tickets:"
    klist
else
    echo "ERROR: Failed to authenticate with keytab"
    exit 1
fi

echo "Client authentication complete"

# The end.
