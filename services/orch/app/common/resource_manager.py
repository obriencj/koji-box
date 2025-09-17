#!/usr/bin/env python3
"""
Resource management for the Orch service
Handles resource creation, mapping, and lifecycle management
"""

import os
import yaml
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.parse import quote_plus as urlquote

from .database import DatabaseManager

logger = logging.getLogger("resource_manager")

class ResourceManager:
    """Manages resource creation and lifecycle"""

    def __init__(self, db_manager: DatabaseManager, ca_manager=None):
        self.db = db_manager
        self.ca_manager = ca_manager

        # Configuration from environment
        self.krb5_realm = os.getenv('KRB5_REALM', 'KOJI.BOX')
        self.kdc_host = os.getenv('KDC_HOST', 'kdc.koji.box')
        self.kadmin_princ = os.getenv('KADMIN_PRINC', f'admin/admin@{self.krb5_realm}')
        self.kadmin_pass = os.getenv('KADMIN_PASS', 'admin_password')

        # Directory configuration
        self.keytabs_dir = Path('/mnt/data/keytabs')
        self.certs_dir = Path('/mnt/data/certs')
        self.keytabs_dir.mkdir(parents=True, exist_ok=True)
        self.certs_dir.mkdir(parents=True, exist_ok=True)

        # Certificate configuration
        self.cert_country = os.getenv('CERT_COUNTRY', 'US')
        self.cert_state = os.getenv('CERT_STATE', 'NC')
        self.cert_location = os.getenv('CERT_LOCATION', 'Raleigh')
        self.cert_org = os.getenv('CERT_ORG', 'Koji')
        self.cert_org_unit = os.getenv('CERT_ORG_UNIT', 'Koji')
        self.cert_days = int(os.getenv('CERT_DAYS', '365'))

    def load_resource_mappings(self, mapping_file: str = "/app/resource_mapping.yaml") -> bool:
        """Load resource mappings from generated YAML file"""
        try:
            mapping_path = Path(mapping_file)
            if not mapping_path.exists():
                logger.error(f"Resource mapping file not found: {mapping_file}")
                return False

            with open(mapping_path, 'r') as f:
                mappings = yaml.safe_load(f)

            loaded_count = 0
            for uuid, mapping in mappings.items():
                if self.db.add_resource_mapping(
                    uuid=uuid,
                    resource_type=mapping['type'],
                    actual_resource_name=mapping['resource'],
                    description=mapping.get('description', '')
                ):
                    loaded_count += 1

            logger.info(f"Loaded {loaded_count} resource mappings")
            return True
        except Exception as e:
            logger.error(f"Failed to load resource mappings: {e}")
            return False

    def create_principal(self, principal_name: str) -> bool:
        """Create a Kerberos principal"""
        try:
            cmd = [
                'kadmin', '-p', f'{self.kadmin_princ}',
                '-w', self.kadmin_pass,
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
            return False

    def check_principal_exists(self, principal_name: str) -> bool:
        """Check if a principal exists in the KDC"""
        try:
            cmd = [
                'kadmin', '-p', f'{self.kadmin_princ}',
                '-w', self.kadmin_pass,
                '-q', f'getprinc {principal_name}'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.stderr and "Principal does not exist" in result.stderr:
                return False
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error checking principal {principal_name}: {e}")
            return False

    def create_keytab(self, principal_name: str) -> Optional[Path]:
        """Create a keytab file for the principal"""
        try:
            keytab_path = self.keytabs_dir / f"{urlquote(principal_name)}.keytab"

            if keytab_path.exists():
                logger.info(f"Keytab already exists: {keytab_path}")
                return keytab_path

            cmd = [
                'kadmin', '-p', f'{self.kadmin_princ}',
                '-w', self.kadmin_pass,
                '-q', f'ktadd -k {keytab_path} {principal_name}'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                logger.error(f"Failed to create keytab for {principal_name}: {result.stderr}")
                return None

            keytab_path.chmod(0o644)
            logger.info(f"Created keytab for {principal_name} at {keytab_path}")
            return keytab_path
        except Exception as e:
            logger.error(f"Error creating keytab for {principal_name}: {e}")
            return None

    def create_certificate(self, cn: str) -> Tuple[Optional[Path], Optional[Path]]:
        """Create SSL certificate and private key"""
        try:
            # If CA manager is available, use CA-signed certificates
            if self.ca_manager:
                logger.info(f"Creating CA-signed certificate for {cn}")
                return self.ca_manager.create_certificate_signed_by_ca(cn)
            else:
                # Fallback to self-signed certificates for backward compatibility
                logger.info(f"Creating self-signed certificate for {cn} (no CA manager)")
                return self._create_self_signed_certificate(cn)
        except Exception as e:
            logger.error(f"Error creating certificate for {cn}: {e}")
            return None, None

    def _create_self_signed_certificate(self, cn: str) -> Tuple[Optional[Path], Optional[Path]]:
        """Create self-signed SSL certificate and private key (fallback method)"""
        try:
            safe_cn = urlquote(cn)
            key_path = self.certs_dir / f"{safe_cn}.key"
            crt_path = self.certs_dir / f"{safe_cn}.crt"

            if key_path.exists() and crt_path.exists():
                logger.info(f"Certificate already exists for {cn}")
                return key_path, crt_path

            cmd = [
                'openssl', 'req', '-x509', '-nodes', '-days', str(self.cert_days),
                '-newkey', 'rsa:2048',
                '-keyout', str(key_path),
                '-out', str(crt_path),
                '-subj', f"/C={self.cert_country}/ST={self.cert_state}/L={self.cert_location}/O={self.cert_org}/OU={self.cert_org_unit}/CN={cn}"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                logger.error(f"Failed to create certificate for {cn}: {result.stderr}")
                return None, None

            key_path.chmod(0o644)
            crt_path.chmod(0o644)

            logger.info(f"Created self-signed certificate for {cn} at {crt_path} and key at {key_path}")
            return key_path, crt_path
        except Exception as e:
            logger.error(f"Error creating self-signed certificate for {cn}: {e}")
            return None, None

    def manage_koji_host(self, worker_name: str, full_principal_name: str, arch: str = None) -> bool:
        """Manage Koji host using the shell script"""

        try:
            cmd = ['/app/manage-koji-host.sh', worker_name, full_principal_name]
            if arch:
                cmd.append(arch)
            result = subprocess.run(cmd, capture_output=False, text=True, timeout=60)
            if result.returncode != 0:
                logger.error(f"Failed to manage Koji host {worker_name}: {result.stderr}")
                return False
            logger.info(f"Successfully managed Koji host {worker_name}")
            return True
        except Exception as e:
            logger.error(f"Error managing Koji host {worker_name}: {e}")
            return False

    def determine_actual_resource_name(self, uuid: str, container, resource_mapping: Dict, container_client=None) -> str:
        """
        Determine the actual resource name for a given UUID and container.
        This is the centralized logic for all resource types.

        Args:
            uuid: The resource UUID
            container: The requesting container object
            resource_mapping: The resource mapping dict from database
            container_client: Optional ContainerClient instance for scale index extraction

        Returns:
            The actual resource name to use for this container/resource combination
        """
        try:
            base_name = resource_mapping['actual_resource_name']
            resource_type = resource_mapping['resource_type']

            # For worker resources, append scale index
            if resource_type == 'worker':
                if not container:
                    logger.error(f"Container required for worker resource {uuid}")
                    return base_name

                # Get scale index from container using container_client if available
                if container_client:
                    scale_index = container_client.get_scale_index(container)
                else:
                    # Fallback to direct extraction if no container_client provided
                    scale_index = self._extract_scale_index_fallback(container)

                # Get service name from container labels
                service_name = base_name  # Default fallback
                if hasattr(container, 'labels') and container.labels:
                    service_name = container.labels.get('io.podman.compose.service', base_name)

                # Build scaled resource name
                actual_name = f"{service_name}-{scale_index}"
                logger.debug(f"Worker resource {uuid}: {base_name} -> {actual_name} (scale_index={scale_index})")
                return actual_name

            # For all other resource types, use base name as-is
            logger.debug(f"Non-worker resource {uuid}: using base name {base_name}")
            return base_name

        except Exception as e:
            logger.error(f"Error determining actual resource name for {uuid}: {e}")
            return resource_mapping.get('actual_resource_name', 'unknown')

    def _extract_scale_index_fallback(self, container) -> int:
        """Fallback method to extract scale index when no ContainerClient is available"""
        try:
            if not hasattr(container, 'labels'):
                return 0

            labels = container.labels or {}

            # Try different label formats
            if 'scale_index' in labels:
                return int(labels['scale_index'])
            elif 'orch.scale.index' in labels:
                return int(labels['orch.scale.index'])
            else:
                # Try environment variables if available
                if hasattr(container, 'attrs') and 'Config' in container.attrs:
                    env_vars = container.attrs['Config'].get('Env', [])
                    for env_var in env_vars:
                        if env_var.startswith('SCALE_INDEX='):
                            return int(env_var.split('=', 1)[1])

                logger.debug(f"No scale index found for container {container.id}, using 0")
                return 0

        except (ValueError, AttributeError) as e:
            logger.error(f"Error extracting scale index from container {getattr(container, 'id', 'unknown')}: {e}")
            return 0

    def get_or_create_resource(self, resource_type: str, actual_resource_name: str) -> Optional[Path]:
        """Get or create a resource based on type and name"""
        try:
            if resource_type == "principal":
                return self._get_or_create_principal(actual_resource_name)
            elif resource_type == "worker":
                return self._get_or_create_worker(actual_resource_name)
            elif resource_type == "cert":
                return self._get_or_create_certificate(actual_resource_name)
            elif resource_type == "key":
                return self._get_or_create_private_key(actual_resource_name)
            else:
                logger.error(f"Unknown resource type: {resource_type}")
                return None
        except Exception as e:
            logger.error(f"Error getting/creating resource {actual_resource_name}: {e}")
            return None

    def _get_or_create_principal(self, principal_name: str) -> Optional[Path]:
        """Get or create a principal keytab"""
        # Ensure principal exists
        if not self.check_principal_exists(principal_name):
            if not self.create_principal(principal_name):
                return None

        # Create keytab
        return self.create_keytab(principal_name)

    def _get_or_create_worker(self, worker_name: str, arch: str = None) -> Optional[Path]:
        """Get or create a worker keytab and register host"""
        # Handle scaled resources

        if not worker_name.startswith('worker/'):
            worker_name = f"worker/{worker_name}"
        principal_name = f"{worker_name}@{self.krb5_realm}"

        # Ensure principal exists
        if not self.check_principal_exists(principal_name):
            if not self.create_principal(principal_name):
                return None

        # Create keytab
        keytab_path = self.create_keytab(principal_name)
        if not keytab_path:
            return None

        # Register as Koji host
        if not self.manage_koji_host(worker_name, principal_name, arch):
            logger.warning(f"Failed to register Koji host {worker_name}")
            return None

        return keytab_path

    def _get_or_create_certificate(self, cn: str) -> Optional[Path]:
        """Get or create an SSL certificate"""
        key_path, crt_path = self.create_certificate(cn)
        return crt_path

    def _get_or_create_private_key(self, cn: str) -> Optional[Path]:
        """Get or create an SSL private key"""
        key_path, crt_path = self.create_certificate(cn)
        return key_path


# The end.
