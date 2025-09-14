#!/usr/bin/env python3
"""
Error handlers for the Orch service
Provides consistent error responses and logging
"""

import logging
from typing import Dict, Any, Optional
from flask import jsonify, request, current_app

logger = logging.getLogger(__name__)

class ErrorResponse:
    """Standardized error response format"""
    
    @staticmethod
    def create_error_response(
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ) -> tuple:
        """Create a standardized error response"""
        response = {
            'error': {
                'code': error_code,
                'message': message,
                'details': details or {}
            },
            'request_id': getattr(request, 'id', None),
            'timestamp': current_app.config.get('TIMESTAMP', None)
        }
        
        return jsonify(response), status_code
    
    @staticmethod
    def validation_error(message: str, field: str = None, value: str = None) -> tuple:
        """Create a validation error response"""
        details = {}
        if field:
            details['field'] = field
        if value:
            details['value'] = value
        
        return ErrorResponse.create_error_response(
            'VALIDATION_ERROR',
            message,
            details,
            400
        )
    
    @staticmethod
    def resource_not_found(resource_type: str, identifier: str) -> tuple:
        """Create a resource not found error response"""
        return ErrorResponse.create_error_response(
            'RESOURCE_NOT_FOUND',
            f"{resource_type} not found",
            {'resource_type': resource_type, 'identifier': identifier},
            404
        )
    
    @staticmethod
    def resource_already_checked_out(uuid: str, container_id: str) -> tuple:
        """Create a resource already checked out error response"""
        return ErrorResponse.create_error_response(
            'RESOURCE_ALREADY_CHECKED_OUT',
            "Resource is already checked out to another container",
            {'uuid': uuid, 'container_id': container_id},
            409
        )
    
    @staticmethod
    def container_not_found(ip: str) -> tuple:
        """Create a container not found error response"""
        return ErrorResponse.create_error_response(
            'CONTAINER_NOT_FOUND',
            "Unable to identify requesting container",
            {'client_ip': ip},
            400
        )
    
    @staticmethod
    def container_not_running(container_id: str) -> tuple:
        """Create a container not running error response"""
        return ErrorResponse.create_error_response(
            'CONTAINER_NOT_RUNNING',
            "Requesting container is not running",
            {'container_id': container_id},
            400
        )
    
    @staticmethod
    def resource_creation_failed(resource_type: str, name: str, reason: str) -> tuple:
        """Create a resource creation failed error response"""
        return ErrorResponse.create_error_response(
            'RESOURCE_CREATION_FAILED',
            f"Failed to create {resource_type} resource",
            {'resource_type': resource_type, 'name': name, 'reason': reason},
            500
        )
    
    @staticmethod
    def database_error(operation: str, details: str) -> tuple:
        """Create a database error response"""
        return ErrorResponse.create_error_response(
            'DATABASE_ERROR',
            f"Database operation failed: {operation}",
            {'operation': operation, 'details': details},
            500
        )
    
    @staticmethod
    def container_client_error(operation: str, details: str) -> tuple:
        """Create a container client error response"""
        return ErrorResponse.create_error_response(
            'CONTAINER_CLIENT_ERROR',
            f"Container client operation failed: {operation}",
            {'operation': operation, 'details': details},
            500
        )
    
    @staticmethod
    def internal_error(message: str, details: Optional[Dict[str, Any]] = None) -> tuple:
        """Create an internal server error response"""
        return ErrorResponse.create_error_response(
            'INTERNAL_ERROR',
            message,
            details,
            500
        )


class ErrorLogger:
    """Centralized error logging"""
    
    @staticmethod
    def log_error(error_type: str, message: str, details: Optional[Dict[str, Any]] = None, exception: Exception = None):
        """Log an error with consistent formatting"""
        log_data = {
            'error_type': error_type,
            'message': message,
            'details': details or {},
            'request_id': getattr(request, 'id', None),
            'client_ip': request.remote_addr if request else None,
            'user_agent': request.headers.get('User-Agent') if request else None
        }
        
        if exception:
            log_data['exception'] = str(exception)
            log_data['exception_type'] = type(exception).__name__
        
        logger.error(f"{error_type}: {message}", extra=log_data)
    
    @staticmethod
    def log_validation_error(field: str, value: str, message: str):
        """Log a validation error"""
        ErrorLogger.log_error(
            'VALIDATION_ERROR',
            f"Validation failed for field '{field}'",
            {'field': field, 'value': value, 'validation_message': message}
        )
    
    @staticmethod
    def log_security_error(operation: str, details: str):
        """Log a security-related error"""
        ErrorLogger.log_error(
            'SECURITY_ERROR',
            f"Security violation in {operation}",
            {'operation': operation, 'details': details}
        )
    
    @staticmethod
    def log_resource_error(operation: str, resource_id: str, details: str):
        """Log a resource-related error"""
        ErrorLogger.log_error(
            'RESOURCE_ERROR',
            f"Resource operation failed: {operation}",
            {'operation': operation, 'resource_id': resource_id, 'details': details}
        )


class ErrorHandler:
    """Centralized error handling for Flask routes"""
    
    @staticmethod
    def handle_validation_error(field: str, value: str, message: str) -> tuple:
        """Handle validation errors"""
        ErrorLogger.log_validation_error(field, value, message)
        return ErrorResponse.validation_error(message, field, value)
    
    @staticmethod
    def handle_resource_not_found(resource_type: str, identifier: str) -> tuple:
        """Handle resource not found errors"""
        ErrorLogger.log_error(
            'RESOURCE_NOT_FOUND',
            f"{resource_type} not found: {identifier}",
            {'resource_type': resource_type, 'identifier': identifier}
        )
        return ErrorResponse.resource_not_found(resource_type, identifier)
    
    @staticmethod
    def handle_container_error(operation: str, details: str, exception: Exception = None) -> tuple:
        """Handle container-related errors"""
        ErrorLogger.log_error(
            'CONTAINER_ERROR',
            f"Container operation failed: {operation}",
            {'operation': operation, 'details': details},
            exception
        )
        return ErrorResponse.container_client_error(operation, details)
    
    @staticmethod
    def handle_database_error(operation: str, details: str, exception: Exception = None) -> tuple:
        """Handle database errors"""
        ErrorLogger.log_error(
            'DATABASE_ERROR',
            f"Database operation failed: {operation}",
            {'operation': operation, 'details': details},
            exception
        )
        return ErrorResponse.database_error(operation, details)
    
    @staticmethod
    def handle_internal_error(message: str, exception: Exception = None, details: Optional[Dict[str, Any]] = None) -> tuple:
        """Handle internal server errors"""
        ErrorLogger.log_error(
            'INTERNAL_ERROR',
            message,
            details,
            exception
        )
        return ErrorResponse.internal_error(message, details)


# The end.
