# Boxed Koji

A containerized integration testing platform for the Koji build system. This project provides a complete, repeatable Koji environment using Podman and Docker Compose for automated integration testing.

## Overview

Boxed Koji creates a fully functional Koji build system with all necessary components. The project has recently migrated to a new **Orch Service** and **orch.sh tool** for comprehensive resource management.

### ✅ Working Services
- **PostgreSQL Database** - Backend data storage
- **KDC (Kerberos)** - Authentication service with realm KOJI.BOX
- **Orch Service** - REST API for resource management with CA certificate support
- **Koji Hub** - Central coordination service (fully functional with orch integration)
- **Ansible Configurator** - Automated Koji configuration management

### 🚧 In Progress Services
- **Koji Client** - CLI interface (working on reliability improvements)
- **Nginx Proxy** - Reverse proxy and static content server
- **Koji Web** - Web frontend interface
- **Koji Workers** - Build execution nodes
- **Test Runner** - Automated testing framework

## Quick Start

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd koji-boxed
   cp env.default .env
   ```

2. **Configure container socket** (see SOCKET_README.md for details):
   ```bash
   # For rootless podman (recommended)
   echo "PODMAN_SOCKET=/run/user/$UID/podman/podman.sock" >> .env

   # For root podman
   echo "PODMAN_SOCKET=/var/run/podman.sock" >> .env

   # For Docker
   echo "PODMAN_SOCKET=/var/run/docker.sock" >> .env
   ```

3. **Start the environment**:
   ```bash
   make quick-start
   ```

4. **Access services**:
   - **Working Services**:
     - Koji Hub: http://koji-hub.koji.box:80 (fully functional with orch integration)
     - Orch Service: http://orch.koji.box:5000 (resource management with CA support)
     - KDC: kdc.koji.box:88 (Kerberos)
     - PostgreSQL: postgres.koji.box:5432
   - **In Progress** (coming soon):
     - Koji Client: CLI interface (reliability improvements in progress)
     - Main Entry Point: http://localhost:8080 (nginx proxy)
     - Koji Web: http://localhost:8081 (or http://koji-web.koji.box:8081)
     - Koji Workers: Build execution nodes (via `make up --profile workers`)

## Recent Updates

### 🚀 New Orch Service Migration

The project has recently migrated to a comprehensive **Orch Service** and **orch.sh tool** for resource management:

- **Enhanced Security**: IP-based container identification and resource checkout system
- **CA Certificate Support**: Built-in Certificate Authority for SSL certificate management
- **UUID-based Access**: Resources accessed via UUIDs for enhanced security
- **Backward Compatibility**: V1 API maintained for existing integrations
- **Comprehensive CLI**: `orch.sh` tool for easy resource management

See the [Orch Service README](services/orch/README.md) for detailed documentation.

## Prerequisites

- Podman with podman-compose
- Git
- Make
- Internet connection (for downloading Koji source)
- Container socket access (see SOCKET_README.md for configuration)

## Project Structure

```
koji-boxed/
├── Makefile                         # Main orchestration file
├── docker-compose.yml               # Service definitions
├── .env.example                     # Environment variables template
├── scripts/                         # Utility scripts
│   └── cleanup.sh                   # Cleanup utilities
├── data/                            # Persistent data volumes
│   ├── postgres/                    # Database data
│   ├── keytabs/                     # Principal keytabs
│   └── logs/                        # Service logs
├── services/                        # Individual service Dockerfiles
│   ├── common/                      # Shared components (includes orch.sh tool)
│   ├── kdc/                         # ✅ Kerberos KDC service
│   ├── koji-hub/                    # ✅ Koji Hub service (with orch integration)
│   ├── koji-client/                 # 🚧 Koji CLI client (reliability improvements)
│   ├── orch/                        # ✅ Orch resource management service
│   ├── postgres/                    # ✅ PostgreSQL database
│   ├── ansible-configurator/        # ✅ Ansible configuration management
│   ├── koji-worker/                 # 🚧 Build workers (in progress)
│   ├── koji-web/                    # 🚧 Web interface (in progress)
│   ├── nginx/                       # 🚧 Reverse proxy (in progress)
│   └── test-runner/                 # 🚧 Test automation (in progress)
├── ansible-configs/                 # ✅ Ansible YAML configuration files
└── tests/                           # Integration tests
    ├── test-scripts/
    └── expected-results/
