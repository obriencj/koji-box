#!/bin/bash
# Health check script for nginx

curl -f http://localhost/health || exit 1
