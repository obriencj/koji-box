#!/bin/bash
# KDC service startup script

set -e

echo "Starting KDC service for realm KOJI.BOX..."

# Copy configuration files
cp /etc/krb5kdc/krb5.conf /etc/krb5.conf
cp /etc/krb5kdc/kdc.conf /var/lib/krb5kdc/kdc.conf
cp /etc/krb5kdc/kadm5.acl /var/lib/krb5kdc/kadm5.acl

# Run setup if database doesn't exist
if [ ! -f /var/lib/krb5kdc/principal ]; then
    echo "Running initial KDC setup..."
    /usr/local/bin/setup-kdc.sh
else
    echo "KDC database already exists, starting services..."

    # Start admin server
    kadmind

    # Start KDC
    krb5kdc -n
fi

# Keep the container running
echo "KDC services started, keeping container alive..."
tail -f /var/log/krb5kdc.log
