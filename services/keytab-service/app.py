#!/usr/bin/env python3
"""
Principal Service
Flask REST service for managing Koji principals and worker hosts
"""

import os
import sys
import logging
import subprocess
import tempfile
import requests
from pathlib import Path
from flask import Flask, request, jsonify, redirect, send_file, abort
from werkzeug.exceptions import NotFound
from urllib.parse import quote_plus as urlquote

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
PRINCIPALS_DIR = Path('/mnt/data/keytabs')
PRINCIPALS_DIR.mkdir(parents=True, exist_ok=True)

KDC_HOST = os.getenv('KDC_HOST', 'kdc.koji.box')
KRB5_REALM = os.getenv('KRB5_REALM', 'KOJI.BOX')
KADMIN_PRINC = os.getenv('KADMIN_PRINC', f'admin/admin@{KRB5_REALM}')
KADMIN_PASS = os.getenv('KADMIN_PASS', 'admin_password')

CERTS_DIR = Path('/mnt/data/certs')
CERTS_DIR.mkdir(parents=True, exist_ok=True)

# Certificate configuration
CERT_COUNTRY = os.getenv('CERT_COUNTRY', 'US')
CERT_STATE = os.getenv('CERT_STATE', 'NC')
CERT_LOCATION = os.getenv('CERT_LOCATION', 'Raleigh')
CERT_ORG = os.getenv('CERT_ORG', 'Koji')
CERT_ORG_UNIT = os.getenv('CERT_ORG_UNIT', 'Koji')
CERT_DAYS = int(os.getenv('CERT_DAYS', '365'))


