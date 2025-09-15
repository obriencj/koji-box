# Orch Service - Resource Management System

The Orch service is a comprehensive resource management system that provides secure, container-based access control for Koji infrastructure resources including Kerberos keytabs, SSL certificates, and Koji worker management.

## Features

### 🔐 Security-First Design
- **IP-based container identification** - No trust in request headers
- **Resource checkout system** - Prevents unauthorized access
- **Automatic cleanup** - Dead container resource cleanup
- **UUID obfuscation** - Resources accessed via UUIDs, not names

### 🚀 Scalable Architecture
- **Multi-UUID support** - Same resource can have multiple UUIDs
- **Scaled worker support** - Automatic scale index detection
- **Background cleanup** - Automatic dead container cleanup
- **Comprehensive logging** - Detailed audit trails

### 🔄 Backward Compatibility
- **V1 API preserved** - Existing keytab-service functionality
- **V2 API enhanced** - New UUID-based system with CA certificate support
- **Gradual migration** - Both APIs can run simultaneously

### 🔐 Certificate Authority (CA) Support
- **Self-managed CA** - Creates and manages its own root CA certificate
- **CA-signed certificates** - All SSL certificates are signed by the CA
- **Public CA access** - CA certificate accessible without authentication
- **System integration** - Easy installation to system trust stores

## Quick Start

### 1. Build and Run
```bash
# Build the service
docker build -f services/orch/Dockerfile -t orch-service .

# Run with Docker Compose
docker-compose up orch-service
```

### 2. Test the Service
```bash
# Run test suite
python services/orch/test/test_orch_service.py http://orch.koji.box:5000

# Check health
curl http://orch.koji.box:5000/api/v2/status/health

# View API documentation
curl http://orch.koji.box:5000/api/v2/docs/
```

## API Reference

### V2 API (New - Recommended)

#### Resource Management
- `POST /api/v2/resource/<uuid>` - Checkout a resource
- `DELETE /api/v2/resource/<uuid>` - Release a resource
- `GET /api/v2/resource/<uuid>/status` - Get resource status
- `GET /api/v2/resource/<uuid>/validate` - Validate access

#### Certificate Authority (CA)
- `GET /api/v2/ca/certificate` - Get CA certificate (public key only)
- `GET /api/v2/ca/info` - Get CA certificate information
- `GET /api/v2/ca/status` - Get CA status

#### Status and Information
- `GET /api/v2/status/health` - Health check
- `GET /api/v2/status/mappings` - List all resource mappings
- `GET /api/v2/docs/` - API documentation

### V1 API (Legacy - Backward Compatibility)

#### Direct Resource Access
- `GET /api/v1/principal/<name>` - Get principal keytab
- `GET /api/v1/worker/<name>` - Get worker keytab
- `GET /api/v1/cert/<cn>` - Get SSL certificate
- `GET /api/v1/cert/key/<cn>` - Get SSL private key

## Configuration

### Environment Variables

#### Service Configuration
- `KRB5_REALM` - Kerberos realm (default: KOJI.BOX)
- `KDC_HOST` - KDC hostname (default: kdc.koji.box)
- `KADMIN_PRINC` - Kadmin principal (default: admin/admin@KOJI.BOX)
- `KADMIN_PASS` - Kadmin password (default: admin_password)

#### Resource UUIDs
- `KOJI_HUB_KEYTAB` - Hub principal keytab UUID
- `KOJI_HUB_PRINC` - Hub principal name
- `KOJI_NGINX_KEYTAB` - Nginx principal keytab UUID
- `KOJI_NGINX_PRINC` - Nginx principal name
- `KOJI_WEB_KEYTAB` - Web principal keytab UUID
- `KOJI_WEB_PRINC` - Web principal name
- `KOJI_ADMIN_KEYTAB` - Admin principal keytab UUID
- `KOJI_ADMIN_PRINC` - Admin principal name
- `KOJI_WORKER_KEYTAB` - Worker keytab UUID (scaled)
- `KOJI_HUB_CERT` - Hub SSL certificate UUID
- `KOJI_HUB_CERT_CN` - Hub certificate CN
- `KOJI_HUB_KEY` - Hub SSL private key UUID
- `KOJI_NGINX_CERT` - Nginx SSL certificate UUID
- `KOJI_NGINX_CERT_CN` - Nginx certificate CN
- `KOJI_NGINX_KEY` - Nginx SSL private key UUID

#### CA Certificate Configuration
- `CA_CERT_DAYS` - CA certificate validity period in days (default: 3650)
- `CERT_DAYS` - Regular certificate validity period in days (default: 365)
- `CA_CN` - CA certificate Common Name (default: koji-box-ca)
- `CA_EMAIL` - CA certificate email address (default: admin@koji.box)
- `CERT_COUNTRY` - Certificate country code (default: US)
- `CERT_STATE` - Certificate state/province (default: NC)
- `CERT_LOCATION` - Certificate locality (default: Raleigh)
- `CERT_ORG` - Certificate organization (default: Koji Box)
- `CERT_ORG_UNIT` - Certificate organizational unit (default: Certificate Authority)

### Docker Compose Integration

The service is integrated into the main Docker Compose stack:

```yaml
services:
  orch-service:
    build:
      context: .
      dockerfile: services/orch/Dockerfile
    environment:
      <<: [*common-kerberos, *common-koji, *common-kadmin, *common-orch-service]
      # Resource UUIDs configured here
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./data/orch:/mnt/data:Z
    networks:
      koji-network:
        aliases:
          - orch.koji.box
```

