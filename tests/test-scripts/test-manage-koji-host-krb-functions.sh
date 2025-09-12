#!/bin/bash
# Test script for manage-koji-host.sh Kerberos functions

set -e

echo "Testing manage-koji-host.sh Kerberos functions..."

# Test 1: Verify setup_krb function creates credential cache
echo -e "\nTest 1: Testing setup_krb function..."

# Source the script to access functions
source /app/manage-koji-host.sh

# Test setup_krb function
if setup_krb; then
    echo "✓ setup_krb function executed successfully"
    
    # Check if KRB5CCNAME is set
    if [ -n "$KRB5CCNAME" ]; then
        echo "✓ KRB5CCNAME is set: $KRB5CCNAME"
    else
        echo "✗ KRB5CCNAME is not set"
        exit 1
    fi
    
    # Check if credential cache file exists
    if [ -f "$KRB5CCNAME" ]; then
        echo "✓ Credential cache file exists: $KRB5CCNAME"
        ls -la "$KRB5CCNAME"
    else
        echo "✗ Credential cache file does not exist"
        exit 1
    fi
    
    # Check if admin keytab is cached
    if [ -f "/tmp/admin.keytab" ] && [ -s "/tmp/admin.keytab" ]; then
        echo "✓ Admin keytab is cached"
        ls -la /tmp/admin.keytab
    else
        echo "✗ Admin keytab is not cached"
        exit 1
    fi
else
    echo "✗ setup_krb function failed"
    exit 1
fi

# Test 2: Verify teardown_krb function cleans up
echo -e "\nTest 2: Testing teardown_krb function..."

# Store the credential cache file path
CACHE_FILE="$KRB5CCNAME"

if teardown_krb; then
    echo "✓ teardown_krb function executed successfully"
    
    # Check if credential cache file is removed
    if [ ! -f "$CACHE_FILE" ]; then
        echo "✓ Credential cache file was removed"
    else
        echo "✗ Credential cache file was not removed"
        exit 1
    fi
    
    # Check if KRB5CCNAME is unset
    if [ -z "$KRB5CCNAME" ]; then
        echo "✓ KRB5CCNAME is unset"
    else
        echo "✗ KRB5CCNAME is still set: $KRB5CCNAME"
        exit 1
    fi
else
    echo "✗ teardown_krb function failed"
    exit 1
fi

# Test 3: Verify admin keytab is preserved
echo -e "\nTest 3: Testing admin keytab preservation..."

if [ -f "/tmp/admin.keytab" ] && [ -s "/tmp/admin.keytab" ]; then
    echo "✓ Admin keytab is preserved after teardown"
else
    echo "✗ Admin keytab was removed after teardown"
    exit 1
fi

# Test 4: Test multiple setup/teardown cycles
echo -e "\nTest 4: Testing multiple setup/teardown cycles..."

for i in {1..3}; do
    echo "Cycle $i:"
    
    if setup_krb; then
        echo "  ✓ setup_krb succeeded"
        if [ -f "$KRB5CCNAME" ]; then
            echo "  ✓ Credential cache created"
        else
            echo "  ✗ Credential cache not created"
            exit 1
        fi
    else
        echo "  ✗ setup_krb failed"
        exit 1
    fi
    
    if teardown_krb; then
        echo "  ✓ teardown_krb succeeded"
        if [ ! -f "$KRB5CCNAME" ]; then
            echo "  ✓ Credential cache cleaned up"
        else
            echo "  ✗ Credential cache not cleaned up"
            exit 1
        fi
    else
        echo "  ✗ teardown_krb failed"
        exit 1
    fi
done

# Test 5: Test cleanup function
echo -e "\nTest 5: Testing cleanup function..."

# Create some old temporary files
touch -t 202301010000 /tmp/krb5cc-123-1234567890 2>/dev/null || true
touch -t 202301010000 /tmp/krb5cc-456-1234567891 2>/dev/null || true

# Run cleanup
cleanup_old_files

# Check if old files were cleaned up
OLD_FILES=$(find /tmp -name "krb5cc-*-*" -mmin +60 2>/dev/null | wc -l)
if [ "$OLD_FILES" -eq 0 ]; then
    echo "✓ Old credential cache files were cleaned up"
else
    echo "✗ Old credential cache files were not cleaned up"
    exit 1
fi

echo -e "\n✓ All manage-koji-host.sh Kerberos function tests passed!"