def check_principal_exists(principal_name):
    """Check if a principal exists in the KDC"""
    try:
        # Use kadmin to check if principal exists
        cmd = [
            'kadmin', '-p', f'{KADMIN_PRINC}',
            '-w', KADMIN_PASS,
            '-q', f'getprinc {principal_name}'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.stderr and "Principal does not exist" in result.stderr:
            # kadmin isn't returning a non-zero return code when the principal doesn't exist
            return False
        else:
            return result.returncode == 0
    except Exception as e:
        logger.error(f"Error checking principal {principal_name}: {e}")
        raise


def create_principal(principal_name):
    """Create a principal in the KDC"""
    try:
        # Create principal with random key
        cmd = [
            'kadmin', '-p', f'{KADMIN_PRINC}',
            '-w', KADMIN_PASS,
            '-q', f'addprinc -randkey {principal_name}'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            logger.error(f"Failed to create principal {principal_name}: {result.stderr}")
            return False
        logger.info(f"Created principal {principal_name}")
        return True
    except Exception as e:
        logger.error(f"Error creating principal {principal_name}: {e}")
        # return False
        raise


def create_keytab(principal_name):
    """Create a keytab file for the principal"""
    try:
        keytab_path = PRINCIPALS_DIR / f"{urlquote(principal_name)}.keytab"

        # Create keytab using kadmin
        cmd = [
            'kadmin', '-p', f'{KADMIN_PRINC}',
            '-w', KADMIN_PASS,
            '-q', f'ktadd -k {keytab_path} {principal_name}'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            logger.error(f"Failed to create keytab for {principal_name}: {result.stderr}")
            # return False
            raise

        # Set proper permissions
        keytab_path.chmod(0o644)
        logger.info(f"Created keytab for {principal_name} at {keytab_path}")
        return True
    except Exception as e:
        logger.error(f"Error creating keytab for {principal_name}: {e}")
        # return False
        raise


def manage_koji_host(worker_name):
    """Manage Koji host using the shell script"""
    try:
        # Use the shell script to manage the Koji host
        cmd = ['/app/manage-koji-host.sh', worker_name]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            logger.error(f"Failed to manage Koji host {worker_name}: {result.stderr}")
            return False
        logger.info(f"Successfully managed Koji host {worker_name}")
        return True
    except Exception as e:
        logger.error(f"Error managing Koji host {worker_name}: {e}")
        # return False
        raise


def create_certificate(cn):
    """Create SSL certificate and private key for the given CN (Common Name)"""
    try:
        # Sanitize CN for filename
        safe_cn = urlquote(cn)
        key_path = CERTS_DIR / f"{safe_cn}.key"
        crt_path = CERTS_DIR / f"{safe_cn}.crt"

        # Create certificate using openssl
        cmd = [
            'openssl', 'req', '-x509', '-nodes', '-days', str(CERT_DAYS),
            '-newkey', 'rsa:2048',
            '-keyout', str(key_path),
            '-out', str(crt_path),
            '-subj', f"/C={CERT_COUNTRY}/ST={CERT_STATE}/L={CERT_LOCATION}/O={CERT_ORG}/OU={CERT_ORG_UNIT}/CN={cn}"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            logger.error(f"Failed to create certificate for {cn}: {result.stderr}")
            return False

        # Set proper permissions
        key_path.chmod(0o644)
        crt_path.chmod(0o644)

        logger.info(f"Created certificate for {cn} at {crt_path} and key at {key_path}")
        return True
    except Exception as e:
        logger.error(f"Error creating certificate for {cn}: {e}")
        return False


def get_certificate_files(cn):
    """Get or create certificate files for the given CN"""
    try:
        safe_cn = urlquote(cn)
        key_path = CERTS_DIR / f"{safe_cn}.key"
        crt_path = CERTS_DIR / f"{safe_cn}.crt"

        # Check if both files exist
        if key_path.exists() and crt_path.exists():
            logger.info(f"Certificate for {cn} already exists, serving from cache")
            return key_path, crt_path

        # Create certificate if it doesn't exist
        logger.info(f"Creating certificate for {cn}...")
        if not create_certificate(cn):
            return None, None

        return key_path, crt_path
    except Exception as e:
        logger.error(f"Error getting certificate files for {cn}: {e}")
        return None, None


@app.route('/api/v1/principal/<path:principal_name>')
def get_principal(principal_name):
    """Get or create a principal and return its keytab"""
    try:

        if principal_name.endswith(KRB5_REALM):
            full_principal_name = principal_name
            principal_name = principal_name.rstrip(KRB5_REALM)
        else:
            full_principal_name = f"{principal_name}@{KRB5_REALM}"

        keytab_path = PRINCIPALS_DIR / f"{urlquote(full_principal_name)}.keytab"

        # Check if keytab already exists
        if keytab_path.exists():
            logger.info(f"Keytab for {principal_name} already exists, serving from cache")
            return send_file(str(keytab_path), as_attachment=True, download_name=f"{full_principal_name}.keytab")

        # Check if principal exists in KDC
        if not check_principal_exists(full_principal_name):
            logger.info(f"Principal {full_principal_name} does not exist, creating...")
            if not create_principal(full_principal_name):
                return jsonify({'error': 'Failed to create principal'}), 500

        # Create keytab
        if not create_keytab(full_principal_name):
            return jsonify({'error': 'Failed to create keytab'}), 500

        # Serve the keytab
        if keytab_path.exists():
            return send_file(str(keytab_path), as_attachment=True, download_name=f"{full_principal_name}.keytab")
        else:
            return jsonify({'error': 'Keytab file not found after creation'}), 500

    except Exception as e:
        logger.error(f"Error in get_principal for {full_principal_name}: {e}")
        #return jsonify({'error': 'Internal server error'}), 500
        raise


@app.route('/api/v1/worker/<worker_name>')
def get_worker(worker_name):
    """Get or create a worker host and return its keytab"""
    try:
        # Validate worker name
        if not worker_name or '/' in worker_name or '@' in worker_name:
            return jsonify({'error': 'Invalid worker name'}), 400

        principal_name = f"koji/{worker_name}.koji.box"
        full_principal_name = f"{principal_name}@{KRB5_REALM}"
        keytab_path = PRINCIPALS_DIR / f"{urlquote(full_principal_name)}.keytab"

        # Check if keytab already exists
        if keytab_path.exists():
            logger.info(f"Keytab for worker {worker_name} already exists, serving from cache")
            return send_file(str(keytab_path), as_attachment=True, download_name=f"{full_principal_name}.keytab")

        # Check if principal exists in KDC
        if not check_principal_exists(full_principal_name):
            logger.info(f"Principal {full_principal_name} does not exist, creating...")
            if not create_principal(full_principal_name):
                return jsonify({'error': 'Failed to create principal'}), 500

        # Create keytab
        if not create_keytab(full_principal_name):
            return jsonify({'error': 'Failed to create keytab'}), 500

        # Manage Koji host (check if exists, create if not)
        logger.info(f"Managing Koji host for {worker_name}...")
        if not manage_koji_host(worker_name):
            return jsonify({'error': 'Failed to manage Koji host'}), 500

        # Serve the keytab
        if keytab_path.exists():
            return send_file(str(keytab_path), as_attachment=True, download_name=f"{full_principal_name}.keytab")
        else:
            return jsonify({'error': 'Keytab file not found after creation'}), 500

    except Exception as e:
        logger.error(f"Error in get_worker for {full_principal_name}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/v1/cert/<path:cn>')
def get_certificate(cn):
    """Get or create a certificate and return the certificate file"""
    try:
        # Validate CN
        if not cn or '/' in cn:
            return jsonify({'error': 'Invalid CN (Common Name)'}), 400

        key_path, crt_path = get_certificate_files(cn)
        if not key_path or not crt_path:
            return jsonify({'error': 'Failed to create certificate'}), 500

        # Serve the certificate file
        return send_file(str(crt_path), as_attachment=True, download_name=f"{cn}.crt")

    except Exception as e:
        logger.error(f"Error in get_certificate for {cn}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/v1/key/<path:cn>')
def get_private_key(cn):
    """Get or create a certificate and return the private key file"""
    try:
        # Validate CN
        if not cn or '/' in cn:
            return jsonify({'error': 'Invalid CN (Common Name)'}), 400

        key_path, crt_path = get_certificate_files(cn)
        if not key_path or not crt_path:
            return jsonify({'error': 'Failed to create certificate'}), 500

        # Serve the private key file
        return send_file(str(key_path), as_attachment=True, download_name=f"{cn}.key")

    except Exception as e:
        logger.error(f"Error in get_private_key for {cn}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/principals/<path:filename>')
def serve_principal(filename):
    """Serve principal keytab files statically"""
    try:
        file_path = PRINCIPALS_DIR / urlquote(filename)
        if file_path.exists() and file_path.is_file():
            return send_file(str(file_path), as_attachment=True)
        else:
            abort(404)
    except Exception as e:
        logger.error(f"Error serving principal file {filename}: {e}")
        abort(500)


@app.route('/certs/<path:filename>')
def serve_certificate(filename):
    """Serve certificate files statically"""
    try:
        file_path = CERTS_DIR / urlquote(filename)
        if file_path.exists() and file_path.is_file():
            return send_file(str(file_path), as_attachment=True)
        else:
            abort(404)
    except Exception as e:
        logger.error(f"Error serving certificate file {filename}: {e}")
        abort(500)


@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'principal-service'})


@app.route('/')
def index():
    """Root endpoint with service information"""
    return jsonify({
        'service': 'principal-service',
        'version': '1.0.0',
        'endpoints': {
            'principal': '/api/v1/principal/<principal_name>',
            'worker': '/api/v1/worker/<worker_name>',
            'certificate': '/api/v1/cert/<cn>',
            'private_key': '/api/v1/key/<cn>',
            'static_keytabs': '/principals/<filename>',
            'static_certs': '/certs/<filename>',
            'health': '/health'
        }
    })


# The end.
