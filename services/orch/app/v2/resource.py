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
        
        # Get container information
        container_client = current_app.container_client
        container_id, scale_index = container_client.identify_container_by_ip(client_ip)
        
        if not container_id:
            return jsonify({'error': 'Unable to identify requesting container'}), 400
        
        # Check if container is running
        if not container_client.is_container_running(container_id):
            return jsonify({'error': 'Requesting container is not running'}), 400
        
        # Get resource mapping
        db_manager = current_app.db_manager
        mapping = db_manager.get_resource_mapping(uuid)
        if not mapping:
            return jsonify({'error': 'Resource not found'}), 404
        
        # Check if resource is already checked out
        status = db_manager.get_resource_status(uuid)
        if status and status['checked_out']:
            # Check if previous owner is still alive
            if container_client.is_container_running(status['container_id']):
                return jsonify({'error': 'Resource already checked out'}), 409
            else:
                # Previous owner is dead, clean up
                logger.info(f"Cleaning up dead container checkout for {uuid}")
                db_manager.release_resource(uuid, status['container_id'])
        
        # Checkout the resource
        actual_resource_name = mapping['actual_resource_name']
        if mapping['resource_type'] == 'worker' and scale_index is not None:
            # For scaled resources, use the scale index
            actual_resource_name = f"{mapping['actual_resource_name']}-{scale_index}"
        
        if not db_manager.checkout_resource(
            uuid=uuid,
            container_id=container_id,
            container_ip=client_ip,
            resource_type=mapping['resource_type'],
            actual_resource_name=actual_resource_name,
            scale_index=scale_index
        ):
            return jsonify({'error': 'Failed to checkout resource'}), 500
        
        # Create/get the actual resource
        resource_manager = current_app.resource_manager
        resource_path = resource_manager.get_or_create_resource(
            resource_type=mapping['resource_type'],
            actual_resource_name=actual_resource_name,
            scale_index=scale_index
        )
        
        if not resource_path:
            # Rollback checkout
            db_manager.release_resource(uuid, container_id)
            return jsonify({'error': 'Failed to create resource'}), 500
        
        # Serve the resource file
        filename = f"{actual_resource_name}.{_get_file_extension(mapping['resource_type'])}"
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
        
        # Get container information
        container_client = current_app.container_client
        container_id, _ = container_client.identify_container_by_ip(client_ip)
        
        if not container_id:
            return jsonify({'error': 'Unable to identify requesting container'}), 400
        
        # Release the resource
        db_manager = current_app.db_manager
        if not db_manager.release_resource(uuid, container_id):
            return jsonify({'error': 'Resource not checked out to this container'}), 400
        
        return jsonify({'message': 'Resource released successfully'})
        
    except Exception as e:
        logger.error(f"Error in release_resource for {uuid}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

def _get_file_extension(resource_type: str) -> str:
    """Get file extension based on resource type"""
    if resource_type in ['principal', 'worker']:
        return 'keytab'
    elif resource_type == 'cert':
        return 'crt'
    elif resource_type == 'key':
        return 'key'
    else:
        return 'bin'

# The end.
