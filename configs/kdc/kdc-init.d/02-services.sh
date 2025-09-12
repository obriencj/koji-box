#! /bin/bash

# Create service principals
echo "Creating service principals..."

# Hub service principal
echo "Creating Koji Hub service principal..."
kadmin.local -q "addprinc -randkey hub/koji-hub.koji.box@KOJI.BOX" || echo "Hub principal already exists"
kadmin.local -q "ktadd -k /mnt/keytabs/koji-hub.keytab hub/koji-hub.koji.box@KOJI.BOX" || echo "Hub keytab already exists"

# Web service principal
echo "Creating Koji Web service principal..."
kadmin.local -q "addprinc -randkey http/koji-web.koji.box@KOJI.BOX" || echo "Web principal already exists"
kadmin.local -q "ktadd -k /mnt/keytabs/koji-web.keytab http/koji-web.koji.box@KOJI.BOX" || echo "Web keytab already exists"

# Worker service principal
echo "Creating Koji Worker 1 service principal..."
kadmin.local -q "addprinc -randkey worker/koji-worker-1.koji.box@KOJI.BOX" || echo "Worker principal already exists"
kadmin.local -q "ktadd -k /mnt/keytabs/koji-worker.keytab worker/koji-worker-1.koji.box@KOJI.BOX" || echo "Worker keytab already exists"

# Set proper permissions
chmod 644 /mnt/keytabs/*.keytab

# The end.
