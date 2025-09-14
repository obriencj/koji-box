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

### Design Decisions & Implementation Details

1. **Resource Mapping Management**:
   - **Approach**: Environment variable-based mapping in docker-compose.yml
   - **Implementation**: Use `envsubst` to generate resource mapping JSON from environment variables
   - **Example**: `KOJI_HUB_KEYTAB=some_uuid_here` → maps to `KOJI_HUB_PRINC` principal
   - **Database Integration**: Orch reads all relevant env vars at startup and populates database

2. **Container Identification**:
   - **Method**: Requestor IP address → Docker socket API lookup
   - **Process**: Extract client IP from request, query Docker API for container with matching IP
   - **Fallback**: Container name parsing if IP lookup fails

3. **Resource Cleanup**:
   - **Approach**: Explicit release with ownership validation
   - **Logic**: Check if requestor owns resource OR if previous owner is dead
   - **Security**: Deny release if different living container owns resource

4. **Scale Index Detection**:
   - **Method**: IP address → Docker socket API → extract scale number from container metadata
   - **Process**: Same as container identification, then parse scale index from container name/labels

5. **Backward Compatibility**:
   - **Decision**: Maintain v1 API during transition
   - **Implementation**: Refactor app.py into app/ package with separate blueprints
   - **Structure**: `app/v1/` and `app/v2/` blueprints for clean separation

6. **Resource Lifecycle**:
   - **Approach**: Lazy creation (on-demand)
   - **Benefit**: Reduces startup time and resource usage
   - **Implementation**: Create resources only when first checked out

7. **Security Validation**:
   - **Authorization**: UUID possession = authorization
   - **Multi-UUID Support**: Same resource can have multiple UUIDs for different containers
   - **Example**: `hub-admin` keytab could have separate UUIDs for hub and web containers

### Additional Implementation Considerations

#### Environment Variable Management
**Docker Compose Integration:**
```yaml
# Example environment variable distribution
services:
  koji-hub:
    environment:
      KOJI_HUB_KEYTAB: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
      KOJI_HUB_PRINC: "HTTP/koji-hub.koji.box@KOJI.BOX"
      KOJI_NGINX_KEYTAB: "b2c3d4e5-f6g7-8901-bcde-f23456789012"
      KOJI_NGINX_PRINC: "HTTP/koji.box@KOJI.BOX"

  koji-web:
    environment:
      KOJI_WEB_KEYTAB: "c3d4e5f6-g7h8-9012-cdef-345678901234"
      KOJI_WEB_PRINC: "HTTP/koji-web.koji.box@KOJI.BOX"
```

**Resource Mapping Template:**
```json
{
  "${KOJI_HUB_KEYTAB}": {
    "type": "principal",
    "resource": "${KOJI_HUB_PRINC}",
    "description": "Koji hub principal keytab"
  },
  "${KOJI_NGINX_KEYTAB}": {
    "type": "principal",
    "resource": "${KOJI_NGINX_PRINC}",
    "description": "Nginx principal keytab"
  },
  "${KOJI_WORKER_KEYTAB}": {
    "type": "worker",
    "resource": "koji-worker-${SCALE_INDEX}",
    "description": "Koji worker keytab (scaled)"
  }
}
```

#### Container Identification Challenges
**IP Address Resolution:**
- **Challenge**: Containers may have multiple IPs (bridge, host, etc.)
- **Solution**: Check all container IPs against requestor IP
- **Fallback**: Use container name patterns if IP matching fails

**Docker Socket Access:**
- **Mount**: `/var/run/docker.sock:/var/run/docker.sock:ro`
- **API**: Use Docker Python SDK for container inspection
- **Performance**: Cache container metadata to reduce API calls

#### Multi-UUID Resource Management
**Database Schema Updates:**
```sql
-- Track multiple UUIDs for same resource
CREATE TABLE resource_mappings (
    uuid TEXT PRIMARY KEY,
    resource_type TEXT NOT NULL,
    actual_resource_name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Track which UUIDs map to same underlying resource
CREATE TABLE resource_aliases (
    uuid TEXT PRIMARY KEY,
    canonical_uuid TEXT NOT NULL,
    FOREIGN KEY (canonical_uuid) REFERENCES resource_mappings(uuid)
);
```

**Resource Sharing Logic:**
- Multiple containers can have different UUIDs for same resource
- Only one container can checkout each UUID at a time
- Resource creation happens only once per actual resource name
- File sharing: Multiple UUIDs can serve the same physical file

