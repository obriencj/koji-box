#!/usr/bin/env python3
"""
V1 Certificate API - Legacy compatibility
Maintains existing certificate endpoint functionality
"""

import logging
from flask import Blueprint, request, jsonify, send_file, current_app

logger = logging.getLogger(__name__)
cert_bp = Blueprint('cert', __name__)

@cert_bp.route('/<path:cn>')
def get_certificate(cn):
    """Get or create a certificate and return the certificate file (V1 API)"""
    try:
        # Validate CN
        if not cn or '/' in cn:
            return jsonify({'error': 'Invalid CN (Common Name)'}), 400

        # Get resource manager
        resource_manager = current_app.resource_manager

        # Create certificate
        cert_path = resource_manager._get_or_create_certificate(cn)
        if not cert_path:
            return jsonify({'error': 'Failed to create certificate'}), 500

        # Serve the certificate file
        return send_file(
            str(cert_path),
            as_attachment=True,
            download_name=f"{cn}.crt"
        )

    except Exception as e:
        logger.error(f"Error in get_certificate for {cn}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@cert_bp.route('/key/<path:cn>')
def get_private_key(cn):
    """Get or create a certificate and return the private key file (V1 API)"""
    try:
        # Validate CN
        if not cn or '/' in cn:
            return jsonify({'error': 'Invalid CN (Common Name)'}), 400

        # Get resource manager
        resource_manager = current_app.resource_manager

        # Create private key
        key_path = resource_manager._get_or_create_private_key(cn)
        if not key_path:
            return jsonify({'error': 'Failed to create private key'}), 500

        # Serve the private key file
        return send_file(
            str(key_path),
            as_attachment=True,
            download_name=f"{cn}.key"
        )

    except Exception as e:
        logger.error(f"Error in get_private_key for {cn}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# The end.
