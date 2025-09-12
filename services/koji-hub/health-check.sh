#!/bin/bash
# Health check script for Koji Hub

curl -f http://localhost:8080/status > /dev/null 2>&1
