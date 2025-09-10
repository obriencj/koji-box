#!/bin/bash
# Health check script for Koji Worker

ps aux | grep -v grep | grep koji-worker > /dev/null 2>&1
