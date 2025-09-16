#! /bin/bash

psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -f /mnt/koji-src/schemas/schema.sql

# The end.
