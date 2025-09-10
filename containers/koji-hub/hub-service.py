#!/usr/bin/env python3
"""
Koji Hub Service
Main Koji hub service providing build system coordination
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
        # Install Koji hub
        logger.info("Installing Koji hub...")
        os.chdir(koji_src / 'hub')
        subprocess.run(['python', 'setup.py', 'install'], check=True)

        # Install Koji web
        logger.info("Installing Koji web...")
        os.chdir(koji_src / 'web')
        subprocess.run(['python', 'setup.py', 'install'], check=True)

        # Install Koji client
        logger.info("Installing Koji client...")
        os.chdir(koji_src / 'cli')
        subprocess.run(['python', 'setup.py', 'install'], check=True)

        logger.info("Koji installation completed")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install Koji: {e}")
        return False

def setup_database():
    """Initialize database schema"""
    try:
        logger.info("Setting up database schema...")

        # Run database initialization
        subprocess.run([
            'koji-hub', '--config', '/etc/koji-hub/hub.conf',
            '--init-db'
        ], check=True)

        logger.info("Database schema initialized")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to setup database: {e}")
        return False

def start_hub():
    """Start the Koji hub service"""
    try:
        logger.info("Starting Koji hub service...")

        # Start hub with gunicorn
        subprocess.run([
            'gunicorn', '--bind', '0.0.0.0:8080',
            '--workers', '4',
            '--timeout', '300',
            '--access-logfile', '-',
            '--error-logfile', '-',
            'koji.hub:app'
        ])

    except Exception as e:
        logger.error(f"Failed to start hub service: {e}")
        sys.exit(1)

if __name__ == '__main__':
    logger.info("Starting Koji Hub Service")

    # Install Koji if not already installed
    if not install_koji():
        logger.error("Failed to install Koji")
        sys.exit(1)

    # Setup database
    if not setup_database():
        logger.error("Failed to setup database")
        sys.exit(1)

    # Start hub service
    start_hub()
