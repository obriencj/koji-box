#!/usr/bin/env python3
"""
V1 Worker API - Legacy compatibility
Maintains existing worker endpoint functionality
"""

import logging
from flask import Blueprint, request, jsonify, send_file, current_app

logger = logging.getLogger(__name__)
worker_bp = Blueprint('worker', __name__)

@worker_bp.route('/<worker_name>')
def get_worker(worker_name):
    """Get or create a worker host and return its keytab (V1 API)"""
    try:
        # Validate worker name
        if not worker_name or '/' in worker_name or '@' in worker_name:
            return jsonify({'error': 'Invalid worker name'}), 400

        # Get resource manager
        resource_manager = current_app.resource_manager

        # Create worker resource (this handles principal creation, keytab, and host registration)
        keytab_path = resource_manager._get_or_create_worker(worker_name)
        if not keytab_path:
            return jsonify({'error': 'Failed to create worker resource'}), 500

        # Serve the keytab
        return send_file(
            str(keytab_path),
            as_attachment=True,
            download_name=f"koji/{worker_name}.koji.box.keytab"
        )

    except Exception as e:
        logger.error(f"Error in get_worker for {worker_name}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# The end.
