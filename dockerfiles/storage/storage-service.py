#!/usr/bin/env python3
"""
Koji Storage Service
Provides HTTP and NFS access to Koji storage
"""

import os
import sys
import logging
from flask import Flask, send_file, jsonify, request
from pathlib import Path
import threading
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
STORAGE_PATH = os.environ.get('KOJI_STORAGE_PATH', '/mnt/koji')
PORT = int(os.environ.get('KOJI_STORAGE_PORT', '8080'))

# Ensure storage directories exist
def setup_storage():
    """Create necessary storage directories"""
    directories = [
        'packages',
        'repos',
        'work',
        'scratch',
        'local'
    ]

    for directory in directories:
        path = Path(STORAGE_PATH) / directory
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {path}")

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'koji-storage',
        'storage_path': STORAGE_PATH
    })

@app.route('/')
def index():
    """Root endpoint with service info"""
    return jsonify({
        'service': 'koji-storage',
        'version': '1.0.0',
        'storage_path': STORAGE_PATH,
        'endpoints': {
            'health': '/health',
            'packages': '/packages',
            'repos': '/repos'
        }
    })

@app.route('/packages/<path:filepath>')
def serve_package(filepath):
    """Serve package files"""
    full_path = Path(STORAGE_PATH) / 'packages' / filepath
    if full_path.exists() and full_path.is_file():
        return send_file(str(full_path))
    return jsonify({'error': 'File not found'}), 404

@app.route('/repos/<path:filepath>')
def serve_repo(filepath):
    """Serve repository files"""
    full_path = Path(STORAGE_PATH) / 'repos' / filepath
    if full_path.exists() and full_path.is_file():
        return send_file(str(full_path))
    return jsonify({'error': 'File not found'}), 404

@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload file to storage"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Determine upload path based on content type or path parameter
    upload_type = request.form.get('type', 'packages')
    upload_path = Path(STORAGE_PATH) / upload_type / file.filename

    # Ensure directory exists
    upload_path.parent.mkdir(parents=True, exist_ok=True)

    # Save file
    file.save(str(upload_path))
    logger.info(f"Uploaded file: {upload_path}")

    return jsonify({
        'message': 'File uploaded successfully',
        'path': str(upload_path.relative_to(Path(STORAGE_PATH)))
    })

def start_nfs_server():
    """Start NFS server in background"""
    try:
        # Export the storage directory
        export_line = f"{STORAGE_PATH} *(rw,sync,no_subtree_check,no_root_squash)"
        with open('/etc/exports', 'w') as f:
            f.write(export_line)

        # Start NFS server
        os.system('exportfs -ra')
        os.system('rpcbind')
        os.system('rpc.nfsd')
        os.system('rpc.mountd')

        logger.info("NFS server started")
    except Exception as e:
        logger.error(f"Failed to start NFS server: {e}")

if __name__ == '__main__':
    logger.info("Starting Koji Storage Service")

    # Setup storage
    setup_storage()

    # Start NFS server in background
    nfs_thread = threading.Thread(target=start_nfs_server, daemon=True)
    nfs_thread.start()

    # Start HTTP server
    logger.info(f"Starting HTTP server on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
