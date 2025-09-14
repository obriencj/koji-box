# Orch Service Improvement Plan
## Resource Management System with Container-Based Access Control

### Executive Summary

This document outlines a comprehensive plan to revamp the current keytab-service (referred to as "orch") to implement resource-based access control using UUID obfuscation and container-based checkout mechanisms. The new system will prevent unauthorized resource access while maintaining the existing functionality for Kerberos keytabs, SSL certificates, and Koji worker management.

### Current State Analysis

#### Existing Keytab Service Capabilities
The current keytab-service provides these endpoints:
- `/api/v1/principal/<principal_name>` - Creates/fetches Kerberos keytabs for principals
- `/api/v1/worker/<worker_name>` - Creates/fetches worker keytabs and registers Koji hosts
- `/api/v1/cert/<cn>` - Creates/fetches SSL certificates
- `/api/v1/key/<cn>` - Creates/fetches SSL private keys
- Static file serving for existing resources

#### Current Security Limitations
- Any container can request any resource by name
- No access control or resource ownership tracking
- Direct resource name exposure in API calls
- No mechanism to prevent resource conflicts during scaling

### Proposed Architecture

#### 1. Resource Types & UUID Mapping System

**Resource Types:**
- `principal` - Kerberos principal keytabs
- `worker` - Koji worker keytabs (with host registration)
- `cert` - SSL certificates
- `key` - SSL private keys

**UUID-Based Resource Mapping:**
Pre-defined mapping file (`resource-mapping.json`) that maps UUIDs to actual resource names:

```json
{
  "a1b2c3d4-e5f6-7890-abcd-ef1234567890": {
    "type": "principal",
    "resource": "hub-admin@KOJI.BOX",
    "description": "Koji hub admin principal"
  },
  "b2c3d4e5-f6g7-8901-bcde-f23456789012": {
    "type": "worker",
    "resource": "koji-worker-1",
    "description": "First Koji worker"
  },
  "c3d4e5f6-g7h8-9012-cdef-345678901234": {
    "type": "cert",
    "resource": "koji-hub.koji.box",
    "description": "Koji hub SSL certificate"
  }
}
```

#### 2. Container Integration & Checkout System

**Docker/Podman Socket Access:**
- Mount container runtime socket into orch container
- Use container runtime API to:
  - Identify requesting container by container ID
  - Check if containers are still running
  - Determine container scale index for scaled resources

**Resource Checkout Database:**
SQLite database to track resource ownership:

```sql
CREATE TABLE resource_checkouts (
    uuid TEXT PRIMARY KEY,
    container_id TEXT NOT NULL,
    checked_out_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resource_type TEXT NOT NULL,
    actual_resource_name TEXT NOT NULL,
    scale_index INTEGER DEFAULT NULL
);

CREATE INDEX idx_container_id ON resource_checkouts(container_id);
CREATE INDEX idx_checked_out_at ON resource_checkouts(checked_out_at);
```

#### 3. New API Design

**Resource Request Endpoints:**
- `POST /api/v2/resource/<uuid>` - Request a resource by UUID
- `DELETE /api/v2/resource/<uuid>` - Release a resource (optional cleanup)
- `GET /api/v2/status/<uuid>` - Check resource status
- `GET /api/v2/health` - Service health check

**Request Flow:**
1. Container requests resource by UUID
2. Orch extracts container ID from request headers or Docker socket
3. Check if resource is already checked out
4. If checked out, verify owning container still exists
5. If available or previous owner is dead, checkout resource to requesting container
6. Create/fetch the actual resource
7. Return resource file

#### 4. Scaled Resource Handling

**Worker Scaling Logic:**
- For worker resources, determine scale index from container name/ID
- Map to actual worker name: `koji-worker-{index}`
- Follow same checkout process
- Register as Koji host if not already registered

**Scale Index Detection Methods:**
1. Parse container name for numeric suffix (e.g., `koji-worker-3`)
2. Use Docker API to get container metadata and labels
3. Handle both single containers and scaled services
4. Fallback to environment variable if needed

#### 5. Implementation Architecture

**Core Components:**

```
services/orch/
├── app.py                    # Main Flask application
├── resource_manager.py       # Resource checkout/management logic
├── container_client.py       # Docker/Podman integration
├── resource_mapping.json     # UUID to resource mapping
├── requirements.txt          # Python dependencies
├── Dockerfile
├── health-check.sh
└── init.d/
    └── 01-setup-db.sh       # Database initialization
```

