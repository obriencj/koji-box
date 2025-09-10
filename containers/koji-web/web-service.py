#!/usr/bin/env python3
"""
Koji Web Service
Web interface for Koji build system
"""

import os
import sys
import logging
import subprocess
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def install_koji():
    """Install Koji from source"""
    koji_src = Path('/mnt/koji/koji-src')
    if not koji_src.exists():
        logger.error("Koji source not found at /mnt/koji/koji-src")
        return False

    try:
        # Install Koji web
        logger.info("Installing Koji web...")
        os.chdir(koji_src / 'web')
        subprocess.run(['python', 'setup.py', 'install'], check=True)

        logger.info("Koji web installation completed")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install Koji web: {e}")
        return False

def start_web():
    """Start the Koji web service"""
    try:
        logger.info("Starting Koji web service...")

        # Start web service with gunicorn
        subprocess.run([
            'gunicorn', '--bind', '0.0.0.0:8080',
            '--workers', '2',
            '--timeout', '300',
            '--access-logfile', '-',
            '--error-logfile', '-',
            'koji.web:app'
        ])

    except Exception as e:
        logger.error(f"Failed to start web service: {e}")
        sys.exit(1)

if __name__ == '__main__':
    logger.info("Starting Koji Web Service")

    # Install Koji if not already installed
    if not install_koji():
        logger.error("Failed to install Koji web")
        sys.exit(1)

    # Start web service
    start_web()
