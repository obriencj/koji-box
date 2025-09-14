#!/bin/bash

# Orch Service Health Check Script

set -e

# Check if the service is responding
if curl -f http://localhost:5000/health >/dev/null 2>&1; then
    echo "✓ Orch service is healthy"
    exit 0
else
    echo "✗ Orch service is not responding"
    exit 1
fi

# The end.
