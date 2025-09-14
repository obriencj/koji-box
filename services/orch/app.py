#!/usr/bin/env python3
"""
Orch Service - Resource Management System
Main application entry point
"""

import os
import logging
import subprocess
from flask import Flask, jsonify, redirect
from app import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = create_app()

# Add configuration
app.config['KRB5_REALM'] = os.getenv('KRB5_REALM', 'KOJI.BOX')

@app.route('/')
def index():
    """Root endpoint with service information"""
    return jsonify({
        'service': 'orch-service',
        'version': '2.0.0',
        'description': 'Resource Management System with Container-Based Access Control',
        'endpoints': {
            'v1': {
                'principal': '/api/v1/principal/<principal_name>',
                'worker': '/api/v1/worker/<worker_name>',
                'certificate': '/api/v1/cert/<cn>',
                'private_key': '/api/v1/cert/key/<cn>'
            },
            'v2': {
                'resource': '/api/v2/resource/<uuid>',
                'status': '/api/v2/status/<uuid>',
                'health': '/api/v2/status/health',
                'mappings': '/api/v2/status/mappings'
            }
        }
    })

@app.route('/health')
def health_check():
    """Legacy health check endpoint"""
    return redirect('/api/v2/status/health')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

# The end.
