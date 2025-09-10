#!/bin/bash
# Health check script for Koji Web

curl -f http://localhost:8080/ > /dev/null 2>&1