**New Dependencies:**
- `docker` Python library for container runtime integration
- `sqlite3` for resource tracking (Python stdlib)
- Container runtime socket mount in Docker Compose

**Configuration Options:**
- Resource mapping file location
- Database file location
- Container runtime type (Docker/Podman)
- Socket path configuration
- Resource cleanup policies

#### 6. Error Handling & Edge Cases

**Error Scenarios:**
- Resource not found (invalid UUID)
- Resource already checked out by living container
- Container runtime unavailable
- Resource creation failure
- Scale index detection failure

**Error Responses:**
```json
{
  "error": "Resource not found",
  "code": "RESOURCE_NOT_FOUND",
  "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

#### 7. Migration Strategy

**Phase 1: Parallel Implementation**
- Implement new v2 API alongside existing v1 API
- Add resource mapping and checkout system
- Test with new containers
- Maintain backward compatibility

**Phase 2: Gradual Migration**
- Update containers to use v2 API with UUIDs
- Maintain v1 API for backward compatibility
- Monitor resource usage and performance
- Add comprehensive logging

**Phase 3: Cleanup**
- Remove v1 API once all containers migrated
- Clean up old resource files
- Optimize database performance

### Security Considerations

#### Access Control
- UUID obfuscation prevents direct resource name guessing
- Container-based checkout prevents resource conflicts
- Automatic cleanup of dead container resources
- Resource ownership validation

#### Container Identification
Multiple methods for container identification:
1. **Request Headers**: `X-Container-ID` header
2. **Docker Socket**: Inspect requesting container metadata
3. **Container Name Parsing**: Extract from container name patterns
4. **Environment Variables**: Container-specific environment variables

### Performance Considerations

#### Resource Caching
- Cache created resources to avoid recreation
- Implement resource cleanup policies
- Monitor database performance with large numbers of checkouts

#### Scalability
- SQLite database for single-instance deployment
- Consider PostgreSQL for multi-instance deployments
- Implement connection pooling for container runtime API

### Monitoring & Observability

#### Logging
- Resource checkout/release events
- Container identification success/failure
- Resource creation/retrieval operations
- Error conditions and edge cases

#### Metrics
- Resource checkout rate
- Container identification success rate
- Resource creation time
- Database query performance

### Questions & Considerations

1. **Resource Mapping Management**: How will you maintain the UUID-to-resource mapping? Static file, database, or dynamic generation?

2. **Container Identification**: Preferred method for container identification? Request headers, Docker socket inspection, or hybrid approach?

3. **Resource Cleanup**: Should checked-out resources be automatically cleaned up when containers die, or require explicit release?

4. **Scale Index Detection**: For scaled resources, how should the orch determine the scale index? From container name, environment variables, or Docker metadata?

5. **Backward Compatibility**: Maintain existing v1 API during transition, or make a clean break?

6. **Resource Lifecycle**: Should resources be created on-demand or pre-created and just checked out?

7. **Security Validation**: Any additional validation that containers can only request resources they're authorized for?

### Implementation Timeline

**Week 1-2: Core Infrastructure**
- Set up new service structure
- Implement resource mapping system
- Create database schema and management

**Week 3-4: Container Integration**
- Implement Docker/Podman client
- Add container identification logic
- Implement resource checkout system

**Week 5-6: API Implementation**
- Build new v2 API endpoints
- Add error handling and validation
- Implement scaled resource handling

**Week 7-8: Testing & Migration**
- Comprehensive testing
- Update existing containers
- Performance optimization

### Success Criteria

- [ ] All resources accessible only via UUID
- [ ] Container-based resource checkout working
- [ ] Scaled worker resources properly managed
- [ ] No resource conflicts during scaling
- [ ] Backward compatibility maintained during transition
- [ ] Performance comparable to existing system
- [ ] Comprehensive error handling and logging

### Conclusion

This improved orch service design provides a robust, secure, and scalable resource management system that addresses the current limitations while maintaining the existing functionality. The UUID-based approach with container checkout mechanisms ensures proper access control and prevents resource conflicts, making the system suitable for dynamic container scaling scenarios.

The phased migration approach ensures minimal disruption to existing services while providing a clear path to the improved architecture. The comprehensive error handling and monitoring capabilities will provide excellent observability for troubleshooting and optimization.
