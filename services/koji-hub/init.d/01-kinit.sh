#! /bin/bash

set -e

echo "Performing kinit with admin keytab..."
if kinit -kt /etc/koji-hub/admin.keytab ${KOJI_ADMIN_PRINC}; then
    echo "Successfully authenticated as $KOJI_ADMIN_PRINC"
else
    echo "ERROR: Failed to authenticate with admin keytab"
    exit 1
fi

koji hello || exit 1

# The end.
