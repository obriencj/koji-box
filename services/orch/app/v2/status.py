#!/usr/bin/env python3
"""
V2 Status API - Resource status and health checks
"""

import logging
from flask import Blueprint, request, jsonify, current_app

logger = logging.getLogger(__name__)
status_bp = Blueprint('status', __name__)

@status_bp.route('/<uuid>')
def get_resource_status(uuid):
    """Get status of a resource by UUID"""
    try:
        checkout_manager = current_app.checkout_manager
        status = checkout_manager.get_resource_status(uuid)

        if not status:
            return jsonify({'error': 'Resource not found'}), 404

        return jsonify(status)

    except Exception as e:
        logger.error(f"Error in get_resource_status for {uuid}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@status_bp.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db_manager = current_app.db_manager
        mappings = db_manager.get_all_mappings()

        # Check container client connection
        container_client = current_app.container_client
        is_connected = container_client.is_connected()

        # Clean up dead containers
        checkout_manager = current_app.checkout_manager
        cleaned = checkout_manager.cleanup_dead_containers()

        return jsonify({
            'status': 'healthy',
            'service': 'orch-service',
            'version': '2.0.0',
            'database': 'connected',
            'container_client': 'connected' if is_connected else 'disconnected',
            'mappings_loaded': len(mappings),
            'containers_cleaned': cleaned
        })

    except Exception as e:
        logger.error(f"Error in health_check: {e}")
        return jsonify({
            'status': 'unhealthy',
            'service': 'orch-service',
            'error': str(e)
        }), 500

@status_bp.route('/mappings')
def get_all_mappings():
    """Get all resource mappings"""
    try:
        db_manager = current_app.db_manager
        mappings = db_manager.get_all_mappings()
        return jsonify({'mappings': mappings})

    except Exception as e:
        logger.error(f"Error in get_all_mappings: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# The end.
