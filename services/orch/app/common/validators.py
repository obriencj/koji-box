#!/usr/bin/env python3
"""
Validators for the Orch service
Handles input validation and security checks
"""

import re
import logging
from typing import Optional, Tuple, Dict
from urllib.parse import quote_plus as urlquote

logger = logging.getLogger(__name__)

class ResourceValidator:
    """Validates resource-related inputs and operations"""
    
    # UUID pattern for validation
    UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
    
    # Valid resource types
    VALID_RESOURCE_TYPES = {'principal', 'worker', 'cert', 'key'}
    
    # Valid principal name pattern
    PRINCIPAL_PATTERN = re.compile(r'^[a-zA-Z0-9._-]+@[A-Z0-9.-]+$')
    
    # Valid worker name pattern
    WORKER_PATTERN = re.compile(r'^[a-zA-Z0-9._-]+$')
    
    # Valid CN pattern for certificates
    CN_PATTERN = re.compile(r'^[a-zA-Z0-9._-]+$')
    
    @staticmethod
    def validate_uuid(uuid: str) -> Tuple[bool, Optional[str]]:
        """Validate UUID format"""
        if not uuid:
            return False, "UUID is required"
        
        if not ResourceValidator.UUID_PATTERN.match(uuid):
            return False, "Invalid UUID format"
        
        return True, None
    
    @staticmethod
    def validate_resource_type(resource_type: str) -> Tuple[bool, Optional[str]]:
        """Validate resource type"""
        if not resource_type:
            return False, "Resource type is required"
        
        if resource_type not in ResourceValidator.VALID_RESOURCE_TYPES:
            return False, f"Invalid resource type. Must be one of: {', '.join(ResourceValidator.VALID_RESOURCE_TYPES)}"
        
        return True, None
    
    @staticmethod
    def validate_principal_name(principal_name: str) -> Tuple[bool, Optional[str]]:
        """Validate principal name format"""
        if not principal_name:
            return False, "Principal name is required"
        
        if len(principal_name) > 255:
            return False, "Principal name too long (max 255 characters)"
        
        if not ResourceValidator.PRINCIPAL_PATTERN.match(principal_name):
            return False, "Invalid principal name format. Must be 'name@REALM'"
        
        return True, None
    
    @staticmethod
    def validate_worker_name(worker_name: str) -> Tuple[bool, Optional[str]]:
        """Validate worker name format"""
        if not worker_name:
            return False, "Worker name is required"
        
        if len(worker_name) > 100:
            return False, "Worker name too long (max 100 characters)"
        
        if not ResourceValidator.WORKER_PATTERN.match(worker_name):
            return False, "Invalid worker name format. Must contain only alphanumeric characters, dots, underscores, and hyphens"
        
        if '/' in worker_name or '@' in worker_name:
            return False, "Worker name cannot contain '/' or '@'"
        
        return True, None
    
    @staticmethod
    def validate_cn(cn: str) -> Tuple[bool, Optional[str]]:
        """Validate Common Name for certificates"""
        if not cn:
            return False, "Common Name is required"
        
        if len(cn) > 255:
            return False, "Common Name too long (max 255 characters)"
        
        if not ResourceValidator.CN_PATTERN.match(cn):
            return False, "Invalid Common Name format. Must contain only alphanumeric characters, dots, underscores, and hyphens"
        
        if '/' in cn:
            return False, "Common Name cannot contain '/'"
        
        return True, None
    
    @staticmethod
    def validate_scale_index(scale_index: Optional[int]) -> Tuple[bool, Optional[str]]:
        """Validate scale index"""
        if scale_index is None:
            return True, None  # Scale index is optional
        
        if not isinstance(scale_index, int):
            return False, "Scale index must be an integer"
        
        if scale_index < 0:
            return False, "Scale index must be non-negative"
        
        if scale_index > 9999:
            return False, "Scale index too large (max 9999)"
        
        return True, None
    
    @staticmethod
    def validate_ip_address(ip: str) -> Tuple[bool, Optional[str]]:
        """Validate IP address format"""
        if not ip:
            return False, "IP address is required"
        
        try:
            import ipaddress
            ipaddress.ip_address(ip)
            return True, None
        except ValueError:
            return False, "Invalid IP address format"
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe file operations"""
        if not filename:
            return "unknown"
        
        # Remove or replace dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Limit length
        if len(sanitized) > 255:
            sanitized = sanitized[:255]
        
        return sanitized or "unknown"


class SecurityValidator:
    """Validates security-related operations"""
    
    @staticmethod
    def validate_container_access(container_id: str, client_ip: str) -> Tuple[bool, Optional[str]]:
        """Validate that a container can access resources"""
        if not container_id:
            return False, "Container ID is required"
        
        if not client_ip:
            return False, "Client IP is required"
        
        # Additional security checks could be added here
        # For example, checking if the container is in an allowed network
        
        return True, None
    
    @staticmethod
    def validate_resource_access(uuid: str, container_id: str, resource_type: str) -> Tuple[bool, Optional[str]]:
        """Validate that a container can access a specific resource type"""
        if not uuid:
            return False, "Resource UUID is required"
        
        if not container_id:
            return False, "Container ID is required"
        
        if not resource_type:
            return False, "Resource type is required"
        
        # Additional access control logic could be added here
        # For example, checking if the container has permission for this resource type
        
        return True, None


class RequestValidator:
    """Validates HTTP requests and parameters"""
    
    @staticmethod
    def validate_request_headers(request) -> Tuple[bool, Optional[str]]:
        """Validate request headers"""
        # Check for required headers if any
        # For now, we only require the client to be identifiable by IP
        
        if not request.remote_addr:
            return False, "Unable to determine client IP address"
        
        return True, None
    
    @staticmethod
    def validate_request_method(request, allowed_methods: list) -> Tuple[bool, Optional[str]]:
        """Validate HTTP request method"""
        if request.method not in allowed_methods:
            return False, f"Method not allowed. Allowed methods: {', '.join(allowed_methods)}"
        
        return True, None
    
    @staticmethod
    def validate_json_request(request) -> Tuple[bool, Optional[str]]:
        """Validate JSON request body"""
        if not request.is_json:
            return False, "Request must be JSON"
        
        return True, None


# The end.
