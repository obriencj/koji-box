#!/bin/bash
# Kerberos functionality test for Boxed Koji

set -e

echo "Running Kerberos functionality tests..."

# Test 1: Check if KDC is running
echo "Test 1: Checking KDC status..."
podman exec koji-boxed-kdc-1 pgrep krb5kdc || {
    echo "ERROR: KDC not running"
    exit 1
}

# Test 2: Test KDC connectivity
echo "Test 2: Testing KDC connectivity..."
podman exec koji-boxed-kdc-1 kadmin.local -q "list_principals" || {
    echo "ERROR: Cannot connect to KDC"
    exit 1
}

# Test 3: Test admin authentication
echo "Test 3: Testing admin authentication..."
podman exec koji-boxed-kdc-1 kinit admin/admin@KOJI.BOX -w admin_password || {
    echo "ERROR: Admin authentication failed"
    exit 1
}

# Test 4: Test ticket listing
echo "Test 4: Testing ticket listing..."
podman exec koji-boxed-kdc-1 klist || {
    echo "ERROR: Cannot list tickets"
    exit 1
}

# Test 5: Test service principals exist
echo "Test 5: Checking service principals..."
podman exec koji-boxed-kdc-1 kadmin.local -q "list_principals" | grep -q "hub/koji-hub.koji.box@KOJI.BOX" || {
    echo "ERROR: Hub service principal not found"
    exit 1
}

podman exec koji-boxed-kdc-1 kadmin.local -q "list_principals" | grep -q "http/koji-web.koji.box@KOJI.BOX" || {
    echo "ERROR: Web service principal not found"
    exit 1
}

podman exec koji-boxed-kdc-1 kadmin.local -q "list_principals" | grep -q "koji/koji-worker-1.koji.box@KOJI.BOX" || {
    echo "ERROR: Worker service principal not found"
    exit 1
}

# Test 6: Test keytabs exist
echo "Test 6: Checking keytabs..."
podman exec koji-boxed-kdc-1 test -f /etc/krb5kdc/hub.keytab || {
    echo "ERROR: Hub keytab not found"
    exit 1
}

podman exec koji-boxed-kdc-1 test -f /etc/krb5kdc/web.keytab || {
    echo "ERROR: Web keytab not found"
    exit 1
}

podman exec koji-boxed-kdc-1 test -f /etc/krb5kdc/worker.keytab || {
    echo "ERROR: Worker keytab not found"
    exit 1
}

echo "All Kerberos functionality tests passed!"
