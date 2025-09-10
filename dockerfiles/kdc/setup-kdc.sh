#!/bin/bash
# KDC setup script

set -e

echo "Setting up KDC for realm KOJI.BOX..."

# Create the realm database
echo "Creating realm database..."
kdb5_util create -r KOJI.BOX -s -P master_password

# Start KDC
echo "Starting KDC..."
krb5kdc

# Start admin server
echo "Starting admin server..."
kadmind

# Wait for services to be ready
sleep 5

# Create admin user
echo "Creating admin user..."
kadmin.local -q "addprinc -pw admin_password admin/admin@KOJI.BOX" || echo "Admin user already exists"

# Create service principals
echo "Creating service principals..."

# Hub service principal
kadmin.local -q "addprinc -randkey hub/koji-hub.koji.box@KOJI.BOX" || echo "Hub principal already exists"

# Web service principal
kadmin.local -q "addprinc -randkey http/koji-web.koji.box@KOJI.BOX" || echo "Web principal already exists"

# Worker service principal
kadmin.local -q "addprinc -randkey koji/koji-worker-1.koji.box@KOJI.BOX" || echo "Worker principal already exists"

# Create keytabs for services
echo "Creating keytabs..."

# Hub keytab
kadmin.local -q "ktadd -k /etc/krb5kdc/hub.keytab hub/koji-hub.koji.box@KOJI.BOX" || echo "Hub keytab already exists"

# Web keytab
kadmin.local -q "ktadd -k /etc/krb5kdc/web.keytab http/koji-web.koji.box@KOJI.BOX" || echo "Web keytab already exists"

# Worker keytab
kadmin.local -q "ktadd -k /etc/krb5kdc/worker.keytab koji/koji-worker-1.koji.box@KOJI.BOX" || echo "Worker keytab already exists"

# Set proper permissions
chmod 644 /etc/krb5kdc/*.keytab

echo "KDC setup completed successfully"
