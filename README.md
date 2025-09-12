# Boxed Koji

A containerized integration testing platform for the Koji build system. This project provides a complete, repeatable Koji environment using Podman and Docker Compose for automated integration testing.

## Overview

Boxed Koji creates a fully functional Koji build system with all necessary components:

### ✅ Working Services
- **PostgreSQL Database** - Backend data storage
- **KDC (Kerberos)** - Authentication service with realm KOJI.BOX
- **Keytab Service** - REST API for principal and worker management
- **Koji Hub** - Central coordination service
- **Koji Client** - CLI interface for testing

### 🚧 In Progress Services
- **Nginx Proxy** - Reverse proxy and static content server
- **Koji Web** - Web frontend interface
- **Test Runner** - Automated testing framework

### 📋 Planned Services
- **Koji Worker(s)** - Build execution nodes
- **Storage Service** - NFS + HTTP file storage

## Quick Start

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd koji-boxed
   cp .env.example .env
   ```

2. **Start the environment**:
   ```bash
   make quick-start
   ```

3. **Access services**:
   - **Working Services**:
     - Koji Hub: http://koji-hub.koji.box:80 (or via nginx when ready)
     - Keytab Service: http://keytabs.koji.box:5000
     - KDC: kdc.koji.box:88 (Kerberos)
     - PostgreSQL: postgres.koji.box:5432
   - **In Progress** (coming soon):
     - Main Entry Point: http://localhost:8080 (nginx proxy)
     - Koji Web: http://localhost:8081 (or http://koji-web.koji.box:8081)

## Prerequisites

- Podman with podman-compose
- Git
- Make
- Internet connection (for downloading Koji source)

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
├── services /                       # Individual service Dockerfiles
│   ├── common/                      # Shared components
│   ├── kdc/                         # ✅ Kerberos KDC service
│   ├── koji-hub/                    # ✅ Koji Hub service
│   ├── koji-client/                 # ✅ Koji CLI client
│   ├── keytab-service/              # ✅ Keytab management service
│   ├── postgres/                    # ✅ PostgreSQL database
│   ├── koji-worker/                 # 📋 Planned: Build workers
│   ├── koji-web/                    # 🚧 In Progress: Web interface
│   ├── nginx/                       # 🚧 In Progress: Reverse proxy
│   └── test-runner/                 # 🚧 In Progress: Test automation
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

### Keytab Service

- `make logs-keytab-service` - Show logs for Keytab Service

The Keytab Service is an internal Flask REST application that manages Koji principals and worker hosts. It provides:

- **Principal Management**: Creates principals in the KDC and generates keytabs
- **Worker Registration**: Registers worker hosts with the Koji hub using admin authentication
- **Static File Serving**: Serves principal keytabs from the shared data directory
- **Koji CLI Integration**: Automatically installs and configures Koji client tools at startup

**API Endpoints:**
- `GET /api/v1/principal/<principal_name>` - Get or create a principal and return its keytab
- `GET /api/v1/worker/<worker_name>` - Get or create a worker host and return its keytab
- `GET /principals/<filename>` - Serve principal keytab files statically
- `GET /health` - Health check endpoint

**Usage:**
```bash
# Get a principal keytab
curl -o my-principal.keytab http://keytabs.koji.box:80/api/v1/principal/my-principal

# Get a worker keytab and register with hub
curl -o worker.keytab http://keytabs.koji.box:80/api/v1/worker/worker-1
```

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

4. **Keytab service issues**:
   ```bash
   make logs-keytab-service
   curl http://keytabs.koji.box:5000/health
   ```

5. **Build failures**:
   ```bash
   make clean
   make rebuild
   ```

### Service-Specific Troubleshooting

**Working Services:**
- PostgreSQL, KDC, Keytab Service, Koji Hub, Koji Client are fully functional
- Check logs with `make logs-<service>` for specific issues

**In Progress Services:**
- Nginx, Koji Web, Test Runner may have configuration issues
- These services are being actively developed and tested

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
postgres → koji-hub ←─── koji-client
    ↓         ↓
   kdc ←──────┘
    ↓
keytab-service ←─── koji-client
```

**Planned Full Architecture:**
```
postgres → koji-hub → koji-worker
    ↓         ↓           ↓
   kdc ←──────┴───────────┘
    ↓
koji-web ←─── nginx (main entry point)
    ↓
keytab-service ←─── test-runner
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

### ✅ Keytab Service
- **Status**: Fully functional
- **Purpose**: REST API for principal and worker management
- **Access**: `keytabs.koji.box:5000`
- **Features**: Principal creation, keytab generation, worker registration

### ✅ Koji Hub
- **Status**: Fully functional
- **Purpose**: Central coordination service
- **Access**: `koji-hub.koji.box:80`
- **Features**: User management, build coordination, API endpoints

### ✅ Koji Client
- **Status**: Fully functional
- **Purpose**: CLI interface for testing and administration
- **Features**: Kerberos authentication, Koji command execution

## Services In Progress

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
