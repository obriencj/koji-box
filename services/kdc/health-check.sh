#!/bin/bash

set -e

pgrep krb5kdc > /dev/null 2>&1
pgrep kadmind > /dev/null 2>&1
test -f /var/lib/krb5kdc/principal
test -f /var/lib/krb5kdc/kadmind-ready
test -f /var/lib/krb5kdc/kdc-init-complete

# The end.
