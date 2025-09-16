#!/usr/bin/env python3
"""
V1 API - Legacy compatibility
Maintains existing keytab-service functionality
"""

from flask import Blueprint
from .principal import principal_bp
from .worker import worker_bp
from .cert import cert_bp

# Create main v1 blueprint
bp = Blueprint('v1', __name__)

# Register sub-blueprints
bp.register_blueprint(principal_bp, url_prefix='/principal')
bp.register_blueprint(worker_bp, url_prefix='/worker')
bp.register_blueprint(cert_bp, url_prefix='/cert')

# The end.
