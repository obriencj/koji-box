#!/usr/bin/env python3
"""
V2 CA API - Certificate Authority management
Provides CA certificate access without UUID/checkout requirements
"""

import logging
from flask import Blueprint, request, jsonify, send_file, current_app

from ..common.error_handlers import ErrorHandler, ErrorResponse

logger = logging.getLogger("/api/v2/ca")
ca_bp = Blueprint('ca', __name__)

@ca_bp.route('/certificate', methods=['GET'])
def get_ca_certificate():
    """Get CA certificate (public key only) - accessible without UUID or checkout"""
    try:
        # Validate request method
        if request.method != 'GET':
            return ErrorHandler.handle_validation_error('method', request.method, 'Only GET method allowed')

        # Get CA manager
        ca_manager = current_app.ca_manager

        # Get or create CA certificate
        ca_cert_path = ca_manager.get_ca_certificate()
        if not ca_cert_path:
            return ErrorHandler.handle_internal_error("Failed to get or create CA certificate")

        # Serve the CA certificate file
        return send_file(
            str(ca_cert_path),
            as_attachment=True,
            download_name='ca.crt',
            mimetype='application/x-x509-ca-cert'
        )

    except Exception as e:
        logger.error(f"Unexpected error in get_ca_certificate: {e}")
        return ErrorHandler.handle_internal_error("Unexpected error during CA certificate retrieval", e)

@ca_bp.route('/info', methods=['GET'])
def get_ca_info():
    """Get CA certificate information - accessible without UUID or checkout"""
    try:
        # Validate request method
        if request.method != 'GET':
            return ErrorHandler.handle_validation_error('method', request.method, 'Only GET method allowed')

        # Get CA manager
        ca_manager = current_app.ca_manager

        # Get CA information
        ca_info = ca_manager.get_ca_info()

        if not ca_info.get('exists', False):
            return ErrorHandler.handle_resource_not_found('ca_certificate', 'CA certificate not found')

        return jsonify({
            'ca_info': ca_info,
            'requested_at': current_app.config.get('TIMESTAMP', None)
        })

    except Exception as e:
        logger.error(f"Unexpected error in get_ca_info: {e}")
        return ErrorHandler.handle_internal_error("Unexpected error during CA info retrieval", e)

@ca_bp.route('/status', methods=['GET'])
def get_ca_status():
    """Get CA status - accessible without UUID or checkout"""
    try:
        # Validate request method
        if request.method != 'GET':
            return ErrorHandler.handle_validation_error('method', request.method, 'Only GET method allowed')

        # Get CA manager
        ca_manager = current_app.ca_manager

        # Check CA status
        ca_exists = ca_manager.ca_exists()

        return jsonify({
            'ca_exists': ca_exists,
            'ca_directory': str(ca_manager.ca_dir),
            'certificates_directory': str(ca_manager.certs_dir),
            'status': 'available' if ca_exists else 'not_created',
            'checked_at': current_app.config.get('TIMESTAMP', None)
        })

    except Exception as e:
        logger.error(f"Unexpected error in get_ca_status: {e}")
        return ErrorHandler.handle_internal_error("Unexpected error during CA status check", e)

# The end.
