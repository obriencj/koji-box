#!/bin/bash

set -euo pipefail

# Configure kerberos, koji, and get the root CA
/app/configuration.sh

/app/orch.sh checkout ${ANSIBLE_KEYTAB} /app/ansible.keytab
chown koji:koji /app/ansible.keytab

exec su koji -- "/app/ansible.sh" "$@"

# The end.
