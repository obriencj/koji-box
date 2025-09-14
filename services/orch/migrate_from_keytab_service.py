#!/usr/bin/env python3
"""
Migration script from keytab-service to orch service
Helps transition existing containers to use the new UUID-based system
"""

import os
import json
import requests
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class KeytabServiceMigrator:
    """Migrates from keytab-service to orch service"""

    def __init__(self, old_service_url: str, new_service_url: str):
        self.old_service_url = old_service_url
        self.new_service_url = new_service_url
        self.session = requests.Session()

    def get_old_service_status(self) -> Dict[str, Any]:
        """Get status from old keytab service"""
        try:
            response = self.session.get(f"{self.old_service_url}/health")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Old service health check failed: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"Failed to check old service status: {e}")
            return {}

    def get_new_service_status(self) -> Dict[str, Any]:
        """Get status from new orch service"""
        try:
            response = self.session.get(f"{self.new_service_url}/api/v2/status/health")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"New service health check failed: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"Failed to check new service status: {e}")
            return {}

    def get_resource_mappings(self) -> List[Dict[str, Any]]:
        """Get resource mappings from new service"""
        try:
            response = self.session.get(f"{self.new_service_url}/api/v2/status/mappings")
            if response.status_code == 200:
                data = response.json()
                return data.get('mappings', [])
            else:
                logger.error(f"Failed to get resource mappings: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Failed to get resource mappings: {e}")
            return []

    def generate_migration_guide(self) -> str:
        """Generate migration guide for containers"""
        mappings = self.get_resource_mappings()

        guide = """
# Migration Guide: keytab-service to orch service

## Overview
This guide helps you migrate from the old keytab-service to the new orch service.

## Key Changes
1. **API Endpoints**: New V2 API with UUID-based resource access
2. **Authentication**: IP-based container identification instead of direct resource names
3. **Resource Management**: Checkout/release system for resource access control

## Migration Steps

### 1. Update Environment Variables
Add the following environment variables to your containers:

```yaml
# Example for koji-hub container
environment:
  KOJI_HUB_KEYTAB: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  KOJI_HUB_PRINC: "HTTP/koji-hub.koji.box@KOJI.BOX"
  KOJI_NGINX_KEYTAB: "b2c3d4e5-f6g7-8901-bcde-f23456789012"
  KOJI_NGINX_PRINC: "HTTP/koji.box@KOJI.BOX"
```

### 2. Update Container Scripts
Replace direct API calls with UUID-based calls:

**Old way:**
```bash
curl "${KEYTAB_SERVICE_URL}/api/v1/principal/${PRINCIPAL_NAME}" -o keytab
```

**New way:**
```bash
curl -X POST "${ORCH_SERVICE_URL}/api/v2/resource/${RESOURCE_UUID}" -o keytab
```

### 3. Resource Mappings
The following resource mappings are available:
"""

        for mapping in mappings:
            guide += f"""
- **{mapping['uuid']}**: {mapping['resource_type']} - {mapping['actual_resource_name']}
  Description: {mapping.get('description', 'No description')}
"""

        guide += """
### 4. API Endpoints

#### V2 API (New)
- `POST /api/v2/resource/<uuid>` - Checkout resource
- `DELETE /api/v2/resource/<uuid>` - Release resource
- `GET /api/v2/resource/<uuid>/status` - Check resource status
- `GET /api/v2/resource/<uuid>/validate` - Validate access
- `GET /api/v2/status/health` - Health check
- `GET /api/v2/status/mappings` - List all mappings
- `GET /api/v2/docs/` - API documentation

#### V1 API (Legacy - Still Available)
- `GET /api/v1/principal/<name>` - Get principal keytab
- `GET /api/v1/worker/<name>` - Get worker keytab
- `GET /api/v1/cert/<cn>` - Get certificate
- `GET /api/v1/cert/key/<cn>` - Get private key

### 5. Error Handling
The new API provides detailed error responses:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid UUID format",
    "details": {"field": "uuid", "value": "invalid"}
  }
}
```

### 6. Testing
Use the provided test script to verify the migration:

```bash
python test/test_orch_service.py http://orch-service:5000
```

## Rollback Plan
If issues occur, you can temporarily switch back to the old service by:
1. Updating service URLs in environment variables
2. Reverting container scripts to use V1 API calls
3. The old keytab-service will continue to work alongside the new service

## Support
For issues or questions, check the API documentation at `/api/v2/docs/`
"""

        return guide

    def save_migration_guide(self, filename: str = "MIGRATION_GUIDE.md"):
        """Save migration guide to file"""
        guide = self.generate_migration_guide()
        with open(filename, 'w') as f:
            f.write(guide)
        logger.info(f"Migration guide saved to {filename}")

    def check_migration_readiness(self) -> Dict[str, Any]:
        """Check if migration is ready"""
        old_status = self.get_old_service_status()
        new_status = self.get_new_service_status()
        mappings = self.get_resource_mappings()

        return {
            'old_service_healthy': old_status.get('status') == 'healthy',
            'new_service_healthy': new_status.get('status') == 'healthy',
            'mappings_loaded': len(mappings) > 0,
            'mapping_count': len(mappings),
            'ready_for_migration': (
                old_status.get('status') == 'healthy' and
                new_status.get('status') == 'healthy' and
                len(mappings) > 0
            )
        }

def main():
    """Main migration function"""
    import sys

    old_url = sys.argv[1] if len(sys.argv) > 1 else "http://keytabs.koji.box:5000"
    new_url = sys.argv[2] if len(sys.argv) > 2 else "http://orch.koji.box:5000"

    migrator = KeytabServiceMigrator(old_url, new_url)

    print("Checking migration readiness...")
    readiness = migrator.check_migration_readiness()

    print(f"Old service healthy: {readiness['old_service_healthy']}")
    print(f"New service healthy: {readiness['new_service_healthy']}")
    print(f"Mappings loaded: {readiness['mappings_loaded']} ({readiness['mapping_count']} mappings)")
    print(f"Ready for migration: {readiness['ready_for_migration']}")

    if readiness['ready_for_migration']:
        print("\nGenerating migration guide...")
        migrator.save_migration_guide()
        print("Migration guide generated successfully!")
    else:
        print("\nMigration not ready. Please check service health and mappings.")
        sys.exit(1)

if __name__ == "__main__":
    main()

# The end.
