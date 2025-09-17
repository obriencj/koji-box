#!/usr/bin/env python3
"""
V2 Resource API - UUID-based resource management
Implements secure resource checkout system with comprehensive validation
"""

import logging
import socket
from flask import Blueprint, request, jsonify, send_file, current_app

from ..common.validators import ResourceValidator, SecurityValidator, RequestValidator
from ..common.error_handlers import ErrorHandler, ErrorResponse

logger = logging.getLogger("/api/v2/resource")
resource_bp = Blueprint('resource', __name__)

@resource_bp.route('/<uuid>', methods=['POST'])
def checkout_resource(uuid):
    """Checkout a resource by UUID"""
    try:
        # Validate request method
        valid, error_msg = RequestValidator.validate_request_method(request, ['POST'])
        if not valid:
            return ErrorHandler.handle_validation_error('method', request.method, error_msg)

        # Validate UUID format
        valid, error_msg = ResourceValidator.validate_uuid(uuid)
        if not valid:
            return ErrorHandler.handle_validation_error('uuid', uuid, error_msg)

        # Validate request headers
        valid, error_msg = RequestValidator.validate_request_headers(request)
        if not valid:
            return ErrorHandler.handle_validation_error('headers', 'remote_addr', error_msg)

        # Get client IP for container identification
        client_ip = request.remote_addr
        if client_ip == '127.0.0.1':
            client_ip = socket.gethostbyname(socket.gethostname())

        # Validate IP address format
        valid, error_msg = ResourceValidator.validate_ip_address(client_ip)
        if not valid:
            return ErrorHandler.handle_validation_error('client_ip', client_ip, error_msg)

        # Get checkout manager
        checkout_manager = current_app.checkout_manager

        # Checkout the resource
        success, resource_path, error_message = checkout_manager.checkout_resource(uuid, client_ip)

        if not success:
            if 'not found' in error_message.lower():
                return ErrorHandler.handle_resource_not_found('resource', uuid)
            elif 'already checked out' in error_message.lower():
                return ErrorResponse.resource_already_checked_out(uuid, 'unknown')
            elif 'unable to identify' in error_message.lower():
                return ErrorHandler.handle_container_error('identification', error_message)
            else:
                return ErrorHandler.handle_internal_error(f"Checkout failed: {error_message}")

        # Get resource mapping for filename
        mapping = current_app.db_manager.get_resource_mapping(uuid)
        if not mapping:
            return ErrorHandler.handle_resource_not_found('resource_mapping', uuid)

        # Determine filename
        filename = _get_resource_filename(mapping, resource_path)

        # Serve the resource file
        return send_file(
            str(resource_path),
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        logger.error(f"Unexpected error in checkout_resource for {uuid}: {e}")
        return ErrorHandler.handle_internal_error("Unexpected error during resource checkout", e)

@resource_bp.route('/<uuid>', methods=['DELETE'])
def release_resource(uuid):
    """Release a resource by UUID"""
    try:
        # Validate request method
        valid, error_msg = RequestValidator.validate_request_method(request, ['DELETE'])
        if not valid:
            return ErrorHandler.handle_validation_error('method', request.method, error_msg)

        # Validate UUID format
        valid, error_msg = ResourceValidator.validate_uuid(uuid)
        if not valid:
            return ErrorHandler.handle_validation_error('uuid', uuid, error_msg)

        # Validate request headers
        valid, error_msg = RequestValidator.validate_request_headers(request)
        if not valid:
            return ErrorHandler.handle_validation_error('headers', 'remote_addr', error_msg)

        # Get client IP for container identification
        client_ip = request.remote_addr

        # Validate IP address format
        valid, error_msg = ResourceValidator.validate_ip_address(client_ip)
        if not valid:
            return ErrorHandler.handle_validation_error('client_ip', client_ip, error_msg)

        # Get checkout manager
        checkout_manager = current_app.checkout_manager

        # Release the resource
        success, error_message = checkout_manager.release_resource(uuid, client_ip)

        if not success:
            if 'unable to identify' in error_message.lower():
                return ErrorHandler.handle_container_error('identification', error_message)
            elif 'not checked out' in error_message.lower():
                return ErrorHandler.handle_validation_error('resource', uuid, "Resource not checked out to this container")
            else:
                return ErrorHandler.handle_internal_error(f"Release failed: {error_message}")

        return jsonify({
            'message': 'Resource released successfully',
            'uuid': uuid,
            'released_at': current_app.config.get('TIMESTAMP', None)
        })

    except Exception as e:
        logger.error(f"Unexpected error in release_resource for {uuid}: {e}")
        return ErrorHandler.handle_internal_error("Unexpected error during resource release", e)

@resource_bp.route('/<uuid>/status', methods=['GET'])
def get_resource_status(uuid):
    """Get status of a resource by UUID"""
    try:
        # Validate request method
        valid, error_msg = RequestValidator.validate_request_method(request, ['GET'])
        if not valid:
            return ErrorHandler.handle_validation_error('method', request.method, error_msg)

        # Validate UUID format
        valid, error_msg = ResourceValidator.validate_uuid(uuid)
        if not valid:
            return ErrorHandler.handle_validation_error('uuid', uuid, error_msg)

        checkout_manager = current_app.checkout_manager
        status = checkout_manager.get_resource_status(uuid)

        if not status:
            return ErrorHandler.handle_resource_not_found('resource', uuid)

        return jsonify({
            'status': status,
            'requested_at': current_app.config.get('TIMESTAMP', None)
        })

    except Exception as e:
        logger.error(f"Unexpected error in get_resource_status for {uuid}: {e}")
        return ErrorHandler.handle_internal_error("Unexpected error during status retrieval", e)

@resource_bp.route('/<uuid>/validate', methods=['GET'])
def validate_resource_access(uuid):
    """Validate if current client can access a resource"""
    try:
        # Validate request method
        valid, error_msg = RequestValidator.validate_request_method(request, ['GET'])
        if not valid:
            return ErrorHandler.handle_validation_error('method', request.method, error_msg)

        # Validate UUID format
        valid, error_msg = ResourceValidator.validate_uuid(uuid)
        if not valid:
            return ErrorHandler.handle_validation_error('uuid', uuid, error_msg)

        # Validate request headers
        valid, error_msg = RequestValidator.validate_request_headers(request)
        if not valid:
            return ErrorHandler.handle_validation_error('headers', 'remote_addr', error_msg)

        client_ip = request.remote_addr

        # Validate IP address format
        valid, error_msg = ResourceValidator.validate_ip_address(client_ip)
        if not valid:
            return ErrorHandler.handle_validation_error('client_ip', client_ip, error_msg)

        checkout_manager = current_app.checkout_manager
        can_access, error_message = checkout_manager.validate_resource_access(uuid, client_ip)

        return jsonify({
            'can_access': can_access,
            'error': error_message if not can_access else None,
            'validated_at': current_app.config.get('TIMESTAMP', None)
        })

    except Exception as e:
        logger.error(f"Unexpected error in validate_resource_access for {uuid}: {e}")
        return ErrorHandler.handle_internal_error("Unexpected error during access validation", e)

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