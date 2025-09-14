#!/usr/bin/env python3
"""
V1 Principal API - Legacy compatibility
Maintains existing principal endpoint functionality
"""

import logging
from flask import Blueprint, request, jsonify, send_file, current_app
from urllib.parse import quote_plus as urlquote

logger = logging.getLogger(__name__)
principal_bp = Blueprint('principal', __name__)

@principal_bp.route('/<path:principal_name>')
def get_principal(principal_name):
    """Get or create a principal and return its keytab (V1 API)"""
    try:
        # Get configuration
        krb5_realm = current_app.config.get('KRB5_REALM', 'KOJI.BOX')
        
        # Normalize principal name
        if principal_name.endswith(krb5_realm):
            full_principal_name = principal_name
        else:
            full_principal_name = f"{principal_name}@{krb5_realm}"
        
        # Get resource manager
        resource_manager = current_app.resource_manager
        
        # Check if principal exists
        if not resource_manager.check_principal_exists(full_principal_name):
            logger.info(f"Principal {full_principal_name} does not exist, creating...")
            if not resource_manager.create_principal(full_principal_name):
                return jsonify({'error': 'Failed to create principal'}), 500
        
        # Create keytab
        keytab_path = resource_manager.create_keytab(full_principal_name)
        if not keytab_path:
            return jsonify({'error': 'Failed to create keytab'}), 500
        
        # Serve the keytab
        return send_file(
            str(keytab_path), 
            as_attachment=True, 
            download_name=f"{full_principal_name}.keytab"
        )
        
    except Exception as e:
        logger.error(f"Error in get_principal for {principal_name}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# The end.
