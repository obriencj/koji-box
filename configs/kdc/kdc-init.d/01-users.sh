#! /bin/bash


# Create Kerberos admin user
echo "Creating kerberos admin user..."
kadmin.local -q "addprinc -pw admin_password admin/admin@KOJI.BOX" || echo "Admin user already exists"


# These users will have koji accounts with varying permissions

# Create test-admin user
echo "Creating test-admin user..."
kadmin.local -q "addprinc -pw test-admin test-admin@KOJI.BOX" || echo "Test-admin user already exists"
kadmin.local -q "ktadd -k /mnt/keytabs/test-admin.keytab test-admin@KOJI.BOX" || echo "Test-admin keytab already exists"

# Create test-user user
echo "Creating test-user user..."
kadmin.local -q "addprinc -pw test-user test-user@KOJI.BOX" || echo "Test-user user already exists"
kadmin.local -q "ktadd -k /mnt/keytabs/test-user.keytab test-user@KOJI.BOX" || echo "Test-user keytab already exists"

# Create friend user
echo "Creating friend user..."
kadmin.local -q "addprinc -pw friend friend@KOJI.BOX" || echo "Friend user already exists"
kadmin.local -q "ktadd -k /mnt/keytabs/friend.keytab friend@KOJI.BOX" || echo "Friend keytab already exists"

# The end.