```

## Available Commands

### Basic Operations

- `make help` - Show all available commands
- `make build` - Build all container images
- `make up` - Start all services
- `make down` - Stop all services
- `make logs` - View service logs
- `make status` - Show service status

### Development

- `make dev` - Start development environment with full setup
- `make dev-logs` - Start dev environment and show logs
- `make quick-start` - Build, start, and setup everything

### Testing

- `make test` - Run integration tests
- `make test-kerberos` - Test Kerberos authentication
- `make shell-hub` - Open shell in Koji Hub container
- `make shell-worker` - Open shell in Koji Worker container
- `make shell-web` - Open shell in Koji Web container
- `make shell-kdc` - Open shell in KDC container
- `make shell-nginx` - Open shell in Nginx container

### Kerberos

- `make setup-kdc` - Setup KDC and create service principals
- `make kinit-admin` - Get Kerberos ticket for admin user
- `make list-principals` - List Kerberos principals
- `make test-kerberos` - Test Kerberos authentication

### Orch Service

- `make logs-orch` - Show logs for Orch Service

The Orch Service is a comprehensive resource management system that provides secure, container-based access control for Koji infrastructure resources. It includes:

- **Principal Management**: Creates principals in the KDC and generates keytabs
- **Worker Registration**: Registers worker hosts with the Koji hub using admin authentication
- **Certificate Authority (CA)**: Manages its own CA for signing SSL certificates
- **SSL Certificate Management**: Creates and manages SSL certificates signed by the CA
- **Container-based Security**: IP-based container identification and resource checkout system
- **UUID-based Access**: Resources accessed via UUIDs for enhanced security

**V2 API Endpoints (Recommended):**
- `POST /api/v2/resource/<uuid>` - Checkout a resource by UUID
- `DELETE /api/v2/resource/<uuid>` - Release a resource by UUID
- `GET /api/v2/resource/<uuid>/status` - Get resource status
- `GET /api/v2/resource/<uuid>/validate` - Validate access
- `GET /api/v2/ca/certificate` - Get CA certificate (public key only)
- `GET /api/v2/ca/info` - Get CA certificate information
- `GET /api/v2/ca/status` - Get CA status
- `GET /api/v2/status/health` - Health check endpoint

**V1 API Endpoints (Legacy):**
- `GET /api/v1/principal/<principal_name>` - Get or create a principal and return its keytab
- `GET /api/v1/worker/<worker_name>` - Get or create a worker host and return its keytab
- `GET /api/v1/cert/<cn>` - Get SSL certificate
- `GET /api/v1/cert/key/<cn>` - Get SSL private key

**Orch CLI Usage:**
```bash
# Using the orch.sh script
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

**Direct API Usage:**
```bash
# Get a principal keytab (V1 API)
curl -o my-principal.keytab http://orch.koji.box:5000/api/v1/principal/my-principal

# Get a worker keytab and register with hub (V1 API)
curl -o worker.keytab http://orch.koji.box:5000/api/v1/worker/worker-1

# Get CA certificate
curl -o ca.crt http://orch.koji.box:5000/api/v2/ca/certificate

# Install CA certificate to system trust store
sudo ./services/common/orch.sh ca-install
```

### Ansible Configuration Management

- `make configure` - Run Ansible configuration on existing Koji instance
- `make reconfigure` - Force reconfiguration by restarting Ansible service
- `make logs-ansible` - Show logs for Ansible Configurator
- `make ansible-shell` - Get shell access to ansible configurator (for debugging)
- `make validate-ansible` - Validate Ansible configuration files

### Maintenance

- `make clean` - Remove all containers and images
- `make clean-data` - Remove all data volumes
- `make rebuild` - Force rebuild all images
- `make backup` - Create backup of data volumes
- `make restore BACKUP_DIR=path` - Restore from backup

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and modify as needed:

