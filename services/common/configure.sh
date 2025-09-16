#! /bin/bash

envsubst < /app/koji.conf.template > /etc/koji.conf
envsubst < /app/krb5.conf.template > /etc/krb5.conf

/app/orch.sh ca-install

# The end.
