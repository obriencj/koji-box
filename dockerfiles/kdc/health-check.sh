#!/bin/bash
# Health check script for KDC

# Check if KDC is running
pgrep krb5kdc > /dev/null 2>&1
