#!/usr/bin/env bash

echo "Setting up Kerberos configuration..."
envsubst < /etc/krb5.conf.template > /etc/krb5.conf
echo "✓ Kerberos configuration created"

echo "Setting up Koji configuration..."
envsubst < /etc/koji.conf.template > /etc/koji.conf
echo "✓ Koji configuration created"

/app/orch.sh ca-install
export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

# Run main function
echo "Running startup.sh as friend user..."
su friend /app/startup.sh

exec tail -f /dev/null

# The end.
