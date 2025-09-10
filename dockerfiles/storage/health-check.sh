#!/bin/bash
# Health check script for storage service

curl -f http://localhost:8080/health > /dev/null 2>&1
