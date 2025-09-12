#!/bin/bash
# Health check script for Keytab Service

curl -f http://localhost:5000/health > /dev/null 2>&1
