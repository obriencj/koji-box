#! /bin/bash

psql -U koji -d koji -f /mnt/koji-src/schemas/schema.sql

# The end.
