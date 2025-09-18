# Boxed Koji

A containerized integration testing platform for the [Koji build system](https://pagure.io/koji). This project provides a complete, repeatable Koji environment using [Podman](https://podman.io/) and Docker Compose. Koji data (users, tags, targets, etc) can be bootstrapped or enforced as YAML (deployed via [Ansible](https://www.ansible.com/)).

## Overview

Boxed Koji creates a fully functional Koji build system with all necessary components, providing a "Koji in a box" experience that hides service complexity while exposing Koji's full functionality.

### ✅ Working Services
- **[PostgreSQL](https://www.postgresql.org/) Database** - Backend data storage
- **[MIT Kerberos](https://web.mit.edu/kerberos/) KDC** - Authentication service with realm KOJI.BOX
- **Orch Service** - REST API for sharing keytabs, certificates, a self-signed CA, and registering workers
- **Koji Hub** - Central coordination service for Koji
- **Ansible Configurator** - Automated Koji configuration management using [ktdreyer.koji_ansible](https://github.com/ktdreyer/koji-ansible)

### 🚧 In Progress Services
- **Koji Client** - CLI interface (working on reliability improvements)
- **Koji Workers** - Build execution nodes (basic functionality working, advanced features in development)
- **Nginx Proxy** - Reverse proxy and static content server
- **Koji Web** - Web frontend interface
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
     - KDC: kdc.koji.box:88 (Kerberos)
     - PostgreSQL: postgres.koji.box:5432
     - Orch Service: http://orch.koji.box:5000 (resource management with CA support)
     - Koji Hub: https://koji-hub.koji.box (fully functional with orch integration)
     - Koji Client: shell with koji and kerberos pre-configured for interactive sessions
     - Koji Workers: scalable, self-registering koji builders

   - **In Progress** (coming soon):
     - Main Entry Point: http://localhost:8080 (nginx proxy)
     - Koji Web: http://localhost:8081 (or http://koji-web.koji.box:8081)
     - Koji Desktop: a VNC enabled desktop with configured firefox and terminal

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

- [Podman](https://podman.io/) with podman-compose
- Git
- Make
- Python 3 (for validation scripts)
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
- **UUID-based Access**: Resources accessed via UUIDs for mild security

** API Endpoints:**
- `POST /api/v2/resource/<uuid>` - Checkout a resource by UUID
- `DELETE /api/v2/resource/<uuid>` - Release a resource by UUID
- `GET /api/v2/resource/<uuid>/status` - Get resource status
- `GET /api/v2/resource/<uuid>/validate` - Validate access
- `GET /api/v2/ca/certificate` - Get CA certificate (public key only)
- `GET /api/v2/ca/info` - Get CA certificate information
- `GET /api/v2/ca/status` - Get CA status
- `GET /api/v2/status/health` - Health check endpoint


**Checkout Explanation**

The original v1 API allowed arbitrary creation of any principal keytab, and certificate. This was convenient,
but left me feeling concerned. While this serivce is not intended to be used as a production-ready long-running
koji instance, it still didn't seem wise to give every service the ability to grab the principal for the hub,
or the KDC master account. So instead I went with a checkout system, where a UUID is used to anonymize the
resource request as a claim. When a service checks out their claim, the orch will identify what container
is making the request, then mark the resource as "checked-out" by that container. No other container can then
use the same claim UUID, so long as the one that checked out the resource is still alive. Resources can be
checked back in manually, or automatically if their requestor container disappears. With this system, the
services are given their relevant claim UUIDs via the environment, and from there they can fetch keytabs
or certificates.


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


### Ansible Configuration Management

- `make validate-ansible` - Validate Ansible configuration files with comprehensive checks
- `make configure` - Run Ansible configuration on existing Koji instance (includes validation)
- `make configure-check` - Validate configuration without applying (dry-run)
- `make reconfigure` - Force reconfiguration by restarting Ansible service
- `make logs-ansible` - Show logs for Ansible Configurator
- `make ansible-shell` - Get shell access to ansible configurator (for debugging)

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

The `ansible-configs/` directory contains YAML data files for automated Koji configuration:

- `ansible-configs/users.yml` - Define Koji users and permissions
- `ansible-configs/hosts.yml` - Define build hosts and capabilities
- `ansible-configs/tags.yml` - Define package tags and inheritance
- `ansible-configs/targets.yml` - Define build targets

All Ansible infrastructure (playbooks, roles, collection) is built into the `ansible-configurator` service container. Users only need to configure data, not infrastructure.

See `ansible-configs/README.md` for detailed configuration documentation.


### General Services Configuration

Configurations that are required to make this service stack functional are baked-in to the images
at build time as templates. These templates are combined with environment vars to produce the actual
config files at startup via the entrypoint. The eventual goal of this mode of configuration is to
make it so that a user can tweak the knobs, but not completely break the deployment. As this project
is still a work in progress, there are still some settings that might break things, and still some
things being mandatory at runtime init.


## Usage Examples

### Starting a Fresh Environment

```bash
# Build and start everything
make quick-start

# Validate and apply custom Koji configuration
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

**Current Architecture:**
```
  ╔════════════════╗                      ╔════════════════╗
  ║    Postgres    ║          ┌─────────► ║      KDC       ║ ◄───┐
  ╚════════════════╝          │           ╚════════════════╝     │
         ▲                    │                  ▲               │
         │                    │                  │               │
  ╔════════════════╗          │           ╔════════════════╗     │
  ║    Koji-Hub    ║──────────┴─────────► ║      Orch      ║ ◄───┤
  ╚════════════════╝                      ╚════════════════╝     │
         ▲  ▲                                    │               │
         │  └────────────────────────────────────┘               │
         │                                                       │
         │            ╔════════════════╗                         │
         ├────────────║  Koji-Workers  ║─────────────────────────┤
         │            ╚════════════════╝                         │
         │                    │                                  │
         │                    ▼                                  │
         │            ╔════════════════╗                         │
         ├────────────║    Koji-Web    ║─────────────────────────┤
         │            ╚════════════════╝                         │
         │                    ▲                                  │
         │                    │                                  │
         │            ╔════════════════╗                         │
         ├────────────║   Koji-Client  ║─────────────────────────┤
         │            ╚════════════════╝                         │
         │                                                       │
         │            ╔════════════════╗                         │
         └────────────║    Ansible     ║─────────────────────────┘
                      ╚════════════════╝
```

**Service Startup Order:**
1. **postgres** - Database backend <br />
   **kdc** - Kerberos authentication
2. **orch-service** - Resource management
3. **koji-hub** - Central coordination
4. **koji-workers** - Build nodes <br />
   **koji-client** - Interactive shell <br />
   **ansible-configurator** - Configuration management (optional)

The orch service is generally required for any service to fetch its CA certs and keytabs,
and from there the keytab is necessary to kinit against the kdc for authentication with
the koji-hub.

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
- **Purpose**: Automated Koji configuration management using [ktdreyer.koji_ansible](https://github.com/ktdreyer/koji-ansible) collection
- **Access**: Run via `make configure` or `make reconfigure`
- **Features**: User/host/tag/target management, schema validation, fail-fast validation, declarative YAML configuration, state reset capability

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

## Technologies Used

This project leverages several key open-source technologies:

- **[Koji](https://pagure.io/koji)** - The core build system for RPM packages
- **[PostgreSQL](https://www.postgresql.org/)** - Robust relational database for Koji's backend storage
- **[MIT Kerberos](https://web.mit.edu/kerberos/)** - Network authentication protocol for secure service communication
- **[Ansible](https://www.ansible.com/)** - Automation platform for configuration management
- **[ktdreyer.koji_ansible](https://github.com/ktdreyer/koji-ansible)** - Official Ansible collection for Koji management
- **[Podman](https://podman.io/)** - Daemonless container engine for running containerized services
- **[Python](https://python.org)** - The Orchestrator is written using [Flask] running under [Gunicorn]

[Flask]: https://github.com/pallets/flask/
[Gunicorn]: https://github.com/benoitc/gunicorn


## Contact

Author: Christopher O'Brien  <obriencj@gmail.com>
Original GitHub Project: https://github.com/obriencj/koji-box


## Development Acknowledgments

This project was developed with significant assistance from **Claude** (Anthropic's
AI assistant). The AI assistance has been invaluable in bootstrapping and
providing feedback on the initial concept. The Orchestrator, in particular, is
primarily AI-generated code, with some human tweaks to ensure correct
functionality. Almost every README is also AI-generated, and sections are kept
up-to-date with the project's state via AI.


## License

This library is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 3 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this library; if not, see http://www.gnu.org/licenses/.
