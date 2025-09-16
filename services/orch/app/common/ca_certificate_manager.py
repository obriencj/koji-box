#!/usr/bin/env python3
"""
CA Certificate Management for the Orch service
Handles CA certificate creation, management, and certificate signing
"""

import os
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import quote_plus as urlquote

logger = logging.getLogger(__name__)

class CACertificateManager:
    """Manages CA certificate creation and certificate signing"""

    def __init__(self):
        # Directory configuration
        self.ca_dir = Path('/mnt/data/ca')
        self.certs_dir = Path('/mnt/data/certs')
        self.ca_dir.mkdir(parents=True, exist_ok=True)
        self.certs_dir.mkdir(parents=True, exist_ok=True)

        # CA file paths
        self.ca_key_path = self.ca_dir / 'ca.key'
        self.ca_cert_path = self.ca_dir / 'ca.crt'
        self.ca_config_path = self.ca_dir / 'ca.conf'

        # Certificate configuration
        self.cert_country = os.getenv('CERT_COUNTRY', 'US')
        self.cert_state = os.getenv('CERT_STATE', 'NC')
        self.cert_location = os.getenv('CERT_LOCATION', 'Raleigh')
        self.cert_org = os.getenv('CERT_ORG', 'Koji Box')
        self.cert_org_unit = os.getenv('CERT_ORG_UNIT', 'Certificate Authority')
        self.cert_days = int(os.getenv('CERT_DAYS', '365'))
        self.ca_cert_days = int(os.getenv('CA_CERT_DAYS', '3650'))  # 10 years for CA

        # CA specific configuration
        self.ca_cn = os.getenv('CA_CN', 'koji-box-ca')
        self.ca_email = os.getenv('CA_EMAIL', 'admin@koji.box')

    def _create_ca_config(self) -> bool:
        """Create OpenSSL configuration file for CA"""
        try:
            config_content = f"""[ca]
default_ca = CA_default

[CA_default]
dir = {self.ca_dir}
certs = $dir
crl_dir = $dir
database = $dir/index.txt
new_certs_dir = $dir
certificate = $dir/ca.crt
serial = $dir/serial
crlnumber = $dir/crlnumber
crl = $dir/crl.pem
private_key = $dir/ca.key
RANDFILE = $dir/.rand

x509_extensions = usr_cert
name_opt = ca_default
cert_opt = ca_default
default_days = {self.cert_days}
default_crl_days = 30
default_md = sha256
preserve = no
policy = policy_strict

[policy_strict]
countryName = match
stateOrProvinceName = match
organizationName = match
organizationalUnitName = optional
commonName = supplied
emailAddress = optional

[policy_loose]
countryName = optional
stateOrProvinceName = optional
localityName = optional
organizationName = optional
organizationalUnitName = optional
commonName = supplied
emailAddress = optional

[req]
default_bits = 2048
distinguished_name = req_distinguished_name
string_mask = utf8only
default_md = sha256
x509_extensions = v3_ca

[req_distinguished_name]
countryName = Country Name (2 letter code)
countryName_default = {self.cert_country}
stateOrProvinceName = State or Province Name
stateOrProvinceName_default = {self.cert_state}
localityName = Locality Name
localityName_default = {self.cert_location}
organizationName = Organization Name
organizationName_default = {self.cert_org}
organizationalUnitName = Organizational Unit Name
organizationalUnitName_default = {self.cert_org_unit}
commonName = Common Name
commonName_default = {self.ca_cn}
emailAddress = Email Address
emailAddress_default = {self.ca_email}

[v3_ca]
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
basicConstraints = critical, CA:true
keyUsage = critical, digitalSignature, cRLSign, keyCertSign

[usr_cert]
basicConstraints = CA:FALSE
nsCertType = client, email
nsComment = "OpenSSL Generated Certificate"
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer
keyUsage = critical, nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth, emailProtection

[server_cert]
basicConstraints = CA:FALSE
nsCertType = server
nsComment = "OpenSSL Generated Server Certificate"
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer:always
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment

[v3_intermediate_ca]
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
basicConstraints = critical, CA:true, pathlen:0
keyUsage = critical, digitalSignature, cRLSign, keyCertSign
"""

            with open(self.ca_config_path, 'w') as f:
                f.write(config_content)

            # Create required files for OpenSSL CA
            (self.ca_dir / 'index.txt').touch()
            (self.ca_dir / 'serial').write_text('1000\n')
            (self.ca_dir / 'crlnumber').write_text('1000\n')

            logger.info(f"Created CA configuration at {self.ca_config_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to create CA configuration: {e}")
            return False

    def create_ca_certificate(self) -> Tuple[Optional[Path], Optional[Path]]:
        """Create CA root key and self-signed certificate"""
        try:
            if self.ca_key_path.exists() and self.ca_cert_path.exists():
                logger.info("CA certificate already exists")
                return self.ca_key_path, self.ca_cert_path

            # Create CA configuration if it doesn't exist
            if not self.ca_config_path.exists():
                if not self._create_ca_config():
                    return None, None

            # Create CA private key
            key_cmd = [
                'openssl', 'genrsa', '-out', str(self.ca_key_path), '2048'
            ]
            result = subprocess.run(key_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                logger.error(f"Failed to create CA private key: {result.stderr}")
                return None, None

            # Create self-signed CA certificate
            cert_cmd = [
                'openssl', 'req', '-new', '-x509', '-days', str(self.ca_cert_days),
                '-key', str(self.ca_key_path),
                '-out', str(self.ca_cert_path),
                '-config', str(self.ca_config_path),
                '-subj', f"/C={self.cert_country}/ST={self.cert_state}/L={self.cert_location}/O={self.cert_org}/OU={self.cert_org_unit}/CN={self.ca_cn}/emailAddress={self.ca_email}"
            ]

            result = subprocess.run(cert_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                logger.error(f"Failed to create CA certificate: {result.stderr}")
                return None, None

            # Set appropriate permissions
            self.ca_key_path.chmod(0o600)  # More restrictive for CA key
            self.ca_cert_path.chmod(0o644)

            logger.info(f"Created CA certificate at {self.ca_cert_path} and key at {self.ca_key_path}")
            return self.ca_key_path, self.ca_cert_path

        except Exception as e:
            logger.error(f"Error creating CA certificate: {e}")
            return None, None

    def get_ca_certificate(self) -> Optional[Path]:
        """Get CA certificate path, creating it if it doesn't exist"""
        try:
            if not self.ca_cert_path.exists():
                logger.info("CA certificate not found, creating...")
                ca_key, ca_cert = self.create_ca_certificate()
                if not ca_cert:
                    return None

            return self.ca_cert_path

        except Exception as e:
            logger.error(f"Error getting CA certificate: {e}")
            return None

    def create_certificate_signed_by_ca(self, cn: str) -> Tuple[Optional[Path], Optional[Path]]:
        """Create a certificate signed by the CA"""
        try:
            safe_cn = urlquote(cn)
            key_path = self.certs_dir / f"{safe_cn}.key"
            crt_path = self.certs_dir / f"{safe_cn}.crt"
            csr_path = self.certs_dir / f"{safe_cn}.csr"

            if key_path.exists() and crt_path.exists():
                logger.info(f"Certificate already exists for {cn}")
                return key_path, crt_path

            # Ensure CA exists
            ca_cert_path = self.get_ca_certificate()
            if not ca_cert_path:
                logger.error("CA certificate not available")
                return None, None

            # Create private key for the certificate
            key_cmd = [
                'openssl', 'genrsa', '-out', str(key_path), '2048'
            ]
            result = subprocess.run(key_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                logger.error(f"Failed to create private key for {cn}: {result.stderr}")
                return None, None

            # Create certificate signing request
            csr_cmd = [
                'openssl', 'req', '-new', '-key', str(key_path),
                '-out', str(csr_path),
                '-config', str(self.ca_config_path),
                '-subj', f"/C={self.cert_country}/ST={self.cert_state}/L={self.cert_location}/O={self.cert_org}/OU={self.cert_org_unit}/CN={cn}"
            ]

            result = subprocess.run(csr_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                logger.error(f"Failed to create CSR for {cn}: {result.stderr}")
                return None, None

            # Sign the certificate with CA
            sign_cmd = [
                'openssl', 'ca', '-batch', '-config', str(self.ca_config_path),
                '-in', str(csr_path),
                '-out', str(crt_path),
                '-days', str(self.cert_days),
                '-extensions', 'server_cert'
            ]

            result = subprocess.run(sign_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                logger.error(f"Failed to sign certificate for {cn}: {result.stderr}")
                return None, None

            # Set appropriate permissions
            key_path.chmod(0o644)
            crt_path.chmod(0o644)

            # Clean up CSR file
            csr_path.unlink(missing_ok=True)

            logger.info(f"Created CA-signed certificate for {cn} at {crt_path} and key at {key_path}")
            return key_path, crt_path

        except Exception as e:
            logger.error(f"Error creating CA-signed certificate for {cn}: {e}")
            return None, None

    def ca_exists(self) -> bool:
        """Check if CA certificate and key exist"""
        return self.ca_key_path.exists() and self.ca_cert_path.exists()

    def get_ca_info(self) -> dict:
        """Get information about the CA certificate"""
        try:
            if not self.ca_exists():
                return {'exists': False}

            # Get certificate information
            info_cmd = [
                'openssl', 'x509', '-in', str(self.ca_cert_path),
                '-text', '-noout'
            ]
            result = subprocess.run(info_cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                logger.error(f"Failed to get CA info: {result.stderr}")
                return {'exists': True, 'error': 'Failed to read certificate'}

            return {
                'exists': True,
                'cert_path': str(self.ca_cert_path),
                'key_path': str(self.ca_key_path),
                'cert_info': result.stdout
            }

        except Exception as e:
            logger.error(f"Error getting CA info: {e}")
            return {'exists': True, 'error': str(e)}

# The end.