#### Scale Index Detection Implementation
**Container Metadata Parsing:**
```python
def get_scale_index(container_id):
    """Extract scale index from container metadata"""
    container = docker_client.containers.get(container_id)

    # Method 1: Parse container name (e.g., koji-worker-3)
    if match := re.search(r'koji-worker-(\d+)', container.name):
        return int(match.group(1))

    # Method 2: Check labels
    if 'scale_index' in container.labels:
        return int(container.labels['scale_index'])

    # Method 3: Environment variable
    if 'SCALE_INDEX' in container.attrs['Config']['Env']:
        return int(container.attrs['Config']['Env']['SCALE_INDEX'])

    return None
```

#### Application Structure Refactoring
**New Package Structure:**
```
services/orch/
├── app/
│   ├── __init__.py
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── principal.py
│   │   ├── worker.py
│   │   └── cert.py
│   ├── v2/
│   │   ├── __init__.py
│   │   ├── resource.py
│   │   └── status.py
│   └── common/
│       ├── __init__.py
│       ├── container_client.py
│       ├── resource_manager.py
│       └── database.py
├── templates/
│   └── resource_mapping.json.template
├── requirements.txt
└── Dockerfile
```

#### Potential Issues & Mitigations

**Issue 1: IP Address Changes**
- **Problem**: Container IPs may change during restarts
- **Mitigation**: Use container name + network inspection for more reliable identification

**Issue 2: Docker Socket Security**
- **Problem**: Read-only access may not be sufficient for all operations
- **Mitigation**: Use Docker API with minimal required permissions

**Issue 3: Resource File Conflicts**
- **Problem**: Multiple UUIDs serving same file may cause permission issues
- **Mitigation**: Use symlinks or copy-on-write for shared resources

**Issue 4: Environment Variable Complexity**
- **Problem**: Many environment variables to manage
- **Mitigation**: Use structured naming conventions and validation

**Issue 5: Scale Index Detection Reliability**
- **Problem**: Scale index detection may fail in some scenarios
- **Mitigation**: Multiple fallback methods and clear error messages

### Critical Concerns & Recommendations

#### 1. IP Address-Based Container Identification
**Concern**: Using IP addresses for container identification is inherently fragile
- Container IPs can change during restarts
- Multiple containers may share IPs in some network configurations
- Docker networking can be complex with overlays, bridges, etc.

**Recommendation**:
- Primary: Use container name + network inspection
- Fallback: IP address matching
- Add container labels for explicit identification

#### 2. Environment Variable Management Complexity
**Concern**: Managing UUIDs via environment variables could become unwieldy
- Many environment variables to track
- Risk of UUID conflicts or typos
- Difficult to validate all mappings

**Recommendation**:
- Use structured naming: `{SERVICE}_{RESOURCE_TYPE}_{UUID}`
- Add validation script to check for conflicts
- Consider using a separate mapping service

#### 3. Multi-UUID Resource Sharing
**Concern**: Multiple UUIDs for same resource creates complexity
- Database schema becomes more complex
- Resource cleanup logic needs to handle multiple owners
- File sharing between UUIDs needs careful implementation

**Recommendation**:
- Implement canonical UUID concept
- Use symlinks for shared files
- Add resource dependency tracking

#### 4. Docker Socket Security
**Concern**: Mounting Docker socket creates security implications
- Even read-only access can leak sensitive information
- Container metadata may contain secrets
- Network inspection requires elevated permissions

**Recommendation**:
- Use Docker API with minimal required permissions
- Implement container metadata filtering
- Consider using Docker labels for identification instead

#### 5. Scale Index Detection Edge Cases
**Concern**: Scale index detection may fail in various scenarios
- Containers without predictable naming
- Custom scaling solutions
- Container restarts with different names

**Recommendation**:
- Make scale index explicit via environment variables
- Use Docker labels for scale information
- Provide clear error messages for detection failures

### Alternative Approaches to Consider

#### Option 1: Request Header-Based Identification
Instead of IP-based identification, use request headers:
```http
X-Container-ID: abc123def456
X-Scale-Index: 3
X-Resource-UUID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Pros**: More reliable, explicit, easier to debug
**Cons**: Requires container modification, can be spoofed

#### Option 2: Container Label-Based Mapping
Use Docker labels to map containers to resources:
```yaml
services:
  koji-worker-1:
    labels:
      - "orch.resource.uuid=a1b2c3d4-e5f6-7890-abcd-ef1234567890"
      - "orch.resource.type=worker"
      - "orch.scale.index=1"
```

**Pros**: No IP dependency, explicit mapping, Docker-native
**Cons**: Requires container restart to change mappings

#### Option 3: Hybrid Approach
Combine multiple identification methods:
1. Try request headers first
2. Fall back to IP + Docker socket
3. Use container labels as final fallback

**Pros**: Most reliable, graceful degradation
**Cons**: More complex implementation

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
