#!/usr/bin/env python3
"""
V2 API - New UUID-based resource management
Implements secure resource checkout system
"""

from flask import Blueprint
from .resource import resource_bp
from .status import status_bp

# Create main v2 blueprint
bp = Blueprint('v2', __name__)

# Register sub-blueprints
bp.register_blueprint(resource_bp, url_prefix='/resource')
bp.register_blueprint(status_bp, url_prefix='/status')

# The end.