```bash
# Database Configuration
POSTGRES_DB=koji
POSTGRES_USER=koji
POSTGRES_PASSWORD=koji_password

# Koji Hub Configuration
KOJI_HUB_HOST=koji-hub
KOJI_HUB_PORT=8080

# Storage Configuration
KOJI_STORAGE_HOST=nginx
KOJI_STORAGE_PORT=80
```

### Ansible Configuration

The `ansible-configs/` directory contains YAML files for automated Koji configuration:

- `ansible-configs/users.yml` - Define Koji users and permissions
- `ansible-configs/hosts.yml` - Define build hosts and capabilities
- `ansible-configs/tags.yml` - Define package tags and inheritance
- `ansible-configs/targets.yml` - Define build targets
- `ansible-configs/site.yml` - Main Ansible playbook
- `ansible-configs/inventory.yml` - Koji environment inventory
- `ansible-configs/group_vars/all.yml` - Global variables and defaults

See `ansible-configs/README.md` for detailed configuration documentation.

### Service Configuration

Each service has its own configuration directory under `configs/`:

- `configs/koji-hub/` - Hub configuration (now uses template-based generation)
- `configs/koji-web/koji_web.conf` - Web UI configuration
- `configs/koji-client/koji.conf` - Client configuration

### Shared Configuration

Common configuration templates are available in `configs/shared/`:

- `configs/shared/koji.conf.template` - Koji client configuration template
- `configs/shared/krb5.conf.template` - Kerberos configuration template
- `configs/shared/hub.conf.template` - Koji hub configuration template

These templates use environment variable substitution and are copied into containers during build, allowing for consistent configuration across all services.

## Usage Examples

### Starting a Fresh Environment

```bash
# Build and start everything
make quick-start

# Apply custom Koji configuration
make configure

# Check status
make status

# View logs
make logs
```

### Running Tests

```bash
# Run all integration tests
make test

# Run specific test
./tests/test-scripts/test-basic-functionality.sh
```

### Development Workflow

```bash
# Start development environment
make dev

# Open shell in hub container
make shell-hub

# Inside hub container, test Koji commands
koji list-users
koji list-tags
koji build --scratch dist-foo "test-package-1.0-1"
```

### Cleanup

```bash
# Stop and remove everything
make clean

# Remove only data volumes
make clean-data

# Complete cleanup including source
./scripts/cleanup.sh
```

## Troubleshooting

### Common Issues

1. **Services not starting**:
   ```bash
   make logs
   make status
   ```

2. **Database connection issues**:
   ```bash
   make logs-postgres
   make shell-postgres
   ```

3. **Kerberos authentication issues**:
   ```bash
   make logs-kdc
   make test-kerberos
   make shell-kdc
   ```

4. **Orch service issues**:
   ```bash
   make logs-orch
   curl http://orch.koji.box:5000/api/v2/status/health
   ```

5. **Build failures**:
   ```bash
   make clean
   make rebuild
   ```

### Service-Specific Troubleshooting

**Working Services:**
- PostgreSQL, KDC, Orch Service, Koji Hub are fully functional
- Check logs with `make logs-<service>` for specific issues

**In Progress Services:**
- Koji Client: Working on reliability improvements
- Koji Workers: Available via `make up --profile workers` but still in development
- Nginx, Koji Web, Test Runner: Configuration and integration in progress

### Logs

View logs for specific services:
- `make logs-hub` - Koji Hub logs
- `make logs-worker` - Koji Worker logs
- `make logs-web` - Koji Web logs
- `make logs-postgres` - Database logs

### Debugging

Access container shells for debugging:
- `make shell-hub` - Koji Hub container
- `make shell-worker` - Koji Worker container
- `make shell-web` - Koji Web container
- `make shell-postgres` - Database container

## Architecture

### Network

All services run on a custom bridge network (`koji-network`) with subnet `172.20.0.0/16`.

### Storage

- **PostgreSQL**: Persistent volume for database data
- **Koji Storage**: Shared volume for build artifacts and packages
- **Logs**: Host-mounted directory for service logs

