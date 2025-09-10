#!/usr/bin/env python3
"""
Koji Client Service
Interactive client for Koji build system
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
        # Install Koji client
        logger.info("Installing Koji client...")
        os.chdir(koji_src / 'cli')
        subprocess.run(['python', 'setup.py', 'install'], check=True)

        logger.info("Koji client installation completed")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install Koji client: {e}")
        return False

def start_client():
    """Start the Koji client service"""
    try:
        logger.info("Starting Koji client service...")

        # Start interactive shell with koji commands available
        print("Koji Client Ready!")
        print("Available commands: koji, koji-admin")
        print("Type 'exit' to quit")

        # Start bash shell
        subprocess.run(['/bin/bash'])

    except Exception as e:
        logger.error(f"Failed to start client service: {e}")
        sys.exit(1)

if __name__ == '__main__':
    logger.info("Starting Koji Client Service")

    # Install Koji if not already installed
    if not install_koji():
        logger.error("Failed to install Koji client")
        sys.exit(1)

    # Start client service
    start_client()
