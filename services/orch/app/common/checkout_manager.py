#!/usr/bin/env python3
"""
Checkout Manager for the Orch service
Handles complex resource checkout logic with security validation
"""

import logging
from typing import Optional, Dict, Tuple
from pathlib import Path

from .database import DatabaseManager
from .resource_manager import ResourceManager
from .container_client import ContainerClient

logger = logging.getLogger("checkout_manager")

class CheckoutManager:
    """Manages resource checkout operations with security validation"""

    def __init__(self, db_manager: DatabaseManager, resource_manager: ResourceManager, container_client: ContainerClient):
        self.db = db_manager
        self.resource_manager = resource_manager
        self.container_client = container_client

    def checkout_resource(self, uuid: str, client_ip: str) -> Tuple[bool, Optional[Path], Optional[str]]:
        """
        Checkout a resource by UUID for a client IP
        Returns: (success, resource_path, error_message)
        """
        try:
            # Step 1: Identify requesting container
            container = self.container_client.get_container_by_ip(client_ip)
            if not container:
                return False, None, "Unable to identify requesting container"

            container_id = container.id

            # Step 2: Verify container is running
            if not self.container_client.is_container_running(container_id):
                return False, None, "Requesting container is not running"

            # Step 3: Get resource mapping
            mapping = self.db.get_resource_mapping(uuid)
            if not mapping:
                return False, None, "Resource not found"

            # Step 4: Determine actual resource name using centralized logic
            actual_resource_name = self.resource_manager.determine_actual_resource_name(
                uuid=uuid,
                container=container,
                resource_mapping=mapping,
                container_client=self.container_client
            )

            # Step 5: Check current checkout status for this specific resource
            status = self.db.get_resource_status(uuid, actual_resource_name)
            if status and status['checked_out']:
                # Check if previous owner is still alive
                if self.container_client.is_container_running(status['container_id']):
                    return False, None, "Resource already checked out to another container"
                else:
                    # Previous owner is dead, clean up
                    logger.info(f"Cleaning up dead container checkout for {uuid} ({actual_resource_name})")
                    self.db.release_resource(uuid, status['container_id'])

            # Step 6: Checkout the resource in database
            if not self.db.checkout_resource(
                uuid=uuid,
                container_id=container_id,
                container_ip=client_ip,
                resource_type=mapping['resource_type'],
                actual_resource_name=actual_resource_name,
            ):
                return False, None, "Failed to checkout resource in database"

            # Step 7: Create/get the actual resource
            try:
                resource_path = self.resource_manager.get_or_create_resource(
                    resource_type=mapping['resource_type'],
                    actual_resource_name=actual_resource_name,
                )

                if not resource_path:
                    # Rollback database checkout
                    self.db.release_resource(uuid, container_id)
                    return False, None, "Failed to create resource"

                logger.info(f"Successfully checked out resource {uuid} to container {container_id}")
                return True, resource_path, None

            except Exception as e:
                # Rollback database checkout
                self.db.release_resource(uuid, container_id)
                logger.error(f"Error creating resource for {uuid}: {e}")
                return False, None, f"Failed to create resource: {str(e)}"

        except Exception as e:
            logger.error(f"Error in checkout_resource for {uuid}: {e}")
            return False, None, f"Internal error: {str(e)}"

    def release_resource(self, uuid: str, client_ip: str) -> Tuple[bool, Optional[str]]:
        """
        Release a resource by UUID for a client IP
        Returns: (success, error_message)
        """
        try:
            # Step 1: Identify requesting container
            container_id, _ = self.container_client.identify_container_by_ip(client_ip)
            if not container_id:
                return False, "Unable to identify requesting container"

            # Step 2: Verify container is running
            if not self.container_client.is_container_running(container_id):
                return False, "Requesting container is not running"

            # Step 3: Release the resource
            if not self.db.release_resource(uuid, container_id):
                return False, "Resource not checked out to this container"

            logger.info(f"Successfully released resource {uuid} from container {container_id}")
            return True, None

        except Exception as e:
            logger.error(f"Error in release_resource for {uuid}: {e}")
            return False, f"Internal error: {str(e)}"

    def get_resource_status(self, uuid: str) -> Optional[Dict]:
        """Get detailed resource status including container validation"""
        try:
            status = self.db.get_resource_status(uuid)
            if not status:
                return None

            # Add container validation if checked out
            if status['checked_out'] and status['container_id']:
                container_info = self.container_client.get_container_info(status['container_id'])
                status['container_info'] = container_info
                status['container_running'] = self.container_client.is_container_running(status['container_id'])

            return status

        except Exception as e:
            logger.error(f"Error in get_resource_status for {uuid}: {e}")
            return None

    def cleanup_dead_containers(self) -> int:
        """Clean up checkouts for containers that no longer exist"""
        try:
            return self.container_client.cleanup_dead_containers(self.db)
        except Exception as e:
            logger.error(f"Error cleaning up dead containers: {e}")
            return 0

    def validate_resource_access(self, uuid: str, client_ip: str) -> Tuple[bool, Optional[str]]:
        """
        Validate if a client can access a resource
        Returns: (can_access, error_message)
        """
        try:
            # Check if resource exists
            mapping = self.db.get_resource_mapping(uuid)
            if not mapping:
                return False, "Resource not found"

            # Determine the specific actual_resource_name using centralized logic
            container = self.container_client.get_container_by_ip(client_ip)
            actual_resource_name = self.resource_manager.determine_actual_resource_name(
                uuid=uuid,
                container=container,
                resource_mapping=mapping,
                container_client=self.container_client
            )

            # Check if this specific resource is checked out
            status = self.db.get_resource_status(uuid, actual_resource_name)
            if not status or not status['checked_out']:
                return True, None  # Resource is available

            # Check if requesting container owns the resource
            container_id, _ = self.container_client.identify_container_by_ip(client_ip)
            if not container_id:
                return False, "Unable to identify requesting container"

            if status['container_id'] == container_id:
                return True, None  # Container owns the resource

            # Check if previous owner is still alive
            if self.container_client.is_container_running(status['container_id']):
                return False, "Resource checked out to another container"
            else:
                # Previous owner is dead, resource can be accessed
                logger.info(f"Previous owner of {uuid} ({actual_resource_name}) is dead, allowing access")
                return True, None

        except Exception as e:
            logger.error(f"Error validating resource access for {uuid}: {e}")
            return False, f"Internal error: {str(e)}"


# The end.
