#! /bin/bash


# Create Kerberos admin user
echo "Creating kerberos admin user..."
kadmin.local -q "addprinc -pw admin_password admin/admin@${KRB5_REALM}" || echo "Admin user already exists"


# # These users will have koji accounts with varying permissions

# # Create koji-admin user
# echo "Creating koji-admin user..."
# kadmin.local -q "addprinc -pw koji-admin koji-admin@${KRB5_REALM}" || echo "Koji-admin user already exists"

# # Create test-admin user
# echo "Creating test-admin user..."
# kadmin.local -q "addprinc -pw test-admin test-admin@${KRB5_REALM}" || echo "Test-admin user already exists"
# # kadmin.local -q "ktadd -k /mnt/keytabs/test-admin.keytab test-admin@${KRB5_REALM}" || echo "Test-admin keytab already exists"

# # Create test-user user
# echo "Creating test-user user..."
# kadmin.local -q "addprinc -pw test-user test-user@${KRB5_REALM}" || echo "Test-user user already exists"
# # kadmin.local -q "ktadd -k /mnt/keytabs/test-user.keytab test-user@${KRB5_REALM}" || echo "Test-user keytab already exists"

# # Create friend user
# echo "Creating friend user..."
# kadmin.local -q "addprinc -pw friend friend@${KRB5_REALM}" || echo "Friend user already exists"
# # kadmin.local -q "ktadd -k /mnt/keytabs/friend.keytab friend@${KRB5_REALM}" || echo "Friend keytab already exists"

# The end.
