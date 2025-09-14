#!/usr/bin/env python3
"""
Container client for Docker/Podman integration
Handles container identification and metadata retrieval
"""

import re
import logging
from typing import Optional, Dict, List, Tuple
import docker

logger = logging.getLogger(__name__)

class ContainerClient:
    """Client for interacting with Docker/Podman containers"""
    
    def __init__(self, socket_path: str = "/var/run/docker.sock"):
        self.socket_path = socket_path
        self.client = None
        self._connect()
    
    def _connect(self):
        """Connect to Docker daemon"""
        try:
            self.client = docker.DockerClient(base_url=f"unix://{self.socket_path}")
            # Test connection
            self.client.ping()
            logger.info("Connected to Docker daemon")
        except Exception as e:
            logger.error(f"Failed to connect to Docker daemon: {e}")
            self.client = None
    
    def is_connected(self) -> bool:
        """Check if connected to Docker daemon"""
        return self.client is not None
    
    def identify_container_by_ip(self, request_ip: str) -> Tuple[Optional[str], Optional[int]]:
        """
        Identify container by IP address and return (container_id, scale_index)
        Enhanced with multiple fallback methods and better error handling
        """
        if not self.is_connected():
            logger.error("Docker client not connected")
            return None, None
        
        try:
            containers = self.client.containers.list()
            logger.debug(f"Searching {len(containers)} containers for IP {request_ip}")
            
            # Method 1: Direct IP matching
            for container in containers:
                if self._check_container_ip(container, request_ip):
                    logger.info(f"Found container {container.id} for IP {request_ip} (direct match)")
                    scale_index = self._extract_scale_index(container)
                    return container.id, scale_index
            
            # Method 2: Check for containers with similar IPs (subnet matching)
            for container in containers:
                if self._check_container_ip_subnet(container, request_ip):
                    logger.info(f"Found container {container.id} for IP {request_ip} (subnet match)")
                    scale_index = self._extract_scale_index(container)
                    return container.id, scale_index
            
            # Method 3: Check container labels for explicit IP mapping
            for container in containers:
                if self._check_container_ip_label(container, request_ip):
                    logger.info(f"Found container {container.id} for IP {request_ip} (label match)")
                    scale_index = self._extract_scale_index(container)
                    return container.id, scale_index
            
            logger.warning(f"No container found for IP {request_ip}")
            return None, None
            
        except Exception as e:
            logger.error(f"Error identifying container by IP {request_ip}: {e}")
            return None, None
    
    def _check_container_ip(self, container, request_ip: str) -> bool:
        """Check if container has the exact IP address"""
        try:
            networks = container.attrs.get('NetworkSettings', {}).get('Networks', {})
            for network_name, network_info in networks.items():
                container_ip = network_info.get('IPAddress')
                if container_ip == request_ip:
                    return True
            return False
        except Exception as e:
            logger.debug(f"Error checking container IP for {container.id}: {e}")
            return False
    
    def _check_container_ip_subnet(self, container, request_ip: str) -> bool:
        """Check if container IP is in the same subnet as request IP"""
        try:
            import ipaddress
            request_net = ipaddress.ip_network(f"{request_ip}/24", strict=False)
            
            networks = container.attrs.get('NetworkSettings', {}).get('Networks', {})
            for network_name, network_info in networks.items():
                container_ip = network_info.get('IPAddress')
                if container_ip and ipaddress.ip_address(container_ip) in request_net:
                    return True
            return False
        except Exception as e:
            logger.debug(f"Error checking container subnet for {container.id}: {e}")
            return False
    
    def _check_container_ip_label(self, container, request_ip: str) -> bool:
        """Check if container has explicit IP mapping in labels"""
        try:
            labels = container.labels
            if 'orch.client.ip' in labels and labels['orch.client.ip'] == request_ip:
                return True
            if 'orch.ip' in labels and labels['orch.ip'] == request_ip:
                return True
            return False
        except Exception as e:
            logger.debug(f"Error checking container IP label for {container.id}: {e}")
            return False
    
    def _extract_scale_index(self, container) -> Optional[int]:
        """Extract scale index from container metadata"""
        try:
            # Method 1: Parse container name (e.g., koji-worker-3)
            container_name = container.name
            if match := re.search(r'koji-worker-(\d+)', container_name):
                return int(match.group(1))
            
            # Method 2: Check labels
            labels = container.labels
            if 'scale_index' in labels:
                return int(labels['scale_index'])
            if 'orch.scale.index' in labels:
                return int(labels['orch.scale.index'])
            
            # Method 3: Environment variables
            env_vars = container.attrs.get('Config', {}).get('Env', [])
            for env_var in env_vars:
                if env_var.startswith('SCALE_INDEX='):
                    return int(env_var.split('=', 1)[1])
            
            # Method 4: Check for any numeric suffix in name
            if match := re.search(r'-(\d+)$', container_name):
                return int(match.group(1))
            
            logger.debug(f"No scale index found for container {container_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting scale index from container {container.id}: {e}")
            return None
    
    def get_container_info(self, container_id: str) -> Optional[Dict]:
        """Get detailed container information"""
        if not self.is_connected():
            return None
        
        try:
            container = self.client.containers.get(container_id)
            return {
                'id': container.id,
                'name': container.name,
                'status': container.status,
                'labels': container.labels,
                'networks': container.attrs.get('NetworkSettings', {}).get('Networks', {}),
                'env': container.attrs.get('Config', {}).get('Env', [])
            }
        except Exception as e:
            logger.error(f"Error getting container info for {container_id}: {e}")
            return None
    
    def is_container_running(self, container_id: str) -> bool:
        """Check if container is running"""
        if not self.is_connected():
            return False
        
        try:
            container = self.client.containers.get(container_id)
            return container.status == 'running'
        except Exception as e:
            logger.error(f"Error checking container status {container_id}: {e}")
            return False
    
    def get_all_container_ids(self) -> List[str]:
        """Get list of all container IDs"""
        if not self.is_connected():
            return []
        
        try:
            containers = self.client.containers.list()
            return [container.id for container in containers]
        except Exception as e:
            logger.error(f"Error getting container list: {e}")
            return []
    
    def get_container_by_name(self, name: str) -> Optional[Dict]:
        """Get container by name"""
        if not self.is_connected():
            return None
        
        try:
            container = self.client.containers.get(name)
            return {
                'id': container.id,
                'name': container.name,
                'status': container.status,
                'labels': container.labels,
                'networks': container.attrs.get('NetworkSettings', {}).get('Networks', {}),
                'env': container.attrs.get('Config', {}).get('Env', [])
            }
        except Exception as e:
            logger.error(f"Error getting container by name {name}: {e}")
            return None
    
    def cleanup_dead_containers(self, db_manager) -> int:
        """Clean up database entries for containers that no longer exist"""
        if not self.is_connected():
            return 0
        
        try:
            active_container_ids = self.get_all_container_ids()
            return db_manager.cleanup_dead_containers(active_container_ids)
        except Exception as e:
            logger.error(f"Error cleaning up dead containers: {e}")
            return 0


# The end.
