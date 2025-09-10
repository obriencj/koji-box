#!/bin/bash
# Health check script for Koji Client

# Client is interactive, so just check if the process is running
ps aux | grep -v grep | grep python | grep client-service > /dev/null 2>&1
