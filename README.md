# Boxed Koji

A containerized integration testing platform for the Koji build system. This project provides a complete, repeatable Koji environment using Podman and Docker Compose for automated integration testing.

## Overview

Boxed Koji creates a fully functional Koji build system with all necessary components:

- **PostgreSQL Database** - Backend data storage
- **KDC (Kerberos)** - Authentication service with realm KOJI.BOX
- **Nginx Proxy** - Reverse proxy and static content server
- **Koji Hub** - Central coordination service
- **Koji Worker(s)** - Build execution nodes
- **Koji Web** - Web frontend interface
- **Storage Service** - NFS + HTTP file storage
- **Koji Client** - CLI interface for testing

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
   - **Main Entry Point**: http://localhost:8080 (nginx proxy)
     - `/` - Koji Web interface
     - `/kojihub/` - Koji Hub API
     - `/downloads/` - Static file downloads with indexing
   - **Direct Access** (if needed):
     - Koji Hub: http://localhost:8080 (or http://koji-hub.koji.box:8080)
     - Koji Web: http://localhost:8081 (or http://koji-web.koji.box:8081)
     - KDC: localhost:88 (or kdc.koji.box:88) (Kerberos)

## Prerequisites

- Podman with podman-compose
- Git
- Make
- Internet connection (for downloading Koji source)

## Project Structure

```
koji-boxed/
├── Makefile                          # Main orchestration file
├── docker-compose.yml                # Service definitions
├── .env.example                      # Environment variables template
├── scripts/                          # Utility scripts
│   ├── setup-koji-db.sh             # Database initialization
│   ├── setup-koji-hub.sh            # Hub configuration
│   └── cleanup.sh                   # Cleanup utilities
├── configs/                          # Configuration files
│   ├── koji-hub/                    # Hub configuration
│   ├── koji-web/                    # Web UI configuration
│   └── koji-client/                 # Client configuration
├── data/                            # Persistent data volumes
│   ├── postgres/                    # Database data
│   └── logs/                        # Service logs
├── dockerfiles/                     # Individual service Dockerfiles
│   ├── koji-hub/
│   ├── koji-worker/
│   ├── koji-web/
│   ├── koji-client/
│   ├── nginx/
│   └── postgres/
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

- `configs/koji-hub/hub.conf` - Hub configuration
- `configs/koji-web/koji_web.conf` - Web UI configuration
- `configs/koji-client/koji.conf` - Client configuration

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

3. **Build failures**:
   ```bash
   make clean
   make rebuild
   ```

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

```
postgres → koji-hub → koji-worker
    ↓         ↓           ↓
   kdc ←──────┴───────────┘
    ↓
koji-web ←─── nginx (main entry point)
```

### Nginx Routing

The nginx proxy provides a unified entry point with the following routing:

- **`/`** - Routes to Koji Web interface (default)
- **`/kojihub/`** - Routes to Koji Hub API
- **`/downloads/`** - Serves static content from `/mnt/koji` with directory indexing
- **`/health`** - Nginx health check endpoint

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
