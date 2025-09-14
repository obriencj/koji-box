#!/usr/bin/env python3
"""
V2 Resource API - UUID-based resource management
Implements secure resource checkout system
"""

import logging
from flask import Blueprint, request, jsonify, send_file, current_app

logger = logging.getLogger(__name__)
resource_bp = Blueprint('resource', __name__)

@resource_bp.route('/<uuid>', methods=['POST'])
def checkout_resource(uuid):
    """Checkout a resource by UUID"""
    try:
        # Get client IP for container identification
        client_ip = request.remote_addr
        if not client_ip:
            return jsonify({'error': 'Unable to determine client IP'}), 400
        
        # Get checkout manager
        checkout_manager = current_app.checkout_manager
        
        # Checkout the resource
        success, resource_path, error_message = checkout_manager.checkout_resource(uuid, client_ip)
        
        if not success:
            return jsonify({'error': error_message}), 400 if 'not found' in error_message.lower() else 500
        
        # Get resource mapping for filename
        mapping = current_app.db_manager.get_resource_mapping(uuid)
        if not mapping:
            return jsonify({'error': 'Resource mapping not found'}), 500
        
        # Determine filename
        filename = _get_resource_filename(mapping, resource_path)
        
        # Serve the resource file
        return send_file(
            str(resource_path),
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error in checkout_resource for {uuid}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@resource_bp.route('/<uuid>', methods=['DELETE'])
def release_resource(uuid):
    """Release a resource by UUID"""
    try:
        # Get client IP for container identification
        client_ip = request.remote_addr
        if not client_ip:
            return jsonify({'error': 'Unable to determine client IP'}), 400
        
        # Get checkout manager
        checkout_manager = current_app.checkout_manager
        
        # Release the resource
        success, error_message = checkout_manager.release_resource(uuid, client_ip)
        
        if not success:
            return jsonify({'error': error_message}), 400
        
        return jsonify({'message': 'Resource released successfully'})
        
    except Exception as e:
        logger.error(f"Error in release_resource for {uuid}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@resource_bp.route('/<uuid>/status', methods=['GET'])
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

@resource_bp.route('/<uuid>/validate', methods=['GET'])
def validate_resource_access(uuid):
    """Validate if current client can access a resource"""
    try:
        client_ip = request.remote_addr
        if not client_ip:
            return jsonify({'error': 'Unable to determine client IP'}), 400
        
        checkout_manager = current_app.checkout_manager
        can_access, error_message = checkout_manager.validate_resource_access(uuid, client_ip)
        
        return jsonify({
            'can_access': can_access,
            'error': error_message if not can_access else None
        })
        
    except Exception as e:
        logger.error(f"Error in validate_resource_access for {uuid}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

def _get_resource_filename(mapping: dict, resource_path) -> str:
    """Get appropriate filename for resource based on type and path"""
    from pathlib import Path
    
    resource_type = mapping['resource_type']
    actual_name = mapping['actual_resource_name']
    
    if resource_type in ['principal', 'worker']:
        return f"{actual_name}.keytab"
    elif resource_type == 'cert':
        return f"{actual_name}.crt"
    elif resource_type == 'key':
        return f"{actual_name}.key"
    else:
        # Fallback to using the actual filename
        return Path(resource_path).name

# The end.