## Usage Examples

### Checkout a Resource
```bash
# Checkout a resource by UUID
curl -X POST http://orch.koji.box:5000/api/v2/resource/a1b2c3d4-e5f6-7890-abcd-ef1234567890 -o resource.keytab
```

### Release a Resource
```bash
# Release a resource
curl -X DELETE http://orch.koji.box:5000/api/v2/resource/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

### Check Resource Status
```bash
# Get resource status
curl http://orch.koji.box:5000/api/v2/resource/a1b2c3d4-e5f6-7890-abcd-ef1234567890/status
```

### Validate Access
```bash
# Validate if current container can access resource
curl http://orch.koji.box:5000/api/v2/resource/a1b2c3d4-e5f6-7890-abcd-ef1234567890/validate
```

### CA Certificate Management
```bash
# Get CA certificate
curl -o ca.crt http://orch.koji.box:5000/api/v2/ca/certificate

# Get CA information
curl http://orch.koji.box:5000/api/v2/ca/info

# Get CA status
curl http://orch.koji.box:5000/api/v2/ca/status
```

### Using the Orch CLI
```bash
# Using the orch.sh script for easier management
./services/common/orch.sh checkout <uuid> [file]     # Checkout a resource
./services/common/orch.sh release <uuid>             # Release a resource
./services/common/orch.sh status <uuid>              # Get resource status
./services/common/orch.sh ca-cert [file]             # Get CA certificate
./services/common/orch.sh ca-info                    # Get CA information
./services/common/orch.sh ca-status                  # Get CA status
./services/common/orch.sh ca-install                 # Install CA to system trust store
./services/common/orch.sh health                     # Check service health
./services/common/orch.sh docs                       # Show API documentation
```

## Migration from keytab-service

### 1. Run Migration Script
```bash
python services/orch/migrate_from_keytab_service.py http://keytabs.koji.box:5000 http://orch.koji.box:5000
```

### 2. Update Container Scripts
Replace direct API calls with UUID-based calls:

**Old:**
```bash
curl "${KEYTAB_SERVICE_URL}/api/v1/principal/${PRINCIPAL_NAME}" -o keytab
```

**New:**
```bash
curl -X POST "${ORCH_SERVICE_URL}/api/v2/resource/${RESOURCE_UUID}" -o keytab
```

### 3. Update Environment Variables
Add resource UUIDs to your container environment variables.

## Architecture

### Components

- **Database Manager** - SQLite database for resource tracking
- **Resource Manager** - Kerberos and SSL resource creation with CA integration
- **CA Certificate Manager** - Certificate Authority management and certificate signing
- **Container Client** - Docker/Podman integration
- **Checkout Manager** - Resource checkout/release logic
- **Validators** - Input validation and security checks
- **Error Handlers** - Standardized error responses

### Security Model

1. **Container Identification** - IP address → Docker socket lookup
2. **Resource Checkout** - One container per UUID at a time
3. **Ownership Validation** - Verify container owns resource
4. **Dead Container Cleanup** - Automatic cleanup of dead containers
5. **UUID Obfuscation** - Resources accessed via UUIDs, not names

### Resource Types

- **Principal** - Kerberos principal keytabs
- **Worker** - Koji worker keytabs with host registration
- **Cert** - SSL certificates (CA-signed)
- **Key** - SSL private keys

### CA Certificate Features

- **Automatic CA Creation** - Creates root CA certificate on first certificate request
- **CA-signed Certificates** - All SSL certificates are signed by the CA
- **Public CA Access** - CA certificate available without authentication
- **System Integration** - Easy installation to system trust stores via `ca-install` command
- **Long-term CA** - CA certificate valid for 10 years by default
- **Secure Storage** - CA private key stored with restrictive permissions (600)

## Development

### Project Structure
```
services/orch/
├── app/
│   ├── common/          # Shared components
│   ├── v1/             # Legacy API
│   └── v2/             # New API
├── templates/          # Resource mapping templates
├── test/              # Test scripts
├── Dockerfile
├── requirements.txt
└── README.md
```

### Running Tests
```bash
# Run test suite
python services/orch/test/test_orch_service.py

# Run specific tests
python -m pytest services/orch/test/
```

### Building
```bash
# Build Docker image
docker build -f services/orch/Dockerfile -t orch-service .

# Run locally
python services/orch/app.py
```

## Troubleshooting

### Common Issues

1. **Container not found** - Check Docker socket access
2. **Resource already checked out** - Another container owns the resource
3. **Resource creation failed** - Check KDC connectivity
4. **Invalid UUID format** - Verify UUID format

### Debugging

1. **Check logs** - Service logs provide detailed information
2. **Health check** - Use `/api/v2/status/health` endpoint
3. **Resource status** - Use `/api/v2/resource/<uuid>/status` endpoint
4. **API documentation** - Use `/api/v2/docs/` endpoint

### Support

- **API Documentation** - `/api/v2/docs/`
- **Health Check** - `/api/v2/status/health`
- **Resource Mappings** - `/api/v2/status/mappings`
- **Test Suite** - `python test/test_orch_service.py`

## License

This project is part of the Koji Boxed infrastructure and follows the same licensing terms.

---

For more information, see the main project documentation or contact the development team.
