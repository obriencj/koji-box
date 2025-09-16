#!/usr/bin/env bash

echo "Setting up Kerberos configuration..."
envsubst < /etc/krb5.conf.template > /etc/krb5.conf
echo "✓ Kerberos configuration created"

echo "Setting up Koji configuration..."
envsubst < /etc/koji.conf.template > /etc/koji.conf
echo "✓ Koji configuration created"

/app/orch.sh ca-install

# Run main function
echo "Running startup.sh as friend user..."
su friend /app/startup.sh

exec tail -f /dev/null

# The end.
