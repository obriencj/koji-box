#!/usr/bin/env python3
"""
Database management for the Orch service
Handles resource mappings, checkouts, and container tracking
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages SQLite database for resource tracking"""

    def __init__(self, db_path: str = "/mnt/data/orch.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    def init_database(self):
        """Initialize database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Resource mappings table - maps UUIDs to actual resources
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resource_mappings (
                    uuid TEXT PRIMARY KEY,
                    resource_type TEXT NOT NULL,
                    actual_resource_name TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Resource aliases table - tracks multiple UUIDs for same resource
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resource_aliases (
                    uuid TEXT PRIMARY KEY,
                    canonical_uuid TEXT NOT NULL,
                    FOREIGN KEY (canonical_uuid) REFERENCES resource_mappings(uuid)
                )
            """)

            # Resource checkouts table - tracks who has checked out what
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resource_checkouts (
                    uuid TEXT NOT NULL,
                    actual_resource_name TEXT NOT NULL,
                    container_id TEXT NOT NULL,
                    container_ip TEXT NOT NULL,
                    checked_out_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resource_type TEXT NOT NULL,
                    scale_index INTEGER DEFAULT NULL,
                    PRIMARY KEY (uuid, actual_resource_name),
                    FOREIGN KEY (uuid) REFERENCES resource_mappings(uuid)
                )
            """)

            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_container_id ON resource_checkouts(container_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_container_ip ON resource_checkouts(container_ip)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_checked_out_at ON resource_checkouts(checked_out_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_resource_type ON resource_mappings(resource_type)")

            conn.commit()
            logger.info("Database initialized successfully")

    def add_resource_mapping(self, uuid: str, resource_type: str, actual_resource_name: str, description: str = None) -> bool:
        """Add a new resource mapping"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO resource_mappings
                    (uuid, resource_type, actual_resource_name, description)
                    VALUES (?, ?, ?, ?)
                """, (uuid, resource_type, actual_resource_name, description))
                conn.commit()
                logger.info(f"Added resource mapping: {uuid} -> {actual_resource_name}")
                return True
        except Exception as e:
            logger.error(f"Failed to add resource mapping {uuid}: {e}")
            return False

    def get_resource_mapping(self, uuid: str) -> Optional[Dict]:
        """Get resource mapping by UUID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT uuid, resource_type, actual_resource_name, description
                    FROM resource_mappings WHERE uuid = ?
                """, (uuid,))
                row = cursor.fetchone()
                if row:
                    return {
                        'uuid': row[0],
                        'resource_type': row[1],
                        'actual_resource_name': row[2],
                        'description': row[3]
                    }
                return None
        except Exception as e:
            logger.error(f"Failed to get resource mapping {uuid}: {e}")
            return None

    def checkout_resource(self, uuid: str, container_id: str, container_ip: str,
                         resource_type: str, actual_resource_name: str, scale_index: int = None) -> bool:
        """Checkout a resource to a container using composite key (uuid, actual_resource_name)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Check if this specific resource (uuid + actual_resource_name) is already checked out
                cursor.execute("""
                    SELECT container_id FROM resource_checkouts
                    WHERE uuid = ? AND actual_resource_name = ?
                """, (uuid, actual_resource_name))
                existing = cursor.fetchone()

                if existing:
                    logger.warning(f"Resource {uuid} ({actual_resource_name}) already checked out to {existing[0]}")
                    return False

                # Checkout the resource
                cursor.execute("""
                    INSERT INTO resource_checkouts
                    (uuid, actual_resource_name, container_id, container_ip, resource_type, scale_index)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (uuid, actual_resource_name, container_id, container_ip, resource_type, scale_index))

                conn.commit()
                logger.info(f"Checked out resource {uuid} ({actual_resource_name}) to container {container_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to checkout resource {uuid} ({actual_resource_name}): {e}")
            return False

    def release_resource(self, uuid: str, container_id: str) -> bool:
        """Release a resource from a container using composite key"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Find all resources for this UUID and container combination
                cursor.execute("""
                    SELECT actual_resource_name, container_id FROM resource_checkouts
                    WHERE uuid = ? AND container_id = ?
                """, (uuid, container_id))
                resources = cursor.fetchall()

                if not resources:
                    logger.warning(f"No resources with UUID {uuid} checked out to container {container_id}")
                    return False

                # Release all matching resources (should typically be just one)
                cursor.execute("""
                    DELETE FROM resource_checkouts
                    WHERE uuid = ? AND container_id = ?
                """, (uuid, container_id))

                released_count = cursor.rowcount
                conn.commit()

                for resource in resources:
                    logger.info(f"Released resource {uuid} ({resource[0]}) from container {container_id}")

                logger.info(f"Released {released_count} resource(s) with UUID {uuid} from container {container_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to release resource {uuid} from container {container_id}: {e}")
            return False

    def get_resource_status(self, uuid: str, actual_resource_name: str = None) -> Optional[Dict]:
        """Get current status of a resource, optionally for a specific actual_resource_name"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Get resource mapping
                cursor.execute("""
                    SELECT uuid, resource_type, actual_resource_name, description
                    FROM resource_mappings WHERE uuid = ?
                """, (uuid,))
                mapping = cursor.fetchone()

                if not mapping:
                    return None

                # Get checkout status - if actual_resource_name specified, check for that specific resource
                if actual_resource_name:
                    cursor.execute("""
                        SELECT container_id, container_ip, checked_out_at, scale_index
                        FROM resource_checkouts WHERE uuid = ? AND actual_resource_name = ?
                    """, (uuid, actual_resource_name))
                    checkout = cursor.fetchone()

                    return {
                        'uuid': mapping[0],
                        'resource_type': mapping[1],
                        'actual_resource_name': actual_resource_name,
                        'description': mapping[3],
                        'checked_out': checkout is not None,
                        'container_id': checkout[0] if checkout else None,
                        'container_ip': checkout[1] if checkout else None,
                        'checked_out_at': checkout[2] if checkout else None,
                        'scale_index': checkout[3] if checkout else None
                    }
                else:
                    # For backward compatibility, get first checkout if any exist
                    cursor.execute("""
                        SELECT container_id, container_ip, checked_out_at, scale_index, actual_resource_name
                        FROM resource_checkouts WHERE uuid = ? LIMIT 1
                    """, (uuid,))
                    checkout = cursor.fetchone()

                    return {
                        'uuid': mapping[0],
                        'resource_type': mapping[1],
                        'actual_resource_name': checkout[4] if checkout else mapping[2],
                        'description': mapping[3],
                        'checked_out': checkout is not None,
                        'container_id': checkout[0] if checkout else None,
                        'container_ip': checkout[1] if checkout else None,
                        'checked_out_at': checkout[2] if checkout else None,
                        'scale_index': checkout[3] if checkout else None
                    }
        except Exception as e:
            logger.error(f"Failed to get resource status {uuid}: {e}")
            return None

    def cleanup_dead_containers(self, active_container_ids: List[str]) -> int:
        """Clean up checkouts for containers that no longer exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Find checkouts for dead containers
                placeholders = ','.join('?' * len(active_container_ids))
                cursor.execute(f"""
                    DELETE FROM resource_checkouts
                    WHERE container_id NOT IN ({placeholders})
                """, active_container_ids)

                cleaned = cursor.rowcount
                conn.commit()

                if cleaned > 0:
                    logger.info(f"Cleaned up {cleaned} checkouts for dead containers")

                return cleaned
        except Exception as e:
            logger.error(f"Failed to cleanup dead containers: {e}")
            return 0

    def get_all_mappings(self) -> List[Dict]:
        """Get all resource mappings"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT uuid, resource_type, actual_resource_name, description
                    FROM resource_mappings ORDER BY created_at
                """)
                rows = cursor.fetchall()
                return [
                    {
                        'uuid': row[0],
                        'resource_type': row[1],
                        'actual_resource_name': row[2],
                        'description': row[3]
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Failed to get all mappings: {e}")
            return []


# The end.