### Service Dependencies

**Current Working Architecture:**
```
postgres → koji-hub ←─── orch-service
    ↓         ↓              ↓
   kdc ←──────┘              ↓
    ↓                       ↓
orch-service ←─── koji-client (reliability improvements)
```

**Planned Full Architecture:**
```
postgres → koji-hub → koji-worker
    ↓         ↓           ↓
   kdc ←──────┴───────────┘
    ↓
koji-web ←─── nginx (main entry point)
    ↓
orch-service ←─── test-runner
```

### Nginx Routing (In Progress)

The nginx proxy will provide a unified entry point with the following planned routing:

- **`/`** - Routes to Koji Web interface (default)
- **`/kojihub/`** - Routes to Koji Hub API
- **`/downloads/`** - Serves static content from `/mnt/koji` with directory indexing
- **`/health`** - Nginx health check endpoint

**Current Status**: Nginx service is being configured and tested.

## Current Working Services

### ✅ PostgreSQL Database
- **Status**: Fully functional
- **Purpose**: Backend data storage for Koji
- **Access**: `postgres.koji.box:5432`
- **Features**: Automated schema initialization, persistent data storage

### ✅ KDC (Kerberos)
- **Status**: Fully functional
- **Purpose**: Authentication service with realm KOJI.BOX
- **Access**: `kdc.koji.box:88`
- **Features**: Service principal management, admin user creation

### ✅ Orch Service
- **Status**: Fully functional
- **Purpose**: Comprehensive resource management system with CA certificate support
- **Access**: `orch.koji.box:5000`
- **Features**: Principal creation, keytab generation, worker registration, CA certificate management, SSL certificate signing

### ✅ Koji Hub
- **Status**: Fully functional
- **Purpose**: Central coordination service
- **Access**: `koji-hub.koji.box:80`
- **Features**: User management, build coordination, API endpoints

### ✅ Ansible Configurator
- **Status**: Fully functional
- **Purpose**: Automated Koji configuration management
- **Access**: Run via `make configure` or `make reconfigure`
- **Features**: User/host/tag/target management, declarative YAML configuration, state reset capability

### 🚧 Koji Client
- **Status**: Working on reliability improvements
- **Purpose**: CLI interface for testing and administration
- **Features**: Kerberos authentication, Koji command execution
- **Issues**: Reliability improvements in progress

## Services In Progress

### 🚧 Koji Workers
- **Status**: Development in progress
- **Purpose**: Build execution nodes
- **Access**: Available via `make up --profile workers`
- **Features**: Build execution, resource management via orch service

### 🚧 Nginx Proxy
- **Status**: Configuration in progress
- **Purpose**: Reverse proxy and static content server
- **Planned Access**: `localhost:8080` (main entry point)
- **Features**: Unified routing, static file serving, health checks

### 🚧 Koji Web
- **Status**: Configuration in progress
- **Purpose**: Web frontend interface
- **Planned Access**: `koji-web.koji.box:8080` or via nginx
- **Features**: Web-based Koji management interface

### 🚧 Test Runner
- **Status**: Development in progress
- **Purpose**: Automated testing framework
- **Features**: Integration test execution, test result reporting

### Kerberos Configuration

The KDC service creates the following service principals:

- `hub/koji-hub.koji.box@KOJI.BOX` - Koji Hub service
- `http/koji-web.koji.box@KOJI.BOX` - Koji Web service
- `koji/koji-worker-1.koji.box@KOJI.BOX` - Koji Worker service

Default admin user: `admin/admin@KOJI.BOX` (password: `admin_password`)

### Domain Aliases

All services are accessible via both short names and full domain names:

- `postgres` or `postgres.koji.box`
- `kdc` or `kdc.koji.box`
- `nginx` or `koji.box` (main entry point)
- `koji-hub` or `koji-hub.koji.box`
- `koji-worker-1` or `koji-worker-1.koji.box`
- `koji-web` or `koji-web.koji.box`
- `koji-client` or `koji-client.koji.box`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `make test`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review service logs
3. Open an issue on the project repository
