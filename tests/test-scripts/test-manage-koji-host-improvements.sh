#!/bin/bash
# Test script for improved manage-koji-host.sh functionality

set -e

echo "Testing improved manage-koji-host.sh functionality..."

# Test 1: Verify caching behavior
echo -e "\nTest 1: Testing keytab caching..."

# Run the script twice and check if second run uses cache
echo "First run (should fetch keytab):"
if /app/manage-koji-host.sh "test-host-1" 2>&1 | grep -q "Fetching fresh admin keytab"; then
    echo "✓ First run fetched fresh keytab"
else
    echo "✗ First run did not fetch fresh keytab"
    exit 1
fi

echo "Second run (should use cache):"
if /app/manage-koji-host.sh "test-host-2" 2>&1 | grep -q "Using cached admin keytab"; then
    echo "✓ Second run used cached keytab"
else
    echo "✗ Second run did not use cached keytab"
    exit 1
fi

# Test 2: Verify unique keytab files for parallel requests
echo -e "\nTest 2: Testing unique keytab files..."

# Check that multiple unique keytab files exist
KEYTAB_COUNT=$(ls /tmp/admin-*-*.keytab 2>/dev/null | wc -l)
if [ "$KEYTAB_COUNT" -gt 0 ]; then
    echo "✓ Found $KEYTAB_COUNT unique keytab files"
    ls -la /tmp/admin-*-*.keytab
else
    echo "✗ No unique keytab files found"
    exit 1
fi

# Test 3: Verify cached keytab is preserved
echo -e "\nTest 3: Testing cached keytab preservation..."

if [ -f "/tmp/admin.keytab" ] && [ -s "/tmp/admin.keytab" ]; then
    echo "✓ Cached admin keytab exists and is not empty"
    ls -la /tmp/admin.keytab
else
    echo "✗ Cached admin keytab not found or empty"
    exit 1
fi

# Test 4: Test cleanup function
echo -e "\nTest 4: Testing cleanup function..."

# Create some old temporary files (simulate old files)
touch -t 202301010000 /tmp/admin-123-1234567890.keytab 2>/dev/null || true
touch -t 202301010000 /tmp/admin-456-1234567891.keytab 2>/dev/null || true

# Run cleanup
if /app/manage-koji-host.sh "test-host-3" 2>&1 | grep -q "cleanup_old_keytabs"; then
    echo "✓ Cleanup function executed"
else
    echo "✗ Cleanup function not executed"
fi

# Check if old files were cleaned up
OLD_FILES=$(find /tmp -name "admin-*-*.keytab" -mmin +60 2>/dev/null | wc -l)
if [ "$OLD_FILES" -eq 0 ]; then
    echo "✓ Old keytab files were cleaned up"
else
    echo "✗ Old keytab files were not cleaned up"
fi

# Test 5: Verify error handling doesn't delete cached keytab
echo -e "\nTest 5: Testing error handling preserves cached keytab..."

# Test with invalid principal name (should fail but preserve cache)
if /app/manage-koji-host.sh "invalid@name" 2>&1 | grep -q "Invalid principal name"; then
    echo "✓ Invalid principal name correctly rejected"
else
    echo "✗ Invalid principal name not rejected"
fi

# Verify cached keytab still exists
if [ -f "/tmp/admin.keytab" ] && [ -s "/tmp/admin.keytab" ]; then
    echo "✓ Cached keytab preserved after error"
else
    echo "✗ Cached keytab was deleted after error"
    exit 1
fi

echo -e "\n✓ All manage-koji-host.sh improvement tests passed!"
