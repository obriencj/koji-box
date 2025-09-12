#!/usr/bin/env python3
"""
Koji Worker Service
Build worker for Koji build system
"""

import os
import sys
import logging
import subprocess
import time
import signal
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
        # Install Koji worker
        logger.info("Installing Koji worker...")
        os.chdir(koji_src / 'builder')
        subprocess.run(['python', 'setup.py', 'install'], check=True)

        logger.info("Koji worker installation completed")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install Koji worker: {e}")
        return False

def setup_worker():
    """Setup worker configuration"""
    try:
        logger.info("Setting up worker configuration...")

        # Create worker configuration
        worker_config = """
[koji]
server = http://koji-hub:8080/kojihub
weburl = http://koji-web:8080
topurl = http://koji-storage:8080

[builder]
workdir = /var/lib/koji-worker
mockdir = /var/lib/mock
mockuser = koji
mockgroup = koji
mockhost = x86_64
mockarch = x86_64
mocktarget = x86_64
"""

        with open('/etc/koji-worker/worker.conf', 'w') as f:
            f.write(worker_config)

        logger.info("Worker configuration created")
        return True

    except Exception as e:
        logger.error(f"Failed to setup worker: {e}")
        return False

def start_worker():
    """Start the Koji worker service"""
    try:
        logger.info("Starting Koji worker service...")

        # Start worker daemon
        subprocess.run([
            'koji-worker',
            '--config', '/etc/koji-worker/worker.conf',
            '--daemon'
        ])

    except Exception as e:
        logger.error(f"Failed to start worker service: {e}")
        sys.exit(1)

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal, stopping worker...")
    sys.exit(0)

if __name__ == '__main__':
    logger.info("Starting Koji Worker Service")

    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Install Koji if not already installed
    if not install_koji():
        logger.error("Failed to install Koji worker")
        sys.exit(1)

    # Setup worker
    if not setup_worker():
        logger.error("Failed to setup worker")
        sys.exit(1)

    # Start worker service
    start_worker()


# The end.
