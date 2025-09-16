#!/usr/bin/env python3
"""
Orch Service - Resource Management System
Main application package
"""

import logging
from os import getenv

from flask import Flask

from .common.ca_certificate_manager import CACertificateManager
from .common.checkout_manager import CheckoutManager
from .common.container_client import ContainerClient
from .common.database import DatabaseManager
from .common.resource_manager import ResourceManager

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)

    # Initialize components
    app.db_manager = DatabaseManager()
    app.ca_manager = CACertificateManager()
    app.resource_manager = ResourceManager(app.db_manager, app.ca_manager)
    app.container_client = ContainerClient()
    app.checkout_manager = CheckoutManager(app.db_manager, app.resource_manager, app.container_client)

    # Load resource mappings
    app.resource_manager.load_resource_mappings()

    # Register blueprints
    #from .v1 import bp as v1_bp
    from .v2 import bp as v2_bp

    # app.register_blueprint(v1_bp, url_prefix='/api/v1')
    app.register_blueprint(v2_bp, url_prefix='/api/v2')

    return app

log_level = getenv('ORCH_LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=getattr(logging, log_level))

logging.info(f"Starting Orch Service with log level: {log_level}")

app = create_app()

# The end.
